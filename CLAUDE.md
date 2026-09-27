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

<!-- rtk-instructions v2 -->
# RTK (Rust Token Killer) - Token-Optimized Commands

## Golden Rule

**Always prefix commands with `rtk`**. If RTK has a dedicated filter, it uses it. If not, it passes through unchanged. This means RTK is always safe to use.

**Important**: Even in command chains with `&&`, use `rtk`:
```bash
# ❌ Wrong
git add . && git commit -m "msg" && git push

# ✅ Correct
rtk git add . && rtk git commit -m "msg" && rtk git push
```

## RTK Commands by Workflow

### Build & Compile (80-90% savings)
```bash
rtk cargo build         # Cargo build output
rtk cargo check         # Cargo check output
rtk cargo clippy        # Clippy warnings grouped by file (80%)
rtk tsc                 # TypeScript errors grouped by file/code (83%)
rtk lint                # ESLint/Biome violations grouped (84%)
rtk prettier --check    # Files needing format only (70%)
rtk next build          # Next.js build with route metrics (87%)
```

### Test (60-99% savings)
```bash
rtk cargo test          # Cargo test failures only (90%)
rtk go test             # Go test failures only (90%)
rtk jest                # Jest failures only (99.5%)
rtk vitest              # Vitest failures only (99.5%)
rtk playwright test     # Playwright failures only (94%)
rtk pytest              # Python test failures only (90%)
rtk rake test           # Ruby test failures only (90%)
rtk rspec               # RSpec test failures only (60%)
rtk test <cmd>          # Generic test wrapper - failures only
```

### Git (59-80% savings)
```bash
rtk git status          # Compact status
rtk git log             # Compact log (works with all git flags)
rtk git diff            # Compact diff (80%)
rtk git show            # Compact show (80%)
rtk git add             # Ultra-compact confirmations (59%)
rtk git commit          # Ultra-compact confirmations (59%)
rtk git push            # Ultra-compact confirmations
rtk git pull            # Ultra-compact confirmations
rtk git branch          # Compact branch list
rtk git fetch           # Compact fetch
rtk git stash           # Compact stash
rtk git worktree        # Compact worktree
```

Note: Git passthrough works for ALL subcommands, even those not explicitly listed.

### GitHub (26-87% savings)
```bash
rtk gh pr view <num>    # Compact PR view (87%)
rtk gh pr checks        # Compact PR checks (79%)
rtk gh run list         # Compact workflow runs (82%)
rtk gh issue list       # Compact issue list (80%)
rtk gh api              # Compact API responses (26%)
```

### JavaScript/TypeScript Tooling (70-90% savings)
```bash
rtk pnpm list           # Compact dependency tree (70%)
rtk pnpm outdated       # Compact outdated packages (80%)
rtk pnpm install        # Compact install output (90%)
rtk npm run <script>    # Compact npm script output
rtk npx <cmd>           # Compact npx command output
rtk prisma              # Prisma without ASCII art (88%)
rtk uv run <cmd>        # Compact uv project command output
```

### Files & Search (60-75% savings)
```bash
rtk ls <path>           # Tree format, compact (65%)
rtk read <file>         # Code reading with filtering (60%)
rtk grep <pattern>      # Search grouped by file (75%). Format flags (-c, -l, -L, -o, -Z) run raw.
rtk find <pattern>      # Find grouped by directory (70%)
```

### Analysis & Debug (70-90% savings)
```bash
rtk err <cmd>           # Filter errors only from any command
rtk log <file>          # Deduplicated logs with counts
rtk json <file>         # JSON structure without values
rtk deps                # Dependency overview
rtk env                 # Environment variables compact
rtk summary <cmd>       # Smart summary of command output
rtk diff                # Ultra-compact diffs
```

### Infrastructure (85% savings)
```bash
rtk docker ps           # Compact container list
rtk docker images       # Compact image list
rtk docker logs <c>     # Deduplicated logs
rtk kubectl get         # Compact resource list
rtk kubectl logs        # Deduplicated pod logs
```

### Network (65-70% savings)
```bash
rtk curl <url>          # Compact HTTP responses (70%)
rtk wget <url>          # Compact download output (65%)
```

### Meta Commands
```bash
rtk gain                # View token savings statistics
rtk gain --history      # View command history with savings
rtk discover            # Analyze Claude Code sessions for missed RTK usage
rtk proxy <cmd>         # Run command without filtering (for debugging)
rtk init                # Add RTK instructions to CLAUDE.md
rtk init --global       # Add RTK to ~/.claude/CLAUDE.md
```

## Token Savings Overview

| Category | Commands | Typical Savings |
|----------|----------|-----------------|
| Tests | vitest, playwright, cargo test | 90-99% |
| Build | next, tsc, lint, prettier | 70-87% |
| Git | status, log, diff, add, commit | 59-80% |
| GitHub | gh pr, gh run, gh issue | 26-87% |
| Package Managers | pnpm, npm, npx | 70-90% |
| Files | ls, read, grep, find | 60-75% |
| Infrastructure | docker, kubectl | 85% |
| Network | curl, wget | 65-70% |

Overall average: **60-90% token reduction** on common development operations.
<!-- /rtk-instructions -->
