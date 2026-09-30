.PHONY: help create-env install download-data preprocess-data build-features train predict visualize clean lint format test all

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = bac-segmentation
PYTHON_VERSION = 3.12.8
PYTHON_INTERPRETER = python3

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Display help
help:
	@echo "Commands:"
	@echo "  make create-env       - Create Python virtual environment using uv"
	@echo "  make install          - Install project dependencies with uv"
	@echo "  make install-dev      - Install project + dev dependencies with uv"
	@echo "  make download-data    - Download EMBED dataset (max 1000 images)"
	@echo "  make preprocess-data  - Preprocess DICOM files to PNG"
	@echo "  make build-features   - Create train/val/test splits"
	@echo "  make train            - Train the BAC segmentation model"
	@echo "  make predict          - Run predictions on test set"
	@echo "  make visualize        - Generate visualizations"
	@echo "  make clean            - Remove build artifacts and cache"
	@echo "  make lint             - Check code style with ruff"
	@echo "  make format           - Format code with black and isort"
	@echo "  make test             - Run tests with pytest"
	@echo "  make all              - Run complete pipeline (preprocess → train → predict → visualize)"

## Create virtual environment using uv
create-env:
	@echo ">>> Creating virtual environment with uv (Python $(PYTHON_VERSION))..."
	uv venv --python $(PYTHON_VERSION)
	@echo ">>> Virtual environment created!"
	@echo ">>> Activate with: source .venv/bin/activate (Linux/Mac) or .venv\\Scripts\\activate (Windows)"

## Install dependencies with uv
install:
	@echo ">>> Installing project dependencies with uv..."
	uv pip install -e .
	@echo ">>> Dependencies installed!"

## Install dev dependencies with uv
install-dev:
	@echo ">>> Installing project + dev dependencies with uv..."
	uv pip install -e ".[dev]"
	@echo ">>> Dev dependencies installed!"

## Download EMBED dataset
download-data:
	@echo ">>> Downloading EMBED MLO images..."
	$(PYTHON_INTERPRETER) src/data/make_dataset.py data/raw data/interim --download --max-images 1000

## Preprocess DICOM files
preprocess-data:
	@echo ">>> Preprocessing DICOM files..."
	$(PYTHON_INTERPRETER) src/data/make_dataset.py data/raw data/interim

## Build features and create splits
build-features:
	@echo ">>> Creating train/val/test splits..."
	$(PYTHON_INTERPRETER) src/features/build_features.py data/interim data/processed

## Train model
train:
	@echo ">>> Training BAC segmentation model..."
	$(PYTHON_INTERPRETER) src/models/train_model.py data/processed models/ \
		--epochs 100 \
		--batch-size 4 \
		--lr 1e-4 \
		--device cuda \
		--num-workers 4

## Run predictions
predict:
	@echo ">>> Running predictions on test set..."
	$(PYTHON_INTERPRETER) src/models/predict_model.py \
		models/best_model.pth \
		data/processed/test/images \
		outputs/ \
		--save-masks \
		--metadata-dir data/interim/metadata

## Generate visualizations
visualize:
	@echo ">>> Generating visualizations..."
	$(PYTHON_INTERPRETER) src/visualization/visualize.py \
		--training-history models/training_history.json \
		--predictions outputs/predictions.json \
		--image-dir data/processed/test/images \
		--mask-dir data/processed/test/masks \
		--pred-dir outputs/masks \
		--output-dir reports/figures \
		--num-samples 10

## Lint code
lint:
	@echo ">>> Checking code style with ruff..."
	uv run ruff check src/

## Format code
format:
	@echo ">>> Formatting code with black and isort..."
	uv run black src/
	uv run isort src/
	uv run ruff check --fix src/

## Run tests
test:
	@echo ">>> Running tests with pytest..."
	uv run pytest tests/ -v --cov=src

## Clean build artifacts
clean:
	@echo ">>> Cleaning build artifacts..."
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf .coverage
	@echo ">>> Clean complete!"

## Run complete pipeline
all: preprocess-data build-features train predict visualize
	@echo ">>> Complete pipeline finished!"

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################
