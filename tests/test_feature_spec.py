from core.features import by_name, levers, load_spec, model_features


def test_spec_shape():
    spec = load_spec()
    for f in spec["features"]:
        assert f["mutability"] in spec["mutability_classes"]
        assert f["monotone_pd"] in (-1, 0, 1)
        assert f["label"]


def test_protected_never_model_inputs():
    b = by_name()
    for name in ("owner_gender", "location_class"):
        assert b[name]["model_input"] is False
    assert not {"owner_gender", "location_class"} & set(model_features())


def test_levers_are_verifiable_and_not_gameable():
    for name in levers():
        assert by_name()[name]["mutability"] == "verifiable"
    assert "avg_bank_balance_3m" not in levers()
