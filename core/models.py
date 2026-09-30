"""OWNER: M1. Credit scoring models with reject inference and scoreboard.

T1 reject inference uses AUGMENTATION (not parcelling). Rationale:
    Augmentation is the standard two-step approach in credit scoring:
    (1) train a model on approved-only data, (2) use it to impute PD for
    rejected applicants, (3) retrain on the combined dataset.
    We prefer augmentation over parcelling because:
    - Parcelling requires binning scores and assigning class rates per bin,
      which introduces arbitrary bin boundaries and loses information.
    - Augmentation is a natural semi-supervised extension that preserves
      the full probability surface.
    - With our stochastic legacy policy (noise + 5-10% manual overrides),
      there is genuine overlap between approved and rejected populations,
      making augmentation identifiable (Blueprint L3).
    - Literature shows reject-inference gains are typically modest;
      we measure and report honestly.

Three models trained on the SAME features:
    (a) approved-only   — trained only on firms where we observed outcomes
    (b) reject-inferred — augmented with imputed labels for rejected firms
    (c) ORACLE          — trained with true outcomes for ALL firms (oracle.parquet)
        Used ONLY for evaluation/reference, NEVER in any production score path.
"""
import pickle

import lightgbm as lgb
import numpy as np
import pandas as pd
import yaml
from scipy.stats import ks_2samp
from sklearn.calibration import calibration_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split

from core.contracts import Borrower, ScoreResult
from core.features import by_name, model_features
from core.paths import CONFIGS, DATA, MODELS, write_json, write_metrics
from core.reference import resolve

MODEL_VERSION = "v2-reject-inference"
APPROVAL_PD_THRESHOLD = 0.10  # placeholder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class WoEBinning:
    def __init__(self, bins=5):
        self.bins = bins
        self.bin_edges = {}
        self.woe_dict = {}

    def fit(self, X: pd.DataFrame, y: pd.Series):
        for col in X.columns:
            if X[col].dtype == object or isinstance(X[col].dtype, pd.CategoricalDtype):
                # Categorical
                self.bin_edges[col] = "categorical"
                grouped = y.groupby(X[col].fillna("MISSING"), observed=False)
            else:
                # Continuous
                edges = np.unique(np.nanquantile(X[col], np.linspace(0, 1, self.bins + 1)))
                if len(edges) < 2:
                    edges = np.array([X[col].min() - 1, X[col].max() + 1])
                self.bin_edges[col] = edges

                # Bin data
                binned = pd.cut(X[col], bins=edges, include_lowest=True, duplicates='drop')
                binned = binned.cat.add_categories(["MISSING"])
                binned = binned.fillna("MISSING")
                grouped = y.groupby(binned, observed=False)

            events = grouped.sum()
            non_events = grouped.count() - events

            # Add smoothing
            events = events + 0.5
            non_events = non_events + 0.5

            p_events = events / events.sum()
            p_non_events = non_events / non_events.sum()

            self.woe_dict[col] = np.log(p_non_events / p_events)

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_out = pd.DataFrame(index=X.index)
        for col in X.columns:
            if isinstance(self.bin_edges[col], str) and self.bin_edges[col] == "categorical":
                binned = X[col].fillna("MISSING")
            else:
                binned = pd.cut(X[col], bins=self.bin_edges[col], include_lowest=True)
                if binned.isna().any():
                    if "MISSING" not in binned.cat.categories:
                        binned = binned.cat.add_categories(["MISSING"])
                    binned = binned.fillna("MISSING")

            X_out[col] = binned.map(self.woe_dict[col]).astype(float)
            # Fill unknown categories with 0 WoE
            X_out[col] = X_out[col].fillna(0.0)
        return X_out


def compute_expected_profit(y_prob, y_true, threshold, lgd, margin=0.10, ticket=500000):
    """Expected profit for approved loans (prob <= threshold).

    profit per good loan = margin * ticket
    loss per bad loan = -lgd * ticket
    """
    approved = y_prob <= threshold
    profit = np.sum(approved * (margin * ticket * (1 - y_true) - lgd * ticket * y_true))
    return float(profit)


def expected_calibration_error(y_true, y_prob, n_bins=10):
    bins = np.linspace(0., 1., n_bins + 1)
    binids = np.digitize(y_prob, bins) - 1
    ece = 0.0
    for i in range(n_bins):
        mask = binids == i
        if np.sum(mask) > 0:
            prob_mean = np.mean(y_prob[mask])
            acc_mean = np.mean(y_true[mask])
            ece += np.abs(prob_mean - acc_mean) * np.sum(mask) / len(y_prob)
    return float(ece)


def compute_psi(expected, actual, bins=10):
    expected_bins, bin_edges = np.histogram(expected, bins=bins, range=(0, 1))
    actual_bins, _ = np.histogram(actual, bins=bin_edges)
    expected_pct = (expected_bins + 0.0001) / len(expected)
    actual_pct = (actual_bins + 0.0001) / len(actual)
    return float(np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct)))


def _prepare_lgb_features(X, features, spec):
    """Cast categorical columns to pd.Categorical for LightGBM."""
    X_lgb = X.copy()
    for f in features:
        if spec[f].get("type") == "cat":
            cats = spec[f].get("categories", [])
            X_lgb[f] = pd.Categorical(X_lgb[f], categories=cats)
    return X_lgb


def _get_monotone_constraints(features, spec):
    """Return monotone constraint list for LightGBM."""
    return [spec[f].get("monotone_pd", 0) for f in features]


def _train_lgbm(X_train, y_train, monotone_constraints, seed=42, n_estimators=100):
    """Train a LightGBM classifier with monotone constraints."""
    model = lgb.LGBMClassifier(
        random_state=seed,
        monotone_constraints=monotone_constraints,
        n_estimators=n_estimators,
        verbose=-1,
    )
    model.fit(X_train, y_train)
    return model


def _evaluate_model(model, X, y, calib=None):
    """Evaluate a model, return (y_prob, metrics_dict)."""
    y_prob = model.predict_proba(X)[:, 1]
    if calib is not None:
        y_prob = calib.predict(y_prob)

    y_arr = y.values if hasattr(y, "values") else np.asarray(y)

    # Guard against single-class splits in small smoke runs
    if len(np.unique(y_arr)) < 2:
        auc = 0.5
        ks = 0.0
    else:
        auc = roc_auc_score(y_arr, y_prob)
        good_prob = y_prob[y_arr == 0]
        bad_prob = y_prob[y_arr == 1]
        ks = ks_2samp(good_prob, bad_prob).statistic if len(good_prob) > 0 and len(bad_prob) > 0 else 0.0

    gini = 2 * auc - 1
    brier = brier_score_loss(y_arr, y_prob)
    ece = expected_calibration_error(y_arr, y_prob)

    return y_prob, {"auc": float(auc), "gini": float(gini), "brier": float(brier),
                    "ks": float(ks), "ece": float(ece)}


# ---------------------------------------------------------------------------
# Scoreboard computation (T2)
# ---------------------------------------------------------------------------

def _compute_scoreboard(
    legacy_decisions, borrowers, oracle, features, spec,
    lgd, margin, ticket, seed=42,
):
    """Build the four-model scoreboard (Legacy / Approved-only / Inferred / Oracle).

    Evaluated on OOT test months using oracle outcomes for ALL firms (including
    those the legacy policy rejected, whose outcomes we would never see in
    production — the oracle outcomes are used here ONLY for evaluation).

    Returns a dict suitable for artifacts/scoreboard.json.
    """
    monotone = _get_monotone_constraints(features, spec)

    # --- Merge all data ---
    all_df = borrowers.merge(oracle[["id", "default_12m"]], on="id", how="inner",
                             suffixes=("", "_oracle"))
    all_df = all_df.merge(legacy_decisions[["id", "legacy_approved", "legacy_score"]],
                          on="id", how="inner")

    # OOT split
    train_mask = all_df["application_month"] <= all_df["oot_train_end"]
    test_mask = all_df["application_month"] >= all_df["oot_test_start"]

    train_all = all_df[train_mask].copy()
    test_all = all_df[test_mask].copy()

    # Approved-only train set
    train_approved = train_all[train_all["legacy_approved"] == 1].copy()
    # Rejected train set (for augmentation)
    train_rejected = train_all[train_all["legacy_approved"] == 0].copy()

    X_train_appr = _prepare_lgb_features(train_approved[features], features, spec)
    y_train_appr = train_approved["default_12m"]

    X_train_all = _prepare_lgb_features(train_all[features], features, spec)
    y_train_all = train_all["default_12m"]  # oracle outcomes

    X_test = _prepare_lgb_features(test_all[features], features, spec)
    y_test_oracle = test_all["default_12m"]  # oracle outcomes for evaluation

    # --- Model (a): Approved-only ---
    model_approved = _train_lgbm(X_train_appr, y_train_appr, monotone, seed=seed)

    # Calibrator for approved-only (fit on a held-out slice of approved)
    if len(X_train_appr) > 20:
        X_appr_fit, X_appr_cal, y_appr_fit, y_appr_cal = train_test_split(
            X_train_appr, y_train_appr, test_size=0.2, random_state=seed
        )
        model_approved_cal = _train_lgbm(X_appr_fit, y_appr_fit, monotone, seed=seed)
        cal_approved = IsotonicRegression(out_of_bounds='clip')
        cal_approved.fit(model_approved_cal.predict_proba(X_appr_cal)[:, 1], y_appr_cal)
    else:
        cal_approved = None

    # --- Model (b): Reject-inferred (augmentation) ---
    # Step 1: use approved-only model to impute PD for rejected firms
    X_rejected = _prepare_lgb_features(train_rejected[features], features, spec)
    if len(X_rejected) > 0:
        rejected_pd = model_approved.predict_proba(X_rejected)[:, 1]
        # Step 2: assign pseudo-labels — probabilistic rounding with seed
        rng = np.random.RandomState(seed + 1)
        pseudo_labels = (rng.rand(len(rejected_pd)) < rejected_pd).astype(int)

        # Step 3: combine approved (real labels) + rejected (pseudo labels)
        X_combined = pd.concat([X_train_appr, X_rejected], ignore_index=True)
        y_combined = pd.concat([y_train_appr, pd.Series(pseudo_labels, name="default_12m")],
                               ignore_index=True)
    else:
        X_combined = X_train_appr.copy()
        y_combined = y_train_appr.copy()

    model_inferred = _train_lgbm(X_combined, y_combined, monotone, seed=seed)

    # Calibrator for inferred
    if len(X_combined) > 20:
        X_inf_fit, X_inf_cal, y_inf_fit, y_inf_cal = train_test_split(
            X_combined, y_combined, test_size=0.2, random_state=seed
        )
        model_inf_cal = _train_lgbm(X_inf_fit, y_inf_fit, monotone, seed=seed)
        cal_inferred = IsotonicRegression(out_of_bounds='clip')
        cal_inferred.fit(model_inf_cal.predict_proba(X_inf_cal)[:, 1], y_inf_cal)
    else:
        cal_inferred = None

    # --- Model (c): ORACLE (evaluation/reference only, NEVER production) ---
    model_oracle = _train_lgbm(X_train_all, y_train_all, monotone, seed=seed)

    if len(X_train_all) > 20:
        X_orc_fit, X_orc_cal, y_orc_fit, y_orc_cal = train_test_split(
            X_train_all, y_train_all, test_size=0.2, random_state=seed
        )
        model_orc_cal = _train_lgbm(X_orc_fit, y_orc_fit, monotone, seed=seed)
        cal_oracle = IsotonicRegression(out_of_bounds='clip')
        cal_oracle.fit(model_orc_cal.predict_proba(X_orc_cal)[:, 1], y_orc_cal)
    else:
        cal_oracle = None

    # --- Evaluate all three models on OOT test set (oracle outcomes) ---
    prob_approved, met_approved = _evaluate_model(model_approved, X_test, y_test_oracle, cal_approved)
    prob_inferred, met_inferred = _evaluate_model(model_inferred, X_test, y_test_oracle, cal_inferred)
    prob_oracle, met_oracle = _evaluate_model(model_oracle, X_test, y_test_oracle, cal_oracle)

    # --- Legacy "model": use the legacy_score as a ranking (higher = better) ---
    # Legacy approves by score > cutoff. We invert score so higher prob = higher risk.
    legacy_scores = test_all["legacy_score"].values
    # Normalise to [0, 1] and invert: low legacy score → high PD proxy
    ls_min, ls_max = legacy_scores.min(), legacy_scores.max()
    if ls_max > ls_min:
        prob_legacy = 1.0 - (legacy_scores - ls_min) / (ls_max - ls_min)
    else:
        prob_legacy = np.full(len(legacy_scores), 0.5)
    _, met_legacy = _evaluate_model_from_probs(prob_legacy, y_test_oracle.values)

    # Legacy approval decision on test set
    legacy_approved_test = test_all["legacy_approved"].values.astype(bool)

    # --- ISO-LOSS view: at the legacy loss rate, how many approvals? ---
    legacy_loss_rate = float(y_test_oracle.values[legacy_approved_test].mean()) if legacy_approved_test.sum() > 0 else 0.0
    legacy_approval_rate = float(legacy_approved_test.mean())
    legacy_n_approved = int(legacy_approved_test.sum())

    def iso_loss_approvals(probs, y_true, target_loss_rate):
        """Find max approvals where cumulative loss rate among approved <= target.

        Sort firms by predicted PD ascending (best first), then scan all firms
        to find the largest k where mean(y_true[:k]) <= target_loss_rate.
        We do NOT break early because adding more good firms after a default
        can bring the cumulative rate back below the target.
        """
        order = np.argsort(probs)
        sorted_y = y_true[order]
        n = len(sorted_y)
        best_k = 0
        cum_defaults = 0
        for k in range(1, n + 1):
            cum_defaults += sorted_y[k - 1]
            loss_rate = cum_defaults / k
            if loss_rate <= target_loss_rate:
                best_k = k
        return best_k

    n_test = len(y_test_oracle)
    y_test_arr = y_test_oracle.values

    appr_at_iso_loss = {
        "legacy": legacy_n_approved,
        "approved_only": iso_loss_approvals(prob_approved, y_test_arr, legacy_loss_rate),
        "inferred": iso_loss_approvals(prob_inferred, y_test_arr, legacy_loss_rate),
        "oracle": iso_loss_approvals(prob_oracle, y_test_arr, legacy_loss_rate),
    }

    # --- ISO-APPROVAL view: at the legacy approval count, what loss rate? ---
    def iso_approval_loss(probs, y_true, n_approve):
        """Approve top-n_approve (lowest predicted PD) and return the loss rate."""
        order = np.argsort(probs)
        approved_y = y_true[order[:n_approve]]
        return float(approved_y.mean()) if n_approve > 0 else 0.0

    loss_at_iso_approval = {
        "legacy": legacy_loss_rate,
        "approved_only": iso_approval_loss(prob_approved, y_test_arr, legacy_n_approved),
        "inferred": iso_approval_loss(prob_inferred, y_test_arr, legacy_n_approved),
        "oracle": iso_approval_loss(prob_oracle, y_test_arr, legacy_n_approved),
    }

    # --- Extra approvals at equal loss ---
    extra_approvals = appr_at_iso_loss["inferred"] - appr_at_iso_loss["legacy"]

    # --- Subgroup breakdowns ---
    test_borrowers = test_all.copy()

    def subgroup_auc(probs, y_true, mask):
        if mask.sum() < 5 or len(np.unique(y_true[mask])) < 2:
            return 0.5
        return float(roc_auc_score(y_true[mask], probs[mask]))

    thin_mask = test_borrowers["bureau_score"].isna().values
    female_mask = (test_borrowers["owner_gender"].values == "female")
    rural_mask = (test_borrowers["location_class"].values == "rural")

    subgroups = {}
    for label, mask in [("thin_file", thin_mask), ("women_led", female_mask), ("rural", rural_mask)]:
        subgroups[label] = {
            "n": int(mask.sum()),
            "auc_approved_only": subgroup_auc(prob_approved, y_test_arr, mask),
            "auc_inferred": subgroup_auc(prob_inferred, y_test_arr, mask),
            "auc_oracle": subgroup_auc(prob_oracle, y_test_arr, mask),
            "legacy_approval_rate": float(legacy_approved_test[mask].mean()) if mask.sum() > 0 else 0.0,
        }

    # --- Expected profit ---
    profit = {}
    for label, probs in [("legacy", prob_legacy), ("approved_only", prob_approved),
                         ("inferred", prob_inferred), ("oracle", prob_oracle)]:
        profit[label] = compute_expected_profit(probs, y_test_arr, APPROVAL_PD_THRESHOLD,
                                                lgd, margin, ticket)

    scoreboard = {
        "model_version": MODEL_VERSION,
        "n_test": n_test,
        "legacy_loss_rate": legacy_loss_rate,
        "legacy_approval_rate": legacy_approval_rate,
        "iso_loss": {
            "description": "Approvals at the loss rate the legacy policy achieved",
            "target_loss_rate": legacy_loss_rate,
            "approvals": appr_at_iso_loss,
        },
        "iso_approval": {
            "description": "Loss rate at the legacy approval count",
            "target_n_approved": legacy_n_approved,
            "loss_rates": loss_at_iso_approval,
        },
        "extra_approvals_at_equal_loss": extra_approvals,
        "auc": {
            "legacy": met_legacy["auc"],
            "approved_only": met_approved["auc"],
            "inferred": met_inferred["auc"],
            "oracle": met_oracle["auc"],
        },
        "subgroups": subgroups,
        "expected_profit": {
            "lgd": lgd,
            "margin": margin,
            "ticket": ticket,
            "values": profit,
        },
    }

    # Also save models for the production path (inferred is "ours")
    models_out = {
        "model_approved": model_approved,
        "model_inferred": model_inferred,
        "model_oracle": model_oracle,
        "cal_approved": cal_approved,
        "cal_inferred": cal_inferred,
        "cal_oracle": cal_oracle,
    }

    return scoreboard, models_out


def _evaluate_model_from_probs(probs, y_true):
    """Evaluate metrics given pre-computed probabilities."""
    if len(np.unique(y_true)) < 2:
        return probs, {"auc": 0.5, "gini": 0.0, "brier": float(brier_score_loss(y_true, probs)),
                       "ks": 0.0, "ece": 0.0}
    auc = float(roc_auc_score(y_true, probs))
    gini = 2 * auc - 1
    brier = float(brier_score_loss(y_true, probs))
    ece = expected_calibration_error(y_true, probs)
    good_prob = probs[y_true == 0]
    bad_prob = probs[y_true == 1]
    ks = float(ks_2samp(good_prob, bad_prob).statistic) if len(good_prob) > 0 and len(bad_prob) > 0 else 0.0
    return probs, {"auc": auc, "gini": float(gini), "brier": brier, "ks": ks, "ece": float(ece)}


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------

def build_artifacts(smoke: bool = False) -> None:
    """Build models and scoreboard.

    This function:
    1. Trains champion (WoE+LR) and challenger (LightGBM) on approved-only data
    2. Runs reject inference (augmentation) to train three comparison models
    3. Generates artifacts/scoreboard.json with iso-loss and iso-approval views
    4. Saves models and metrics
    """
    print("[models] Starting build_artifacts...")
    MODELS.mkdir(exist_ok=True, parents=True)

    # Load data
    borrowers = pd.read_parquet(DATA / "borrowers.parquet")
    outcomes = pd.read_parquet(DATA / "observed_outcomes.parquet")
    oracle = pd.read_parquet(DATA / "oracle.parquet")
    legacy_decisions = pd.read_parquet(DATA / "legacy_decisions.parquet")

    # Merge to get approved-only observed outcomes
    df = borrowers.merge(outcomes, on="id", how="inner").sort_values("id")

    features = model_features()

    # OOT Split (24/36)
    train_df = df[df["application_month"] <= df["oot_train_end"]].copy()
    test_df = df[df["application_month"] >= df["oot_test_start"]].copy()

    X_train = train_df[features]
    y_train = train_df["default_12m"]
    X_test = test_df[features]
    y_test = test_df["default_12m"]

    # Champion: WoE + Logistic Regression
    woe = WoEBinning(bins=5)
    woe.fit(X_train, y_train)
    X_train_woe = woe.transform(X_train)

    champion = LogisticRegression(random_state=42)
    champion.fit(X_train_woe, y_train)

    # Challenger: LightGBM with Monotone Constraints
    spec = by_name()
    monotone_constraints = _get_monotone_constraints(features, spec)
    # Prepare LightGBM data
    X_train_lgb = _prepare_lgb_features(X_train, features, spec)
    X_test_lgb = _prepare_lgb_features(X_test, features, spec)

    # Split train for calibration
    X_tr_fit, X_tr_cal, y_tr_fit, y_tr_cal = train_test_split(X_train_lgb, y_train, test_size=0.2, random_state=42)

    challenger = lgb.LGBMClassifier(
        random_state=42,
        monotone_constraints=monotone_constraints,
        n_estimators=100,
        verbose=-1,
    )
    challenger.fit(X_tr_fit, y_tr_fit)

    # Calibration
    calibrator = IsotonicRegression(out_of_bounds='clip')
    y_tr_cal_prob = challenger.predict_proba(X_tr_cal)[:, 1]
    calibrator.fit(y_tr_cal_prob, y_tr_cal)

    # Metrics: evaluate champion and challenger on approved-only test set
    def evaluate_woe(model, X, y):
        X_eval = woe.transform(X)
        y_prob = model.predict_proba(X_eval)[:, 1]
        return _evaluate_model_from_probs(y_prob, y.values)

    y_prob_champ, champ_metrics = evaluate_woe(champion, X_test, y_test)
    y_prob_chall, chall_metrics = _evaluate_model(challenger, X_test_lgb, y_test, calib=calibrator)

    # LGD from scenarios.yaml
    with open(CONFIGS / "scenarios.yaml", encoding="utf-8") as f:
        scenarios = yaml.safe_load(f)
    lgd = scenarios.get("lgd_default", 0.45)
    margin = 0.10
    ticket = 500000

    profit_champ = compute_expected_profit(y_prob_champ, y_test.values, threshold=0.10, lgd=lgd,
                                           margin=margin, ticket=ticket)
    profit_chall = compute_expected_profit(y_prob_chall, y_test.values, threshold=0.10, lgd=lgd,
                                           margin=margin, ticket=ticket)

    # PSI
    y_train_prob_chall = calibrator.predict(challenger.predict_proba(X_train_lgb)[:, 1])
    psi_challenger = compute_psi(y_train_prob_chall, y_prob_chall)

    # Ablation: bureau-only vs alt-data-only
    bureau_features = ["bureau_score"]
    alt_features = [f for f in features if f != "bureau_score"]

    # LightGBM Bureau Only
    X_tr_fit_bureau = X_tr_fit[bureau_features].copy()
    X_test_bureau = X_test_lgb[bureau_features].copy()
    abl_bureau = lgb.LGBMClassifier(random_state=42, verbose=-1)
    abl_bureau.fit(X_tr_fit_bureau, y_tr_fit)
    y_prob_bureau = abl_bureau.predict_proba(X_test_bureau)[:, 1]
    auc_bureau = roc_auc_score(y_test, y_prob_bureau) if y_test.nunique() > 1 else 0.5

    # LightGBM Alt Only
    X_tr_fit_alt = X_tr_fit[alt_features].copy()
    X_test_alt = X_test_lgb[alt_features].copy()
    abl_alt = lgb.LGBMClassifier(random_state=42, verbose=-1)
    abl_alt.fit(X_tr_fit_alt, y_tr_fit)
    y_prob_alt = abl_alt.predict_proba(X_test_alt)[:, 1]
    auc_alt = roc_auc_score(y_test, y_prob_alt) if y_test.nunique() > 1 else 0.5

    # Thin-file subset (bureau_score is missing)
    thin_mask = X_test["bureau_score"].isna()
    if thin_mask.sum() > 0:
        auc_thin_bureau_only = roc_auc_score(y_test[thin_mask], y_prob_bureau[thin_mask]) if y_test[thin_mask].nunique() > 1 else 0.5
        auc_thin_alt_data = roc_auc_score(y_test[thin_mask], y_prob_alt[thin_mask]) if y_test[thin_mask].nunique() > 1 else 0.5
    else:
        auc_thin_bureau_only = 0.5
        auc_thin_alt_data = 0.5

    # --- T1/T2: Scoreboard (reject inference + comparison) ---
    scoreboard, sb_models = _compute_scoreboard(
        legacy_decisions, borrowers, oracle, features, spec,
        lgd=lgd, margin=margin, ticket=ticket, seed=42,
    )

    # Write scoreboard artifact
    write_json("scoreboard.json", scoreboard)
    
    # --- T2: Model Cockpit Artifacts ---
    def get_roc(y_true, y_prob):
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        idx = np.linspace(0, len(fpr)-1, min(50, len(fpr))).astype(int)
        return {"fpr": fpr[idx].tolist(), "tpr": tpr[idx].tolist()}

    def get_ks_curve(y_true, y_prob):
        y_true_arr = np.asarray(y_true)
        good_prob = y_prob[y_true_arr == 0]
        bad_prob = y_prob[y_true_arr == 1]
        
        thresholds = np.linspace(0, 1, 50)
        cum_good = [float(np.mean(good_prob <= t)) for t in thresholds] if len(good_prob)>0 else [0.0]*50
        cum_bad = [float(np.mean(bad_prob <= t)) for t in thresholds] if len(bad_prob)>0 else [0.0]*50
        
        return {
            "thresholds": thresholds.tolist(),
            "cum_good": cum_good,
            "cum_bad": cum_bad
        }
    
    def get_calib(y_true, y_prob):
        prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)
        return {"prob_true": prob_true.tolist(), "prob_pred": prob_pred.tolist()}

    roc_champ = get_roc(y_test.values, y_prob_champ)
    roc_chall = get_roc(y_test.values, y_prob_chall)
    
    ks_champ = get_ks_curve(y_test.values, y_prob_champ)
    ks_chall = get_ks_curve(y_test.values, y_prob_chall)
    
    calib_champ = get_calib(y_test.values, y_prob_champ)
    calib_chall = get_calib(y_test.values, y_prob_chall)
    
    psi_features = {}
    for f in features:
        if X_train_lgb[f].dtype.name in ['category', 'object']:
            continue
        psi_features[f] = float(compute_psi(X_train_lgb[f].dropna().values, X_test_lgb[f].dropna().values, bins=10))
    
    auc_thin_both = float(roc_auc_score(y_test[thin_mask], y_prob_chall[thin_mask])) if thin_mask.sum() > 0 and y_test[thin_mask].nunique() > 1 else 0.5
    
    cockpit_artifacts = {
        "roc": {"champion": roc_champ, "challenger": roc_chall},
        "ks_curve": {"champion": ks_champ, "challenger": ks_chall},
        "calibration": {"champion": calib_champ, "challenger": calib_chall},
        "ablation": {
            "bureau_only": float(auc_bureau),
            "alt_data_only": float(auc_alt),
            "both": float(chall_metrics["auc"]),
            "thin_bureau_only": float(auc_thin_bureau_only),
            "thin_alt_data": float(auc_thin_alt_data),
            "thin_both": auc_thin_both
        },
        "psi_features": psi_features,
        "champion_metrics": champ_metrics,
        "challenger_metrics": chall_metrics
    }
    write_json("model_cockpit.json", cockpit_artifacts)
    print(f"[models] scoreboard: iso-loss approvals={scoreboard['iso_loss']['approvals']}, "
          f"extra_approvals={scoreboard['extra_approvals_at_equal_loss']}")

    metrics = {
        "auc_champion_oot": float(champ_metrics["auc"]),
        "auc_challenger_oot": float(chall_metrics["auc"]),
        "gini_challenger_oot": float(chall_metrics["gini"]),
        "ks_challenger_oot": float(chall_metrics["ks"]),
        "brier_challenger_oot": float(chall_metrics["brier"]),
        "ece_challenger": float(chall_metrics["ece"]),
        "psi_challenger": float(psi_challenger),
        "expected_profit_champion": float(profit_champ),
        "expected_profit_challenger": float(profit_chall),
        "auc_bureau_only": float(auc_bureau),
        "auc_alt_data": float(auc_alt),
        "auc_thin_bureau_only": float(auc_thin_bureau_only),
        "auc_thin_alt_data": float(auc_thin_alt_data),
        # Scoreboard metrics
        "auc_approved_only_oot": scoreboard["auc"]["approved_only"],
        "auc_inferred_oot": scoreboard["auc"]["inferred"],
        "auc_oracle_oot": scoreboard["auc"]["oracle"],
        "extra_approvals_at_equal_loss": scoreboard["extra_approvals_at_equal_loss"],
        "legacy_loss_rate": scoreboard["legacy_loss_rate"],
    }

    write_metrics("models", metrics)

    # Save models
    with open(MODELS / "champion.pkl", "wb") as f:
        pickle.dump({"model": champion, "woe": woe}, f)
    with open(MODELS / "challenger.pkl", "wb") as f:
        pickle.dump(challenger, f)
    with open(MODELS / "calibrator.pkl", "wb") as f:
        pickle.dump(calibrator, f)

    print("[models] build_artifacts complete.")


# ---------------------------------------------------------------------------
# T3: Sensitivity grid
# ---------------------------------------------------------------------------

def run_grid(smoke: bool = True) -> dict:
    """Run kappa x bias_strength 3x3 grid end-to-end.

    For each cell: generator -> legacy_policy -> models -> scoreboard.
    Returns and writes artifacts/sensitivity_grid.json with per-cell:
        - lift (extra approvals at equal loss)
        - thin_file_auc_lift (inferred AUC - approved-only AUC on thin-file subset)
        - direction_holds (whether lift >= 0)
    """
    from core.generator import build_artifacts as gen_build
    from core.legacy_policy import build_artifacts as legacy_build

    with open(CONFIGS / "generator" / "grid.yaml", encoding="utf-8") as f:
        grid_cfg = yaml.safe_load(f)

    kappa_labels = list(grid_cfg["axes"]["kappa"].keys())
    bias_labels = list(grid_cfg["axes"]["bias_strength"].keys())

    cells = []
    for k_label in kappa_labels:
        for b_label in bias_labels:
            print(f"\n[grid] === Running cell kappa={k_label}, bias={b_label} ===")

            # Step 1: generate data for this cell
            gen_build(smoke=smoke, kappa=k_label, bias_strength=b_label)

            # Step 2: run legacy policy
            legacy_build(smoke=smoke)

            # Step 3: compute scoreboard
            borrowers = pd.read_parquet(DATA / "borrowers.parquet")
            oracle = pd.read_parquet(DATA / "oracle.parquet")
            legacy_decisions = pd.read_parquet(DATA / "legacy_decisions.parquet")

            features = model_features()
            spec = by_name()

            with open(CONFIGS / "scenarios.yaml", encoding="utf-8") as f:
                scenarios = yaml.safe_load(f)
            lgd = scenarios.get("lgd_default", 0.45)

            sb, _ = _compute_scoreboard(
                legacy_decisions, borrowers, oracle, features, spec,
                lgd=lgd, margin=0.10, ticket=500000, seed=42,
            )

            lift = sb["extra_approvals_at_equal_loss"]
            thin_auc_approved = sb["subgroups"].get("thin_file", {}).get("auc_approved_only", 0.5)
            thin_auc_inferred = sb["subgroups"].get("thin_file", {}).get("auc_inferred", 0.5)
            thin_auc_lift = thin_auc_inferred - thin_auc_approved

            cell = {
                "kappa": k_label,
                "bias_strength": b_label,
                "lift_approvals_at_equal_loss": lift,
                "thin_file_auc_lift": round(thin_auc_lift, 4),
                "direction_holds": lift >= 0,
                "auc_approved_only": sb["auc"]["approved_only"],
                "auc_inferred": sb["auc"]["inferred"],
                "auc_oracle": sb["auc"]["oracle"],
                "legacy_loss_rate": sb["legacy_loss_rate"],
                "n_test": sb["n_test"],
            }
            cells.append(cell)
            print(f"[grid]   lift={lift}, thin_auc_lift={thin_auc_lift:.4f}, "
                  f"direction_holds={cell['direction_holds']}")

    grid_result = {
        "model_version": MODEL_VERSION,
        "n_cells": len(cells),
        "kappa_labels": kappa_labels,
        "bias_labels": bias_labels,
        "cells": cells,
    }

    write_json("sensitivity_grid.json", grid_result)
    print(f"\n[grid] Wrote sensitivity_grid.json with {len(cells)} cells.")

    # Restore default config data
    gen_build(smoke=smoke, kappa="medium", bias_strength="medium")
    legacy_build(smoke=smoke)

    return grid_result


# ---------------------------------------------------------------------------
# Production scoring functions (unchanged contract)
# ---------------------------------------------------------------------------

_MODEL_CACHE = {}

def _lazy_load_models():
    if "challenger" not in _MODEL_CACHE:
        with open(MODELS / "challenger.pkl", "rb") as f:
            _MODEL_CACHE["challenger"] = pickle.load(f)
        with open(MODELS / "calibrator.pkl", "rb") as f:
            _MODEL_CACHE["calibrator"] = pickle.load(f)
    return _MODEL_CACHE["challenger"], _MODEL_CACHE["calibrator"]


def score(borrower: Borrower) -> ScoreResult:
    """Return calibrated PD, band, top-3 reasons, data confidence."""
    b = resolve(borrower)
    bid = str(b["id"])

    challenger, calibrator = _lazy_load_models()

    features = model_features()
    spec = by_name()

    # Build dataframe for a single borrower
    row = {f: b.get(f, None) for f in features}
    df = pd.DataFrame([row])

    for f in features:
        if spec[f].get("type") == "cat":
            cats = spec[f].get("categories", [])
            df[f] = pd.Categorical(df[f], categories=cats)
        else:
            df[f] = pd.to_numeric(df[f], errors="coerce")

    # Predict
    pd_raw = challenger.predict_proba(df)[:, 1]
    pd_cal = calibrator.predict(pd_raw)[0]

    # Band
    band = "low" if pd_cal < 0.06 else "medium" if pd_cal < 0.12 else "high"

    # Explain fallback
    reasons = [
        {"feature": "bureau_score", "text": "Bureau score impact.", "impact": 0.05},
        {"feature": "receivable_days", "text": "Receivable days impact.", "impact": 0.03},
        {"feature": "gst_filing_delay_days", "text": "GST filing delay impact.", "impact": 0.02},
    ]

    # Trust fallback
    data_confidence = 80

    # TODO: Handle missing reasons integration: When M2 completes core/explain.py,
    # replace the fallback reason text generator with direct invocation of M2's explainability function.
    try:
        from core.explain import reason_codes
        res = reason_codes(b, challenger)
        if res:
            reasons = res
    except (ImportError, Exception):
        pass

    try:
        from core.trust import trust
        trust_res = trust(b)
        data_confidence = trust_res.get("confidence", 80)
    except (ImportError, Exception):
        pass

    return {
        "borrower_id": bid,
        "pd": float(pd_cal),
        "pd_band": band,
        "reasons": reasons,
        "data_confidence": int(data_confidence),
        "model_version": MODEL_VERSION,
    }


def score_batch(ids_or_df) -> pd.DataFrame:
    """Batch score borrowers."""
    if isinstance(ids_or_df, pd.DataFrame):
        df = ids_or_df
    elif isinstance(ids_or_df, list) and len(ids_or_df) > 0 and isinstance(ids_or_df[0], dict):
        df = pd.DataFrame(ids_or_df)
    else:
        borrowers = pd.read_parquet(DATA / "borrowers.parquet")
        df = borrowers[borrowers["id"].isin(ids_or_df)].copy()

    challenger, calibrator = _lazy_load_models()
    features = model_features()
    spec = by_name()

    X = df[features].copy()
    for f in features:
        if spec[f].get("type") == "cat":
            cats = spec[f].get("categories", [])
            X[f] = pd.Categorical(X[f], categories=cats)
        else:
            X[f] = pd.to_numeric(X[f], errors="coerce")

    pd_raw = challenger.predict_proba(X)[:, 1]
    pd_cal = calibrator.predict(pd_raw)

    res = pd.DataFrame({"id": df["id"].values, "pd": pd_cal})
    res["pd_band"] = np.where(res["pd"] < 0.06, "low", np.where(res["pd"] < 0.12, "medium", "high"))

    if isinstance(ids_or_df, list) and len(ids_or_df) > 0 and isinstance(ids_or_df[0], dict):
        return res.to_dict(orient="records")
    return res


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="M1 Credit Risk Models & Sensitivity Grid")
    parser.add_argument("--grid", action="store_true", help="Run 3x3 sensitivity grid")
    parser.add_argument("--smoke", action="store_true", default=True, help="Use smoke dataset size")
    args = parser.parse_args()

    if args.grid:
        run_grid(smoke=args.smoke)
    else:
        build_artifacts(smoke=args.smoke)

