# Deploy (owner: M3)

## Local Fallback Command
If cloud deployment fails, run the application locally:
```bash
python run_all.py
streamlit run app/Home.py
```

## Creating a Snapshot
To create a frozen state of the data for deployment without recalculating:
```bash
make snapshot
```
> **Note:** The `make snapshot` command creates the `demo_snapshot/` folder. This is a **MANUAL** step done by M3 to commit the frozen artifacts before deploying.

## Lock Requirements
Before deploying, lock the exact package versions used in development:
```bash
pip freeze > requirements.lock
```

## Streamlit Community Cloud (Recommended)
1. **[MANUAL]** Push your repository to GitHub and ensure `main` branch is protected.
2. **[MANUAL]** Go to [share.streamlit.io](https://share.streamlit.io) and click "New app".
3. Point to your repository, branch `main`, and main file path `app/Home.py`.
4. Select Python version 3.11.
5. In advanced settings, add any necessary secrets.
6. Click Deploy. Streamlit will install from `requirements.txt` (or `requirements.lock` if present).

## Hugging Face Spaces (Alternative)
1. **[MANUAL]** Go to [huggingface.co/spaces](https://huggingface.co/spaces) and click "Create new Space".
2. Name the space, select "Streamlit" as the SDK.
3. Choose the Space hardware.
4. **[MANUAL]** Link your GitHub repository or push code directly to the HF Space remote.
5. Ensure `app/Home.py` is either renamed to `app.py` or configured in the space settings as the startup file.
6. Set any secrets in the Space settings.
