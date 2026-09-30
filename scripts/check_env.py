import sys

packages = [
    "lightgbm", "shap", "fairlearn", "networkx", "statsmodels", 
    "scipy", "pyvis", "plotly", "streamlit", "pyarrow", "yaml", "sklearn"
]

def main():
    print(f"Python version: {sys.version.split()[0]}")
    failures = 0
    for pkg in packages:
        try:
            mod = __import__(pkg)
            version = getattr(mod, "__version__", "unknown")
            print(f"OK   {pkg:15s} {version}")
        except Exception as e:
            print(f"FAIL {pkg:15s} not found or failed to load: {type(e).__name__} - {e}")
            failures += 1
            
    if failures > 0:
        sys.exit(1)
    print("All required packages are importable.")

if __name__ == "__main__":
    main()
