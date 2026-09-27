# Agent Instructions for BAC Segmentation

## Architecture
* **Data Flow**: `data/raw` (DICOM) -> `data/interim` -> `data/processed` (PNG splits).
* **Model**: Mix Vision Transformer (PVT) + MLP Decoder. Inputs are 1024x1024 grayscale mammograms.
* **Entrypoints**: Root `Makefile` is the primary interface. `run_train.py` at the root wraps `src.models.train_model.main` for manual training testing.
* **Core Code**: `src/models/train_model.py` and `src/models/predict_model.py`. Dataset integration (CVAT, LabelMe, INbreast) lives in `src/data/`.
* **src packages**: `src.data`, `src.features`, `src.models`, `src.visualization`.

## Environment
* **Python**: `3.13.5` (specified in Makefile `PYTHON_VERSION`).
* **Package Manager**: `uv` only. Never `pip install`.
* **Dependencies**: Edit `pyproject.toml`, then `uv pip install -e .` or `uv pip install -e ".[dev]"`.
* **`.env`**: Contains `MAGVIEW_PATH`, `SCORE_PATH`, `OUTPUT_PATH` (all default to `/path/to/...`). Set real paths before processing medical reports.

## Commands
* **Full pipeline**: `make all` (preprocess -> build-features -> train -> predict -> visualize).
* **Individual steps**: `make preprocess-data`, `make build-features`, `make train`, `make predict`, `make visualize`.
* **Training with custom params**: `python src/models/train_model.py data/processed models/ --epochs 150 --batch-size 8 --lr 5e-5 --device cuda --num-workers 8`.
* **Resume training**: Add `--resume models/checkpoint_epoch_N.pth`.
* **Tests**: `make test` (pytest + coverage). Run `python tests/generate_dummy_data.py` for synthetic data instead of downloading the EMBED dataset.
* **Format**: `make format` (black + isort + ruff --fix).
* **Lint**: `make lint` (ruff).
* **Clean**: `make clean`.

## Linting Notes
* **Ruff** (line-length 100, from `pyproject.toml`) is the source of truth. Ignore `tox.ini`'s flake8 line-length 79 setting — it conflicts and is not used.
* All formatters/linters target `src/` only (via Makefile).

## Domain Constraints
* **BAC Severity** (by segmented area in mm²): Zero (0), Mild (0-10), Moderate (10-25), Severe (>=25).
* **`embed-toolkit`** is a domain-specific dependency (`embed-toolkit>=0.2.14`) used for EMBED dataset handling.
