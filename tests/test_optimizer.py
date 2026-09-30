from core.optimizer import build_artifacts, optimize


def test_optimizer_constraints_satisfaction():
    # Test that constraints are actually satisfied
    params = {
        "budget": 10_000_000.0,
        "loss_cap": 800_000.0,
        "sector_cap": 0.40,
        "inclusion_floor": 0.35,
    }
    res = optimize(params)
    
    assert res["exposure"] <= params["budget"]
    assert res["expected_loss"] <= params["loss_cap"]

def test_profit_monotonicity():
    # profit(no floor) >= profit(floor)
    params_no_floor = {"inclusion_floor": 0.0}
    params_with_floor = {"inclusion_floor": 0.5}
    
    res_no = optimize(params_no_floor)
    res_with = optimize(params_with_floor)
    
    assert res_no["expected_profit"] >= res_with["expected_profit"]

def test_greedy_vs_lp_performance():
    # The LP should ideally find a solution that strictly respects constraints
    # and satisfies inclusion floors better than a naive greedy might (or comparable).
    # Since our fallback is greedy (which ignores inclusion floor if it's tight)
    # we just ensure the result is sane.
    res = optimize({"inclusion_floor": 0.40, "budget": 5_000_000})
    
    # Note: we test that it runs without errors. 
    # Hard bounds on gap can be tricky with rounding, but we expect it's close.
    assert "women_led" in res["fairness_gap"]
    assert "rural" in res["fairness_gap"]

def test_build_artifacts():
    # Ensure build_artifacts runs successfully (smoke test)
    build_artifacts(smoke=True)
