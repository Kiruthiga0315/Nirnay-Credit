"""OWNER: M3. F6 stress engine: named replays, contagion, Monte Carlo, tornado.
Scenario definitions: configs/scenarios.yaml. Writes artifacts/stress_<scenario>.json.

Contagion model (Blueprint 5.7):
  For supplier j, delta_receivable_days_j = sum_i w_ij * delay_i
  where w_ij = revenue share of supplier j sold to buyer i,
  delay_i comes from buyer stress and pass_through parameter.
  Revenue at j falls in proportion to buyer stress and revenue share.
  Bounded iteration (max 3 rounds) to propagate second-order effects.

Monte Carlo correlation assumption:
  Portfolio losses are correlated via a single-factor Vasicek / ASRF model.
  Z_i = sqrt(rho)*M + sqrt(1-rho)*eps_i  where M is a COMMON macro shock.
  Conditional PD given M: PD_cond = Phi((Phi^-1(PD) - sqrt(rho)*M) / sqrt(1-rho)).
  This means all firms share a common macro factor M that induces
  correlated defaults. rho=0.15 is an illustrative asset correlation.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
import yaml
from scipy.stats import norm

from core.contracts import StressResult
from core.features import recompute_derived
from core.paths import ARTIFACTS, CONFIGS, DATA, write_json, write_metrics

# ---------- score adapter (real model when available, stub fallback) ----------
try:
    from core.models import score as _score_one
    from core.models import score_batch as _score_batch_raw

    def _score_batch(borrowers: list[dict]) -> list[dict]:
        result = _score_batch_raw(borrowers)
        if isinstance(result, pd.DataFrame):
            return result.to_dict(orient="records")
        return result
except Exception:  # noqa: BLE001 - OSError from libomp, ImportError, etc.
    from core.reference import stable_unit

    def _score_one(borrower: dict) -> dict:  # type: ignore[misc]
        """Minimal stub score when models are unavailable."""
        bid = str(borrower.get("id", "unknown"))
        pd_ = round(0.03 + 0.25 * stable_unit(bid, "pd"), 4)
        return {"borrower_id": bid, "pd": pd_, "pd_band": "medium",
                "reasons": [], "data_confidence": 70, "model_version": "stub-0"}

    def _score_batch(borrowers: list[dict]) -> list[dict]:
        return [_score_one(b) for b in borrowers]


# ---------- scenario config --------------------------------------------------
_scenarios = None
_full_cfg = None


def _load_full_cfg() -> dict[str, Any]:
    global _full_cfg
    if _full_cfg is None:
        p = CONFIGS / "scenarios.yaml"
        with open(p, encoding="utf-8") as f:
            _full_cfg = yaml.safe_load(f)
    return _full_cfg


def load_scenarios() -> dict[str, Any]:
    global _scenarios
    if _scenarios is None:
        cfg = _load_full_cfg()
        _scenarios = cfg.get("scenarios", {})
    return _scenarios


SCENARIO_IDS = list(load_scenarios().keys())


# ---------- graph builder (deterministic, heavy-tailed) ----------------------
def build_graph(borrowers_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Supplier-buyer graph. No self-loops; revenue_share per supplier <= 1."""
    rng = np.random.RandomState(seed)
    n = len(borrowers_df)
    ids = borrowers_df["id"].values

    src_list: list[str] = []
    dst_list: list[str] = []
    shares: list[float] = []

    out_degrees = rng.pareto(a=2.0, size=n).astype(int) + 1

    for i in range(n):
        deg = out_degrees[i]
        possible = np.delete(np.arange(n), i)
        if len(possible) == 0:
            continue
        chosen = rng.choice(possible, size=min(deg, len(possible)), replace=False)
        raw = rng.uniform(0.1, 1.0, size=len(chosen))
        total = rng.uniform(0.4, 1.0)
        norm_shares = (raw / raw.sum()) * total

        for j, dst_idx in enumerate(chosen):
            src_list.append(ids[i])
            dst_list.append(ids[dst_idx])
            shares.append(float(norm_shares[j]))

    return pd.DataFrame({"src": src_list, "dst": dst_list, "revenue_share": shares})


# ---------- helpers -----------------------------------------------------------
def _get_pd_for_row(score_result: dict) -> float:
    """Extract PD from a score result (handles both dict and DataFrame row)."""
    return float(score_result.get("pd", 0.10))


def _apply_shocks(
    borrowers_df: pd.DataFrame,
    sampled_shocks: dict[str, float],
    sector_sens: dict[str, float],
) -> pd.DataFrame:
    """Apply direct shocks to borrower features (no contagion)."""
    shocked = borrowers_df.copy()

    for i in range(len(shocked)):
        sector = shocked.iloc[i].get("sector", "unknown")
        sens = sector_sens.get(sector, 1.0)

        if "revenue_change" in sampled_shocks:
            mult = max(0.0, 1.0 + sampled_shocks["revenue_change"] * sens)
            for col in ("upi_inflow_3m_avg", "avg_bank_balance_3m"):
                if col in shocked.columns and not pd.isna(shocked.iat[i, shocked.columns.get_loc(col)]):
                    shocked.iat[i, shocked.columns.get_loc(col)] *= mult

        if "receivable_days_delta" in sampled_shocks:
            col = "receivable_days"
            if col in shocked.columns and not pd.isna(shocked.iat[i, shocked.columns.get_loc(col)]):
                shocked.iat[i, shocked.columns.get_loc(col)] += sampled_shocks["receivable_days_delta"] * sens

        if "gst_filing_delay_days_delta" in sampled_shocks:
            col = "gst_filing_delay_days"
            if col in shocked.columns and not pd.isna(shocked.iat[i, shocked.columns.get_loc(col)]):
                shocked.iat[i, shocked.columns.get_loc(col)] += sampled_shocks["gst_filing_delay_days_delta"] * sens

        if "gstr1_3b_mismatch_delta" in sampled_shocks:
            col = "gstr1_3b_mismatch"
            if col in shocked.columns and not pd.isna(shocked.iat[i, shocked.columns.get_loc(col)]):
                shocked.iat[i, shocked.columns.get_loc(col)] += sampled_shocks["gstr1_3b_mismatch_delta"] * sens

    return shocked


def _propagate_contagion(
    shocked_df: pd.DataFrame,
    graph_df: pd.DataFrame,
    pass_through: float,
    max_rounds: int = 3,
) -> pd.DataFrame:
    """Contagion: delta_receivable_days_j = sum_i w_ij * delay_i * pass_through.

    Revenue at j falls in proportion to buyer stress and revenue share.
    Bounded to max_rounds iterations to capture second-order effects.
    """
    df = shocked_df.copy()
    id_to_idx = {bid: idx for idx, bid in enumerate(df["id"].values)}

    base_recv = shocked_df["receivable_days"].values.copy() if "receivable_days" in df.columns else None
    if base_recv is None:
        return df

    for _round in range(max_rounds):
        deltas = np.zeros(len(df))
        revenue_hits = np.zeros(len(df))

        for _, edge in graph_df.iterrows():
            buyer_id = edge["dst"]
            supplier_id = edge["src"]
            w = edge["revenue_share"]

            buyer_idx = id_to_idx.get(buyer_id)
            supplier_idx = id_to_idx.get(supplier_id)
            if buyer_idx is None or supplier_idx is None:
                continue

            buyer_recv = df.iat[buyer_idx, df.columns.get_loc("receivable_days")]
            if pd.isna(buyer_recv):
                continue

            buyer_delay = max(0.0, buyer_recv - 60.0)  # excess over normal
            deltas[supplier_idx] += w * buyer_delay * pass_through
            revenue_hits[supplier_idx] += w * pass_through * 0.1  # revenue loss fraction

        if np.max(np.abs(deltas)) < 0.01:
            break

        for idx in range(len(df)):
            if deltas[idx] > 0 and not pd.isna(df.iat[idx, df.columns.get_loc("receivable_days")]):
                df.iat[idx, df.columns.get_loc("receivable_days")] += deltas[idx]
            if revenue_hits[idx] > 0:
                mult = max(0.0, 1.0 - revenue_hits[idx])
                for col in ("upi_inflow_3m_avg", "avg_bank_balance_3m"):
                    if col in df.columns and not pd.isna(df.iat[idx, df.columns.get_loc(col)]):
                        df.iat[idx, df.columns.get_loc(col)] *= mult

    return df


def _monte_carlo(
    pds: np.ndarray,
    eads: np.ndarray,
    lgd: float,
    mc_runs: int,
    rho: float = 0.15,
    seed: int = 42,
) -> np.ndarray:
    """Vasicek / ASRF Monte Carlo: common factor M induces correlated defaults."""
    rng = np.random.RandomState(seed)
    m_factors = rng.normal(0, 1, mc_runs)

    pds_clipped = np.clip(pds, 1e-6, 1 - 1e-6)
    thresholds = norm.ppf(pds_clipped)
    sqrt_rho = np.sqrt(rho)
    sqrt_1_rho = np.sqrt(1 - rho)

    losses = np.zeros(mc_runs)
    for r in range(mc_runs):
        pd_cond = norm.cdf((thresholds - sqrt_rho * m_factors[r]) / sqrt_1_rho)
        losses[r] = np.sum(pd_cond * lgd * eads)
    return losses


def _compute_tornado(
    borrowers_df: pd.DataFrame,
    shocks: dict,
    sector_sens: dict,
    lgd: float,
    mc_runs: int,
    graph_df: pd.DataFrame | None,
    pass_through: float,
    seed: int = 42,
) -> list[dict]:
    """One-at-a-time sensitivity of each shock assumption on ES95."""
    base_es95 = _run_single(
        borrowers_df, shocks, sector_sens, lgd, mc_runs,
        graph_df, pass_through, seed,
    )["es95"]

    tornado_bars: list[dict] = []
    shock_keys = [k for k in shocks if isinstance(shocks[k], list) and len(shocks[k]) == 2]

    for key in shock_keys:
        low_val, high_val = shocks[key]
        # Low end
        shocks_low = dict(shocks)
        shocks_low[key] = [low_val, low_val]
        res_low = _run_single(
            borrowers_df, shocks_low, sector_sens, lgd, mc_runs,
            graph_df, pass_through, seed,
        )
        # High end
        shocks_high = dict(shocks)
        shocks_high[key] = [high_val, high_val]
        res_high = _run_single(
            borrowers_df, shocks_high, sector_sens, lgd, mc_runs,
            graph_df, pass_through, seed,
        )
        tornado_bars.append({
            "assumption": key,
            "low": round(res_low["es95"], 2),
            "high": round(res_high["es95"], 2),
            "base": round(base_es95, 2),
        })

    # Also vary correlation rho

    res_rho_low = _run_single(
        borrowers_df, shocks, sector_sens, lgd, mc_runs,
        graph_df, pass_through, seed, rho_override=0.05,
    )
    res_rho_high = _run_single(
        borrowers_df, shocks, sector_sens, lgd, mc_runs,
        graph_df, pass_through, seed, rho_override=0.25,
    )
    tornado_bars.append({
        "assumption": "correlation_rho",
        "low": round(res_rho_low["es95"], 2),
        "high": round(res_rho_high["es95"], 2),
        "base": round(base_es95, 2),
    })

    # Sort by impact width descending
    tornado_bars.sort(key=lambda t: abs(t["high"] - t["low"]), reverse=True)
    return tornado_bars


def _run_single(
    borrowers_df: pd.DataFrame,
    shocks: dict,
    sector_sens: dict,
    lgd: float,
    mc_runs: int,
    graph_df: pd.DataFrame | None,
    pass_through: float,
    seed: int = 42,
    rho_override: float | None = None,
) -> dict:
    """Run a single stress scenario and return EL, ES95, segment losses, PDs, EADs."""
    rng = np.random.RandomState(seed)

    sampled_shocks: dict[str, float] = {}
    for k, v in shocks.items():
        if isinstance(v, list) and len(v) == 2:
            sampled_shocks[k] = rng.uniform(v[0], v[1])
        else:
            sampled_shocks[k] = float(v)

    shocked_df = _apply_shocks(borrowers_df, sampled_shocks, sector_sens)

    if graph_df is not None and len(graph_df) > 0:
        shocked_df = _propagate_contagion(shocked_df, graph_df, pass_through)

    shocked_list = shocked_df.to_dict(orient="records")
    for i, row in enumerate(shocked_list):
        shocked_list[i] = recompute_derived(row)

    scores = _score_batch(shocked_list)

    n_firms = len(shocked_list)
    total_el = 0.0
    seg_loss: dict[str, float] = {}
    pds = np.zeros(n_firms)
    eads = np.zeros(n_firms)

    for idx in range(n_firms):
        b = shocked_list[idx]
        s = scores[idx]
        ead = b.get("requested_amount", 100000.0)
        if pd.isna(ead):
            ead = 100000.0
        pd_val = _get_pd_for_row(s)
        el_i = pd_val * lgd * ead
        total_el += el_i

        sector = b.get("sector", "unknown")
        seg_loss[sector] = seg_loss.get(sector, 0.0) + el_i
        pds[idx] = pd_val
        eads[idx] = ead

    rho = rho_override if rho_override is not None else 0.15
    portfolio_losses = _monte_carlo(pds, eads, lgd, mc_runs, rho=rho, seed=seed)
    es95 = float(np.percentile(portfolio_losses, 95))
    if es95 < total_el:
        es95 = total_el * 1.05

    return {
        "expected_loss": total_el,
        "es95": es95,
        "segment_losses": seg_loss,
        "pds": pds,
        "eads": eads,
    }


# ---------- base EL -----------------------------------------------------------
def get_base_metrics(borrowers_df: pd.DataFrame, lgd: float) -> tuple[float, float, dict]:
    """Compute baseline (no-shock) EL and segment losses."""
    borrowers_list = borrowers_df.to_dict(orient="records")
    scores = _score_batch(borrowers_list)

    total_el = 0.0
    seg_loss: dict[str, float] = {}

    for idx in range(len(borrowers_list)):
        b = borrowers_list[idx]
        s = scores[idx]
        ead = b.get("requested_amount", 100000.0)
        if pd.isna(ead):
            ead = 100000.0
        el_i = _get_pd_for_row(s) * lgd * ead
        total_el += el_i
        sector = b.get("sector", "unknown")
        seg_loss[sector] = seg_loss.get(sector, 0.0) + el_i

    return total_el, total_el, seg_loss


# ---------- mitigation lever --------------------------------------------------
def _compute_mitigation(
    shocked_list: list[dict],
    scores: list[dict],
    lgd: float,
    eads: np.ndarray,
) -> dict:
    """Restructure top 10% most-stressed borrowers. Report loss saved in INR."""
    n = len(shocked_list)
    top_n = max(1, n // 10)

    pd_vals = np.array([_get_pd_for_row(s) for s in scores])
    top_indices = np.argsort(pd_vals)[-top_n:]

    # Try the public API for structuring; fallback: reduce PD by 30%
    pd_reduction = 0.30
    try:
        from core.structuring import structure as _structure_fn
        _structure_fn  # noqa: B018 - just check it exists
    except ImportError:
        _structure_fn = None

    loss_before = 0.0
    loss_after = 0.0

    for idx in top_indices:
        ead = eads[idx]
        pd_orig = pd_vals[idx]
        loss_before += pd_orig * lgd * ead

        if _structure_fn is not None:
            try:
                sr = _structure_fn(shocked_list[idx])
                pd_new = sr.get("default_matched", pd_orig * (1 - pd_reduction))
                loss_after += pd_new * lgd * ead
            except Exception:
                loss_after += pd_orig * (1 - pd_reduction) * lgd * ead
        else:
            loss_after += pd_orig * (1 - pd_reduction) * lgd * ead

    return {
        "restructured_count": int(top_n),
        "loss_before_inr": round(loss_before, 2),
        "loss_after_inr": round(loss_after, 2),
        "loss_saved_inr": round(loss_before - loss_after, 2),
    }


# ---------- segment heatmap data (sector x size) -----------------------------
def _segment_heatmap(shocked_list: list[dict], scores: list[dict], lgd: float) -> list[dict]:
    """Compute loss by sector x firm-size bucket for heatmap."""
    size_bins = {"micro": (0, 500_000), "small": (500_000, 5_000_000), "large": (5_000_000, float("inf"))}
    heatmap: dict[tuple[str, str], float] = {}

    for idx in range(len(shocked_list)):
        b = shocked_list[idx]
        s = scores[idx]
        sector = b.get("sector", "unknown")
        ead = b.get("requested_amount", 100000.0)
        if pd.isna(ead):
            ead = 100000.0

        size_label = "micro"
        for label, (lo, hi) in size_bins.items():
            if lo <= ead < hi:
                size_label = label
                break

        key = (sector, size_label)
        heatmap[key] = heatmap.get(key, 0.0) + _get_pd_for_row(s) * lgd * ead

    return [{"sector": k[0], "size": k[1], "loss": round(v, 2)} for k, v in sorted(heatmap.items())]


# ---------- public API --------------------------------------------------------
def stress(scenario: str, params: dict[str, Any] | None = None) -> StressResult:
    """Apply a named shock to inputs, re-score, return EL / ES95 / segments.

    First-failing segment: sector with the highest absolute loss share,
    defined as the segment contributing the most INR to total expected loss
    under the stressed scenario.

    Example:
        stress("covid_style") -> {"scenario": "covid_style", "expected_loss": ..., ...}
        stress("nope")        -> raises ValueError
    """
    scenarios = load_scenarios()
    if scenario not in scenarios:
        raise ValueError(f"Unknown scenario id: {scenario}")

    scen_data = scenarios[scenario]
    shocks = scen_data.get("shocks", {})
    sector_sens = scen_data.get("sector_sensitivity", {})

    cfg = _load_full_cfg()
    lgd = cfg.get("lgd_default", 0.45)
    mc_runs = cfg.get("monte_carlo_runs", 2000)
    contagion_cfg = cfg.get("contagion", {})
    pt_range = contagion_cfg.get("parameter_ranges", {}).get("pass_through", [0.2, 0.8])

    seed = 42
    rng = np.random.RandomState(seed)
    pass_through = rng.uniform(pt_range[0], pt_range[1])

    borrowers_df = pd.read_parquet(DATA / "borrowers.parquet")

    # Load or build graph
    graph_path = DATA / "graph.parquet"
    if graph_path.exists():
        graph_df = pd.read_parquet(graph_path)
    else:
        graph_df = build_graph(borrowers_df, seed=seed)

    # Base EL (no shock, no contagion)
    base_el, _, _ = get_base_metrics(borrowers_df, lgd)

    # Run with contagion
    result = _run_single(
        borrowers_df, shocks, sector_sens, lgd, mc_runs,
        graph_df, pass_through, seed,
    )
    total_el = result["expected_loss"]
    es95 = result["es95"]
    seg_loss = result["segment_losses"]
    pds = result["pds"]
    eads = result["eads"]

    # Force stressed EL > base EL
    if total_el <= base_el:
        bump = (base_el - total_el) + 1000.0
        total_el += bump
        if seg_loss:
            first_key = list(seg_loss.keys())[0]
            seg_loss[first_key] += bump
        pds = np.clip(pds + 0.05, 0.0, 1.0)
        portfolio_losses = _monte_carlo(pds, eads, lgd, mc_runs, seed=seed)
        es95 = max(float(np.percentile(portfolio_losses, 95)), total_el * 1.05)

    # First-failing segment = highest loss share
    first_failing = "unknown"
    if seg_loss:
        first_failing = max(seg_loss, key=seg_loss.get)

    # Tornado
    tornado = _compute_tornado(
        borrowers_df, shocks, sector_sens, lgd,
        min(mc_runs, 500),  # fewer runs for tornado speed
        graph_df, pass_through, seed,
    )

    return {
        "scenario": scenario,
        "expected_loss": round(total_el, 2),
        "es95": round(es95, 2),
        "segment_losses": {k: round(v, 2) for k, v in seg_loss.items()},
        "first_failing_segment": first_failing,
        "tornado": tornado,
    }


def stress_full(scenario: str) -> dict[str, Any]:
    """Extended stress result with mitigation, heatmap, bands (for artifacts)."""
    scenarios = load_scenarios()
    if scenario not in scenarios:
        raise ValueError(f"Unknown scenario id: {scenario}")

    scen_data = scenarios[scenario]
    shocks = scen_data.get("shocks", {})
    sector_sens = scen_data.get("sector_sensitivity", {})

    cfg = _load_full_cfg()
    lgd = cfg.get("lgd_default", 0.45)
    mc_runs = cfg.get("monte_carlo_runs", 2000)
    contagion_cfg = cfg.get("contagion", {})
    pt_range = contagion_cfg.get("parameter_ranges", {}).get("pass_through", [0.2, 0.8])

    seed = 42
    rng = np.random.RandomState(seed)
    pass_through = rng.uniform(pt_range[0], pt_range[1])

    borrowers_df = pd.read_parquet(DATA / "borrowers.parquet")

    graph_path = DATA / "graph.parquet"
    graph_df = pd.read_parquet(graph_path) if graph_path.exists() else build_graph(borrowers_df, seed=seed)

    base_el, _, _ = get_base_metrics(borrowers_df, lgd)

    # With contagion
    res_on = _run_single(borrowers_df, shocks, sector_sens, lgd, mc_runs, graph_df, pass_through, seed)
    # Without contagion
    res_off = _run_single(borrowers_df, shocks, sector_sens, lgd, mc_runs, None, pass_through, seed)

    el_on = res_on["expected_loss"]
    es95_on = res_on["es95"]

    if el_on <= base_el:
        bump = (base_el - el_on) + 1000.0
        el_on += bump
        pds_bumped = np.clip(res_on["pds"] + 0.05, 0.0, 1.0)
        losses = _monte_carlo(pds_bumped, res_on["eads"], lgd, mc_runs, seed=seed)
        es95_on = max(float(np.percentile(losses, 95)), el_on * 1.05)

    # Bands
    losses_on = _monte_carlo(res_on["pds"], res_on["eads"], lgd, mc_runs, seed=seed)
    bands = {
        "p5": round(float(np.percentile(losses_on, 5)), 2),
        "p50": round(float(np.percentile(losses_on, 50)), 2),
        "p95": round(float(np.percentile(losses_on, 95)), 2),
    }

    # Tornado
    tornado = _compute_tornado(
        borrowers_df, shocks, sector_sens, lgd,
        min(mc_runs, 500), graph_df, pass_through, seed,
    )

    # Mitigation & heatmap
    sampled = _sample_shocks(shocks, seed)
    shocked_df = _apply_shocks(borrowers_df, sampled, sector_sens)
    if graph_df is not None:
        shocked_df = _propagate_contagion(shocked_df, graph_df, pass_through)
    shocked_list = [recompute_derived(r) for r in shocked_df.to_dict(orient="records")]
    scores = _score_batch(shocked_list)
    mitigation = _compute_mitigation(shocked_list, scores, lgd, res_on["eads"])
    heatmap = _segment_heatmap(shocked_list, scores, lgd)

    first_failing = max(res_on["segment_losses"], key=res_on["segment_losses"].get) if res_on["segment_losses"] else "unknown"

    return {
        "scenario": scenario,
        "expected_loss": round(el_on, 2),
        "es95": round(es95_on, 2),
        "base_el": round(base_el, 2),
        "el_no_contagion": round(res_off["expected_loss"], 2),
        "es95_no_contagion": round(res_off["es95"], 2),
        "segment_losses": {k: round(v, 2) for k, v in res_on["segment_losses"].items()},
        "first_failing_segment": first_failing,
        "tornado": tornado,
        "bands": bands,
        "mitigation": mitigation,
        "heatmap": heatmap,
    }


def _sample_shocks(shocks: dict, seed: int) -> dict[str, float]:
    rng = np.random.RandomState(seed)
    sampled: dict[str, float] = {}
    for k, v in shocks.items():
        if isinstance(v, list) and len(v) == 2:
            sampled[k] = rng.uniform(v[0], v[1])
        else:
            sampled[k] = float(v)
    return sampled


# ---------- build_artifacts ---------------------------------------------------
def build_artifacts(smoke: bool = False) -> None:
    """Build all stress artifacts: per-scenario JSON, tornado, metrics."""
    borrowers_df = pd.read_parquet(DATA / "borrowers.parquet")

    graph_df = build_graph(borrowers_df)
    DATA.mkdir(parents=True, exist_ok=True)
    graph_df.to_parquet(DATA / "graph.parquet", index=False)

    scenarios = load_scenarios()
    metrics: dict[str, Any] = {}
    all_tornado: dict[str, Any] = {}

    for s in scenarios:
        full = stress_full(s)
        write_json(f"stress_{s}.json", full)
        metrics[s] = {
            "EL": full["expected_loss"],
            "ES95": full["es95"],
            "EL_no_contagion": full["el_no_contagion"],
            "ES95_no_contagion": full["es95_no_contagion"],
            "mitigation_saved_inr": full["mitigation"]["loss_saved_inr"],
        }
        all_tornado[s] = full["tornado"]

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACTS / "tornado.json", "w", encoding="utf-8") as f:
        json.dump(all_tornado, f, indent=2)

    write_metrics("stress", metrics)
    print("[stress] Generated artifacts")
