# Architecture (see docs/ideas/PS12_Winning_Blueprint.md Section 5 for the full spec)

    configs/*  ->  core.generator -> data/*.parquet -> core.legacy_policy (stochastic) -> observed outcomes
                                   -> core.models (champion WoE-logit, challenger monotone LightGBM, calibration)
                                   -> core.explain / recourse / forecast / structuring / fairness / optimizer
                                   -> core.stress / early_warning / trust / governance
                                   -> artifacts/*.json|parquet  ->  app/ (Streamlit, reads only artifacts)
    run_all.py orchestrates every stage; each stage = core.<module>.build_artifacts(smoke)

Principles: one owner per file; frozen contracts; UI never computes heavy things; every number traceable to
`artifacts/metrics.json`; stubs let the UI run from hour 0.
