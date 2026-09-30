# Owner: M3. Optional (Windows users: run the plain commands listed in README).
.RECIPEPREFIX = >
.PHONY: setup check smoke run-all app snapshot clean offline-demo health claims

setup:
> python -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt

check:
> ruff check . && pytest

smoke:
> python run_all.py --smoke --keep-going

run-all:
> python run_all.py

app:
> streamlit run app/Home.py

snapshot:
> python run_all.py && rm -rf demo_snapshot/artifacts && mkdir -p demo_snapshot && cp -r artifacts demo_snapshot/artifacts && chmod +x scripts/offline_demo.sh && echo "snapshot ready: commit demo_snapshot/ (M3 only)"

offline-demo:
> DRY_RUN=1 bash scripts/offline_demo.sh

health:
> python scripts/health_check.py --no-pull

claims:
> pytest tests/test_claims.py -v --tb=short

clean:
> rm -rf data/* models/* artifacts/* .pytest_cache .ruff_cache
