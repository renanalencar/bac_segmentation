# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

### Environment Setup
```bash
make create-env          # Create Python 3.13.5 venv using uv
make install-dev         # Install all dependencies + dev tools
```

### Run the Full Pipeline
```bash
make all                 # Runs: preprocess → build-features → train → predict → visualize
```

### Common Development Tasks
```bash
make lint                # Check code style (ruff)
make format              # Format code (black + isort + ruff --fix)
make test                # Run all tests with coverage
make clean               # Remove build artifacts
```

## Architecture Overview

### Data Pipeline
**Raw Data Flow**: `data/raw/` (DICOM) → `data/interim/` (PNG, normalized) → `data/processed/` (train/val/test splits with PNG + mask pairs)

**Key Components**:
- `src/data/make_dataset.py`: Downloads EMBED dataset, converts DICOM to PNG, extracts metadata
- `src/features/build_features.py`: Creates train/val/test splits (80/10/10), applies data augmentation
- `src/models/dataset.py`: PyTorch Dataset class that loads image-mask pairs with augmentation

### Model Architecture
**Mix Vision Transformer (PVT)** + **MLP Decoder**
- **Input**: 1024×1024 grayscale mammogram
- **Output**: Binary segmentation mask → BAC area in mm²
- **Config** (from `src/models/architecture.py`):
  - Embed dims: [64, 128, 320, 512]
  - Attention heads: [1, 2, 5, 8]
  - Depths: [3, 4, 6, 3]
  - Spatial reduction ratios: [8, 4, 2, 1]

### Code Organization
| Module | Purpose | Key Files |
|--------|---------|-----------|
| `src/data/` | Dataset prep, format conversion (CVAT, LabelMe, INbreast) | `make_dataset.py`, `cvat_export_to_masks.py`, `labelme_to_masks.py` |
| `src/features/` | Feature engineering, train/val/test splits | `build_features.py` |
| `src/models/` | Model training & prediction | `train_model.py`, `predict_model.py`, `architecture.py`, `dataset.py` |
| `src/visualization/` | Results plotting and analysis | `visualize.py` |

### Entrypoints
- **Pipeline control**: `Makefile` (primary interface)
- **Manual training**: `run_train.py` (wraps `src.models.train_model.main` for parameter testing)
- **Training script**: `src/models/train_model.py --help` (see all training options)
- **Prediction script**: `src/models/predict_model.py --help` (batch inference)

## Environment & Dependency Management

### Python & Package Manager
- **Python**: `3.13.5` (required, specified in Makefile)
- **Package Manager**: `uv` only — never use standard `pip install`

### Adding/Updating Dependencies
1. Edit `pyproject.toml`:
   - Add to `dependencies` for core packages
   - Add to `[project.optional-dependencies] dev` for dev tools
2. Update environment:
   ```bash
   uv pip install -e .           # Core dependencies
   uv pip install -e ".[dev]"    # + dev dependencies
   ```

### Hardware & Configuration
- **GPU**: PyTorch targets CUDA. Verify with `nvidia-smi`
- **Environment variables** (`.env`):
  ```
  MAGVIEW_PATH=/path/to/magview    # (optional) DICOM viewer path
  SCORE_PATH=/path/to/score        # (optional) Medical report scores
  OUTPUT_PATH=/path/to/output      # (optional) Output directory
  DEVICE=cuda                      # or 'cpu' for CPU training
  BATCH_SIZE=4                     # Adjust based on GPU memory
  ```

## Commands & Workflows

### Complete Pipeline
```bash
make all
# Equivalent to:
make preprocess-data && make build-features && make train && make predict && make visualize
```

### Step-by-Step Workflow

#### 1. Prepare Data
```bash
# Download EMBED dataset (up to 1000 images)
make download-data

# Or preprocess existing DICOM files in data/raw/
make preprocess-data

# Create train/val/test splits
make build-features
```

#### 2. Train Model
```bash
# Train with default parameters
make train

# Train with custom parameters (100 epochs, batch-size 8, learning rate 5e-5)
python src/models/train_model.py data/processed models/ \
  --epochs 100 \
  --batch-size 8 \
  --lr 5e-5 \
  --device cuda \
  --num-workers 8 \
  --seed 42

# Resume training from checkpoint
python src/models/train_model.py data/processed models/ \
  --resume models/checkpoint_epoch_50.pth \
  --epochs 150
```

#### 3. Run Predictions
```bash
# Batch prediction on test set
make predict

# Custom prediction command
python src/models/predict_model.py \
  models/best_model.pth \
  data/processed/test/images \
  outputs/ \
  --save-masks \
  --threshold 0.5 \
  --metadata-dir data/interim/metadata
```

#### 4. Visualize Results
```bash
make visualize
```

### Testing

#### Run All Tests
```bash
make test           # Runs pytest with coverage reporting
```

#### Run Specific Test File
```bash
uv run pytest tests/test_specific_module.py -v
```

#### Run Specific Test Function
```bash
uv run pytest tests/test_module.py::TestClass::test_function -v
```

#### Generate Synthetic Data for Testing
Instead of downloading the large EMBED dataset, create dummy data for rapid testing:
```bash
python tests/generate_dummy_data.py
# Creates test fixtures in data/processed/
```

#### Run Tests with Coverage Report
```bash
uv run pytest tests/ -v --cov=src --cov-report=html
# Open htmlcov/index.html for detailed coverage
```

### Code Quality

#### Format Code
```bash
make format    # black + isort + ruff --fix (targets src/ only)
```

#### Lint Code
```bash
make lint      # ruff check (targets src/ only)
```

**Important**: 
- Ruff uses `pyproject.toml` config (line-length=100, Python 3.12+)
- Ignore `tox.ini` flake8 settings (line-length=79) — they conflict and are not enforced

#### Manual Code Formatting
```bash
uv run black src/                 # Format with black
uv run isort src/                 # Sort imports
uv run ruff check --fix src/      # Fix ruff violations
```

### Cleaning Up
```bash
make clean    # Remove __pycache__, .pytest_cache, build/, dist/, .coverage
```

## Domain Knowledge

### BAC Severity Classification
BAC (Breast Arterial Calcifications) severity is determined by segmented area (mm²):

| Severity | BAC Area (mm²) |
|----------|----------------|
| Zero     | 0              |
| Mild     | 0–10           |
| Moderate | 10–25          |
| Severe   | ≥25            |

### Key Dataset
- **EMBED (Emory Breast Imaging Dataset)**: Multi-view mammography dataset with DICOM files
- **Supported formats**: DICOM (via pydicom), PNG (via PIL/OpenCV)
- **Annotation tools supported**: CVAT, LabelMe, INbreast format

### Visualization Outputs
- `reports/figures/`: Training history plots, prediction overlays, BAC severity distributions
- `outputs/predictions.json`: Prediction metadata and computed BAC areas
- `outputs/masks/`: Predicted segmentation masks (PNG)

## Development Workflow Tips

### Debugging Training
```bash
# Monitor training with tensorboard
tensorboard --logdir models/tensorboard_logs

# Run quick smoke test with 1 epoch
python src/models/train_model.py data/processed models/ --epochs 1
```

### Debugging Memory Issues
```bash
# Reduce batch size for GPU with limited VRAM
python src/models/train_model.py data/processed models/ --batch-size 2 --num-workers 2

# Use CPU instead
python src/models/train_model.py data/processed models/ --device cpu
```

### Working with Different Datasets
Conversion scripts in `src/data/`:
- **CVAT annotations** → masks: `cvat_export_to_masks.py`
- **LabelMe annotations** → masks: `labelme_to_masks.py`
- **INbreast data** → annotation-ready: `prepare_inbreast_for_annotation.py`

### Testing Model on Custom Images
```bash
# Place custom mammograms (PNG/DICOM) in a directory
python src/models/predict_model.py \
  models/best_model.pth \
  /path/to/custom/images \
  /path/to/output
```

## File Locations & Conventions

| Purpose | Location |
|---------|----------|
| Model checkpoints | `models/best_model.pth`, `models/checkpoint_epoch_*.pth` |
| Training logs | `models/training_history.json`, `models/tensorboard_logs/` |
| Training data | `data/processed/{train,val,test}/{images,masks}/` |
| Predictions | `outputs/predictions.json`, `outputs/masks/` |
| Visualizations | `reports/figures/` |
| Notebooks | `notebooks/` (e.g., `1.0-initials-exploration.ipynb`) |
| Configuration | `.env` (local), `.env_example` (template) |

## Important Notes

1. **Line length**: Use Ruff's 100-char limit (from `pyproject.toml`), not tox.ini's 79-char limit
2. **Package manager**: Always use `uv`, never mix with standard `pip`
3. **Python version**: Strictly 3.13.5 (checked in Makefile)
4. **GPU training**: Requires CUDA-capable GPU; CPU fallback available but slow
5. **Data versioning**: Raw DICOM files are immutable; processed data can be regenerated via pipeline
6. **Testing strategy**: Use synthetic data (`tests/generate_dummy_data.py`) for CI/rapid iteration; full dataset for validation
