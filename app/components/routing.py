"""OWNER: M4. Routing table rules."""

def route_borrower(pd: float, dscr_feasible: bool, data_confidence: int) -> str:
    """Routing rules mapping borrower metrics to processing paths.
    
    Paths:
    - fast-track: PD < 0.05 and high data confidence (>= 80).
    - manual review: PD < 0.10 and medium data confidence (>= 50).
    - structured repayment: PD < 0.15 and DSCR is feasible (e.g. cash flow can support it).
    - decline-with-recourse: High risk or very low data confidence.
    """
    if pd < 0.05 and data_confidence >= 80:
        return "fast-track"
    elif pd < 0.10 and data_confidence >= 50:
        return "manual review"
    elif pd < 0.15 and dscr_feasible:
        return "structured repayment"
    else:
        return "decline-with-recourse"
