# Agent Instructions for BAC Segmentation

## Architecture & Entrypoints
* **Data Flow**: `data/raw` (DICOM) -> `data/interim` -> `data/processed` (PNG splits).
* **Model**: Mix Vision Transformer (PVT) + MLP Decoder. Inputs are 1024x1024 grayscale mammograms.
* **Entrypoints**: The root `Makefile` is the primary interface for running the pipeline. Use `run_train.py` at the root as a direct wrapper to `src.models.train_model.main` if you need to test training parameters manually without `make`.
* **Core Code**: Modeling logic lives in `src/models/train_model.py` and `src/models/predict_model.py`. External dataset integration logic lives in `src/data/` (e.g. CVAT, LabelMe, INbreast formats).

## Environment & Dependency Management
* **Python version**: `3.13.5` is strictly required. 
* **Package Manager**: `uv`. 
* **Dependency Updates**: Add packages to `pyproject.toml` (in `dependencies` or `[project.optional-dependencies]`), then update the environment by running `uv pip install -e .` or `uv pip install -e ".[dev]"`. Do not use standard `pip install`.
* **Hardware**: PyTorch targets CUDA. Configuration goes into `.env` (e.g., `DEVICE=cuda`, `BATCH_SIZE=4`).

## Commands & Workflows
* **Complete Pipeline**: `make all` runs preprocessing, feature building, training, predicting, and visualization sequentially.
* **Testing**: Use `make test` to run pytest. 
  * *Tip*: You can run `python tests/generate_dummy_data.py` to create a synthetic dataset for rapid pipeline testing without needing to download the large EMBED dataset.
* **Formatting**: `make format` runs `black`, `isort`, and `ruff check --fix`.
* **Linting**: `make lint` runs `ruff check`. 
  * *Note*: Ignore `tox.ini` (which specifies `flake8` max-line-length 79) for linting; `pyproject.toml`'s ruff configuration (line-length 100) is the actual source of truth.

## Domain Constraints
* **BAC Severity Rules**: BAC (Breast Arterial Calcifications) severity is classified strictly by segmented area (mm²):
  * Zero (0)
  * Mild (0-10)
  * Moderate (10-25)
  * Severe (≥25)
* **Metadata Paths**: Processing medical reports often requires `MAGVIEW_PATH` and `SCORE_PATH` defined in `.env`.
