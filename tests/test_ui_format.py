import pytest

pytest.importorskip("streamlit")
from app.components.ui import inr


def test_inr_grouping():
    assert inr(1234567) == "₹12,34,567"
    assert inr(999) == "₹999"
    assert inr(100000) == "₹1,00,000"
    assert inr(-25000) == "-₹25,000"
    assert inr(12345.5, 2) == "₹12,345.50"
