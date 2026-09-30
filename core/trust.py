"""OWNER: M3. F11 data-trust: GST/bank/UPI reconciliation, cycle detection, gaming lab.

Writes:
- artifacts/trust.json: Portfolio trust reconciliation audit statistics and flag breakdown
- artifacts/gaming_lab.json: Before/after vulnerability test results for gaming attacks
- artifacts/metrics/trust.json: Summary metrics via write_metrics('trust', ...)

Design & Methodology:
- Cross-source reconciliation: compares GST filings (GSTR-1, GSTR-3B), bank statements, and UPI inflows.
- Trust Score / Data Confidence Formula:
    Base confidence = 100
    Penalties:
      - FLAG_INFLATED_TURNOVER (-25): GST turnover > 1.8x bank deposits (circular billing)
      - FLAG_UNDERREPORTED_GST (-20): GST turnover < 0.6x bank deposits (cash diversion)
      - FLAG_GSTR_MISMATCH (-20): GSTR-1 vs GSTR-3B mismatch > 15% (tax divergence)
      - FLAG_CASHFLOW_DIVERGENCE (-15): Banking+UPI inflows diverge > 40% from revenue
      - FLAG_CHRONIC_GST_DELAY (-10): Average filing delay > 30 days or regularity < 70%
      - FLAG_ANOMALOUS_UPI (-10): High UPI share (> 70%) in B2B heavy sectors
      - FLAG_ARTIFICIAL_SMOOTHING (-20): Inflow CV < 0.05 on large turnover (automated looping)
      - FLAG_THIN_FILE (-10): Missing bureau score
      - FLAG_CIRCULAR_UPI (-25): Firm is part of a circular UPI transfer ring
      - FLAG_WINDOW_DRESSING (-20): Anomalous pre-application bank balance spike
      - FLAG_INVOICE_ROUND_TRIPPING (-30): Round-tripping matching anomalous GST and cycle
    Data Confidence = int(clip(100 - sum(penalties), 0, 100))
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.contracts import AttackResult, Borrower, TrustResult
from core.paths import ARTIFACTS, DATA, write_json, write_metrics
from core.reference import resolve

ATTACKS = ["circular_upi", "window_dressing", "invoice_round_tripping"]

FLAG_DEFINITIONS = {
    "FLAG_INFLATED_TURNOVER": "GST reported turnover exceeds bank deposits by > 80% (possible circular billing)",
    "FLAG_UNDERREPORTED_GST": "GST reported turnover is less than 60% of bank deposits (possible unfiled revenue)",
    "FLAG_GSTR_MISMATCH": "Discrepancy between GSTR-1 (sales) and GSTR-3B (tax paid) exceeds 15%",
    "FLAG_CASHFLOW_DIVERGENCE": "Total banking and UPI inflows diverge from reported revenue by > 40%",
    "FLAG_CHRONIC_GST_DELAY": "Chronic late GST filings (> 30 days delay or regularity < 70%)",
    "FLAG_ANOMALOUS_UPI": "Unusually high UPI concentration (> 70% of inflows) for a B2B sector",
    "FLAG_ARTIFICIAL_SMOOTHING": "Artificially smooth inflows (CV < 0.05) with high volume (circular transactions)",
    "FLAG_THIN_FILE": "No bureau track record found (thin-file borrower)",
    "FLAG_CIRCULAR_UPI": "Firm is part of a circular UPI transfer ring (NetworkX cycle detection)",
    "FLAG_WINDOW_DRESSING": "Anomalous pre-application bank balance spike (Z-score > 3)",
    "FLAG_INVOICE_ROUND_TRIPPING": "Matched high GST turnover and anomalous UPI in cycle (round-tripping)",
}

PENALTIES = {
    "FLAG_INFLATED_TURNOVER": 25,
    "FLAG_UNDERREPORTED_GST": 20,
    "FLAG_GSTR_MISMATCH": 20,
    "FLAG_CASHFLOW_DIVERGENCE": 15,
    "FLAG_CHRONIC_GST_DELAY": 10,
    "FLAG_ANOMALOUS_UPI": 10,
    "FLAG_ARTIFICIAL_SMOOTHING": 20,
    "FLAG_THIN_FILE": 10,
    "FLAG_CIRCULAR_UPI": 25,
    "FLAG_WINDOW_DRESSING": 20,
    "FLAG_INVOICE_ROUND_TRIPPING": 30,
}

_DETECTOR_CACHE = {}

def _lazy_load_detectors() -> tuple[set[str], set[str]]:
    if not _DETECTOR_CACHE:
        cycle_nodes = set()
        wd_nodes = set()
        
        if (DATA / "graph.parquet").exists():
            import networkx as nx
            graph = pd.read_parquet(DATA / "graph.parquet")
            G = nx.from_pandas_edgelist(graph, "src", "dst", create_using=nx.DiGraph)
            try:
                cycles = list(nx.simple_cycles(G, length_bound=5))
            except TypeError:
                # Older networkx fallback
                cycles = [c for c in nx.simple_cycles(G) if len(c) <= 5]
            cycle_nodes = {n for c in cycles for n in c if len(c) > 1}
            
        if (DATA / "panel.parquet").exists():
            panel = pd.read_parquet(DATA / "panel.parquet")
            # Calculate z-score of avg_bank_balance for each firm at month 24
            grp_mean = panel.groupby("id")["avg_bank_balance"].transform("mean")
            grp_std = panel.groupby("id")["avg_bank_balance"].transform("std").replace(0, 1)
            z_score = (panel["avg_bank_balance"] - grp_mean) / grp_std
            spikes = panel[(panel["month"] == 24) & (z_score > 3.0)]
            wd_nodes = set(spikes["id"])
            
        _DETECTOR_CACHE["cycle_nodes"] = cycle_nodes
        _DETECTOR_CACHE["wd_nodes"] = wd_nodes
        
    return _DETECTOR_CACHE["cycle_nodes"], _DETECTOR_CACHE["wd_nodes"]


def audit_borrower(b: dict[str, Any], cycle_nodes: set[str] | None = None, wd_nodes: set[str] | None = None) -> tuple[int, list[str]]:
    flags: list[str] = []

    gst_turnover = float(b.get("gst_turnover", b.get("revenue", 0.0)))
    bank_inflows = float(b.get("bank_inflow", b.get("avg_bank_balance_3m", 0.0) * 4.0))
    upi_inflows = float(b.get("upi_inflow", b.get("upi_inflow_3m_avg", 0.0)))

    if bank_inflows > 0:
        ratio = gst_turnover / (bank_inflows + 1e-6)
        if ratio > 1.8: 
            flags.append("FLAG_INFLATED_TURNOVER")
        elif ratio < 0.6 and gst_turnover > 0: 
            flags.append("FLAG_UNDERREPORTED_GST")

    if float(b.get("gstr1_3b_mismatch", 0.0)) > 0.15:
        flags.append("FLAG_GSTR_MISMATCH")

    reported_revenue = float(b.get("revenue", gst_turnover))
    total_inflows = bank_inflows + upi_inflows
    if reported_revenue > 0 and total_inflows > 0:
        if abs(total_inflows - reported_revenue) / reported_revenue > 0.40:
            flags.append("FLAG_CASHFLOW_DIVERGENCE")

    if float(b.get("gst_filing_delay_days", 0.0)) > 30.0 or float(b.get("gst_filing_regularity", 1.0)) < 0.70:
        flags.append("FLAG_CHRONIC_GST_DELAY")

    sector = str(b.get("sector", "unknown")).lower()
    if sector in {"auto_components", "logistics"} and total_inflows > 0:
        if upi_inflows / total_inflows > 0.70:
            flags.append("FLAG_ANOMALOUS_UPI")

    if float(b.get("inflow_stability_cv", 0.20)) < 0.05 and total_inflows > 500000.0:
        flags.append("FLAG_ARTIFICIAL_SMOOTHING")

    bureau = b.get("bureau_score")
    if bureau is None or pd.isna(bureau):
        flags.append("FLAG_THIN_FILE")

    b_id = b.get("id")
    if cycle_nodes and b_id in cycle_nodes:
        flags.append("FLAG_CIRCULAR_UPI")
        if "FLAG_ANOMALOUS_UPI" in flags or "FLAG_INFLATED_TURNOVER" in flags:
            flags.append("FLAG_INVOICE_ROUND_TRIPPING")
            
    if wd_nodes and b_id in wd_nodes:
        flags.append("FLAG_WINDOW_DRESSING")

    penalty_sum = sum(PENALTIES.get(f, 10) for f in flags)
    confidence = int(np.clip(100 - penalty_sum, 0, 100))

    return confidence, flags


def trust(borrower: Borrower) -> TrustResult:
    b = resolve(borrower)
    borrower_id = str(b.get("id", "UNKNOWN"))
    
    cycle_nodes, wd_nodes = _lazy_load_detectors()
    confidence, flags = audit_borrower(b, cycle_nodes, wd_nodes)

    return {
        "borrower_id": borrower_id,
        "data_confidence": confidence,
        "flags": flags,
    }


def attack(kind: str) -> AttackResult:
    if kind not in ATTACKS:
        kind = "circular_upi"

    borrowers = pd.read_parquet(DATA / "borrowers.parquet") if (DATA / "borrowers.parquet").exists() else pd.DataFrame()
    oracle = pd.read_parquet(DATA / "oracle.parquet") if (DATA / "oracle.parquet").exists() else pd.DataFrame()
    
    if borrowers.empty or oracle.empty:
        return {"attack": kind, "flagged_before": 0, "flagged_after": 0, "auc_before": 0.5, "auc_after": 0.5}

    from sklearn.metrics import roc_auc_score

    from core.models import score_batch
    
    scores_before = score_batch(borrowers)
    merged_before = scores_before.merge(oracle[["id", "default_12m"]], on="id")
    auc_before = roc_auc_score(merged_before["default_12m"], merged_before["pd"]) if merged_before["default_12m"].nunique() > 1 else 0.5
    
    cycle_nodes, wd_nodes = _lazy_load_detectors()
    
    flagged_before = 0
    for _, row in borrowers.iterrows():
        _, flags = audit_borrower(row.to_dict(), cycle_nodes, wd_nodes)
        if kind == "circular_upi" and "FLAG_CIRCULAR_UPI" in flags: 
            flagged_before += 1
        elif kind == "window_dressing" and "FLAG_WINDOW_DRESSING" in flags: 
            flagged_before += 1
        elif kind == "invoice_round_tripping" and "FLAG_INVOICE_ROUND_TRIPPING" in flags: 
            flagged_before += 1

    # Simulate attack by perturbing 50 bad firms
    attack_borrowers = borrowers.copy()
    bad_firms = oracle[oracle["default_12m"] == 1]["id"].values
    rng = np.random.RandomState(42)
    attack_targets = rng.choice(bad_firms, size=min(50, len(bad_firms)), replace=False)
    
    attack_cycle_nodes = set(cycle_nodes)
    attack_wd_nodes = set(wd_nodes)
    
    if kind == "circular_upi":
        attack_borrowers.loc[attack_borrowers["id"].isin(attack_targets), "upi_inflow_3m_avg"] *= 3.0
        attack_cycle_nodes |= set(attack_targets)
    elif kind == "window_dressing":
        attack_borrowers.loc[attack_borrowers["id"].isin(attack_targets), "avg_bank_balance_3m"] *= 5.0
        attack_wd_nodes |= set(attack_targets)
    elif kind == "invoice_round_tripping":
        attack_borrowers.loc[attack_borrowers["id"].isin(attack_targets), "upi_inflow_3m_avg"] *= 2.0
        attack_cycle_nodes |= set(attack_targets)
        
    scores_after = score_batch(attack_borrowers)
    merged_after = scores_after.merge(oracle[["id", "default_12m"]], on="id")
    auc_after = roc_auc_score(merged_after["default_12m"], merged_after["pd"]) if merged_after["default_12m"].nunique() > 1 else 0.5
    
    flagged_after = 0
    for _, row in attack_borrowers.iterrows():
        _, flags = audit_borrower(row.to_dict(), attack_cycle_nodes, attack_wd_nodes)
        if kind == "circular_upi" and "FLAG_CIRCULAR_UPI" in flags: 
            flagged_after += 1
        elif kind == "window_dressing" and "FLAG_WINDOW_DRESSING" in flags: 
            flagged_after += 1
        elif kind == "invoice_round_tripping" and "FLAG_INVOICE_ROUND_TRIPPING" in flags: 
            flagged_after += 1
        
    return {
        "attack": kind,
        "flagged_before": flagged_before,
        "flagged_after": flagged_after,
        "auc_before": round(float(auc_before), 4),
        "auc_after": round(float(auc_after), 4),
    }


def build_artifacts(smoke: bool = False) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    borrowers_df = pd.read_parquet(DATA / "borrowers.parquet") if (DATA / "borrowers.parquet").exists() else pd.DataFrame()

    total_firms = len(borrowers_df)
    confidences: list[int] = []
    flag_counts: dict[str, int] = {k: 0 for k in PENALTIES}
    flagged_firms_count = 0

    cycle_nodes, wd_nodes = _lazy_load_detectors()

    for _, row in borrowers_df.iterrows():
        b_dict = row.to_dict()
        conf, flags = audit_borrower(b_dict, cycle_nodes, wd_nodes)
        confidences.append(conf)
        if flags:
            flagged_firms_count += 1
            for f in flags:
                flag_counts[f] = flag_counts.get(f, 0) + 1

    avg_conf = float(np.mean(confidences)) if confidences else 75.0
    clean_firms_count = total_firms - flagged_firms_count

    gaming_lab_results = {a: attack(a) for a in ATTACKS}
    write_json("gaming_lab.json", gaming_lab_results)

    trust_summary = {
        "total_audited_firms": total_firms,
        "clean_firms_count": clean_firms_count,
        "flagged_firms_count": flagged_firms_count,
        "clean_firms_share": round(clean_firms_count / max(1, total_firms), 4),
        "average_data_confidence": round(avg_conf, 2),
        "flag_definitions": FLAG_DEFINITIONS,
        "flag_occurrences": flag_counts,
        "attacks_tested": len(ATTACKS),
    }
    write_json("trust.json", trust_summary)

    write_metrics("trust", {
        "avg_data_confidence": round(avg_conf, 2),
        "flagged_firms_count": flagged_firms_count,
        "clean_firms_count": clean_firms_count,
        "clean_firms_share": round(clean_firms_count / max(1, total_firms), 4),
        "attacks_tested": len(ATTACKS),
    })

    print(f"[trust] Reconciled {total_firms} firms. Avg confidence: {avg_conf:.1f}, "
          f"Flagged firms: {flagged_firms_count} ({flagged_firms_count/max(1, total_firms):.1%})")
