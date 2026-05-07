# BAC Segmentation

Artificial intelligence-based quantification of breast arterial calcifications to predict cardiovascular morbidity and mortality.

## Project Organization

    ├── LICENSE
    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    ├── README.md          <- The top-level README for developers using this project.
    ├── pyproject.toml <- Project configuration and dependencies (managed by uv)
    ├── .python-version <- Python version (3.13.5)
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    │
    ├── docs               <- A default Sphinx project; see sphinx-doc.org for details
    │
    ├── models             <- Trained and serialized models, model predictions, or model summaries
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── outputs <- Predictions and results
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
    └── src <- Source code for this project
    ├── _init_.py <- Makes src a Python module
    ├── data <- Scripts to download or generate data
    │ └── make_dataset.py
    │
    ├── features <- Scripts to turn raw data into features for modeling
    │ └── build_features.py
    │
    ├── models <- Scripts to train models and then use trained models to make predictions
    │ ├── architecture.py
    │ ├── dataset.py
    │ ├── train_model.py
    │ └── predict_model.py
    │
    └── visualization <- Scripts to create exploratory and results oriented visualizations
    └── visualize.py
    └── tox.ini            <- tox file with settings for running tox; see tox.readthedocs.io

## Requirements

### System Requirements

- **Python**: 3.13.5
- **Package Manager**: [uv](https://github.com/astral-sh/uv)
- **GPU**: CUDA-capable GPU (recommended for training)
- **RAM**: 16GB+ recommended
- **Storage**: 50GB+ for EMBED dataset

### Installation

1. **Install Python 3.13.5**

If you don't have Python 3.13.5:

**Ubuntu/Debian:**
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.13 python3.13-venv python3.13-dev
```

**macOS (with Homebrew):**
```bash
brew install python@3.13
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/)

2. **Install uv**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. **Clone repository**
```bash
git clone <your-repo-url>
cd bac-segmentation
```

4. **Run setup script**
```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Create virtual environment with Python 3.13.5
- Install all dependencies via uv
- Create project directory structure
- Verify PyTorch CUDA installation

5. **Activate environment**
```bash
source .venv/bin/activate
```

## Quick Start

### Complete Pipeline

Run the entire pipeline with one command:

```bash
make all
```

This will:
1. Preprocess DICOM files
2. Create train/val/test splits
3. Train the model (100 epochs)
4. Run predictions on test set
5. Generate visualizations

### Step-by-Step Workflow

1. **Download EMBED dataset** (optional)
```bash
make download-data
```

2. **Preprocess DICOM files**
```bash
make preprocess-data
```

3. **Create dataset splits**
```bash
make build-features
```

4. **Train model**
```bash
make train
```

Training parameters can be customized:
```bash
python src/models/train_model.py data/processed models/ \
    --epochs 150 \
    --batch-size 8 \
    --lr 5e-5 \
    --device cuda \
    --num-workers 8
```

5. **Run predictions**
```bash
make predict
```

6. **Generate visualizations**
```bash
make visualize
```

## Usage Examples

### Training with Custom Parameters

```bash
python src/models/train_model.py \
    data/processed \
    models/ \
    --epochs 200 \
    --batch-size 4 \
    --lr 1e-4 \
    --device cuda \
    --num-workers 4 \
    --seed 42
```

### Resume Training from Checkpoint

```bash
python src/models/train_model.py \
    data/processed \
    models/ \
    --resume models/checkpoint_epoch_50.pth \
    --epochs 100
```

### Batch Prediction

```bash
python src/models/predict_model.py \
    models/best_model.pth \
    data/processed/test/images \
    outputs/ \
    --save-masks \
    --threshold 0.5 \
    --metadata-dir data/interim/metadata
```

## Development

### Code Quality

**Format code:**
```bash
make format
```

**Lint code:**
```bash
make lint
```

**Run tests:**
```bash
make test
```

### Adding Dependencies

Edit `pyproject.toml` and add to `dependencies`:
```toml
dependencies = [
    # ... existing dependencies
    "new-package>=1.0.0",
]
```

Then reinstall:
```bash
uv pip install -e .
```

## Model Architecture

**Mix Vision Transformer** (PVT-based) with MLP decoder

**Configuration:**
- Embed dimensions: [64, 128, 320, 512]
- Attention heads: [1, 2, 5, 8]
- Depths: [3, 4, 6, 3]
- Spatial reduction ratios: [8, 4, 2, 1]

**Input:** 1024×1024 grayscale mammogram  
**Output:** Binary segmentation mask → BAC area in mm²

## BAC Severity Classification

| Severity | BAC Area (mm²) |
|----------|----------------|
| Zero     | 0              |
| Mild     | 0-10           |
| Moderate | 10-25          |
| Severe   | ≥25            |

## Project Commands Reference

```bash
make help              # Show all available commands
make create-env        # Create Python 3.13.5 virtual environment
make install           # Install dependencies
make install-dev       # Install with dev dependencies
make download-data     # Download EMBED dataset
make preprocess-data   # Preprocess DICOMs to PNG
make build-features    # Create train/val/test splits
make train             # Train model
make predict           # Run predictions
make visualize         # Generate plots
make clean             # Remove artifacts
make lint              # Check code quality
make format            # Format code
make test              # Run tests
make all               # Complete pipeline
```

## Troubleshooting

### CUDA Not Available

If `torch.cuda.is_available()` returns `False`:

1. Check NVIDIA driver:
```bash
nvidia-smi
```

2. Reinstall PyTorch with CUDA:
```bash
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### Memory Issues

Reduce batch size in training:
```bash
python src/models/train_model.py data/processed models/ --batch-size 2
```

## Citation

Based on:
- **Paper**: "Artificial intelligence-based quantification of breast arterial calcifications to predict cardiovascular morbidity and mortality" (2024)

## License

MIT License

## Author

Renan Costa Alencar

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
