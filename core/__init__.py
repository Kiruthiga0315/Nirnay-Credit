"""Public SDK. The UI imports ONLY from `core` (never from core.<module> internals)."""
from core.documents import make_cam, make_letter
from core.early_warning import watchlist
from core.fairness import fairness_report
from core.models import score
from core.optimizer import optimize
from core.recourse import recourse
from core.stress import stress
from core.structuring import structure
from core.trust import attack, trust

__all__ = [
    "attack", "fairness_report", "make_cam", "make_letter", "optimize", "recourse",
    "score", "stress", "structure", "trust", "watchlist",
]
