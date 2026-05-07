#!/bin/bash

echo "=================================="
echo "BAC Segmentation - Setup Script"
echo "Python 3.13.5"
echo "=================================="

# Verificar versão do Python
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "🐍 Detected Python version: $PYTHON_VERSION"

if [[ ! "$PYTHON_VERSION" =~ ^3\.13 ]]; then
    echo "⚠️  Warning: This project requires Python 3.13.x"
    echo "   Current version: $PYTHON_VERSION"
    echo "   Recommended: Python 3.13.5"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Verificar se uv está instalado
if ! command -v uv &> /dev/null
then
    echo "❌ uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Adicionar uv ao PATH para sessão atual
    export PATH="$HOME/.cargo/bin:$PATH"

    echo "✅ uv installed successfully!"
else
    UV_VERSION=$(uv --version)
    echo "✅ uv found: $UV_VERSION"
fi

# Criar ambiente virtual
echo ""
echo "📦 Creating virtual environment with Python 3.13.5..."
uv venv --python 3.13.5

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    echo "   Make sure Python 3.13.5 is installed on your system"
    exit 1
fi

# Ativar ambiente
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Verificar versão do Python no venv
VENV_PYTHON_VERSION=$(.venv/bin/python --version 2>&1 | awk '{print $2}')
echo "✅ Virtual environment Python: $VENV_PYTHON_VERSION"

# Instalar dependências
echo ""
echo "📥 Installing dependencies..."
uv pip install -e ".[dev]"

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Criar estrutura de diretórios
echo ""
echo "📁 Creating directory structure..."
mkdir -p data/raw data/interim data/processed
mkdir -p data/interim/metadata
mkdir -p models outputs reports/figures notebooks

# Criar .gitkeep files
touch data/raw/.gitkeep
touch data/interim/.gitkeep
touch data/processed/.gitkeep
touch models/.gitkeep
touch outputs/.gitkeep

# Criar arquivo .env de exemplo
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# AWS Credentials (if needed for private buckets)
# AWS_ACCESS_KEY_ID=your_key_here
# AWS_SECRET_ACCESS_KEY=your_secret_here

# Training Configuration
DEVICE=cuda
BATCH_SIZE=4
NUM_EPOCHS=100
LEARNING_RATE=1e-4

# Data Configuration
IMAGE_SIZE=1024
MAX_DOWNLOAD_IMAGES=1000
EOF
    echo "✅ .env file created (edit as needed)"
fi

# Verificar instalação do PyTorch com CUDA
echo ""
echo "🔍 Checking PyTorch installation..."
python3 -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}')"

echo ""
echo "=================================="
echo "✅ Setup complete!"
echo "=================================="
echo ""
echo "📊 Project Information:"
echo "  Python version: $VENV_PYTHON_VERSION"
echo "  Virtual env: .venv/"
echo "  Package manager: uv"
echo ""
echo "🚀 Next steps:"
echo "  1. Activate environment: source .venv/bin/activate"
echo "  2. View commands: make help"
echo "  3. Download data: make download-data"
echo "  4. Run pipeline: make all"
echo ""
echo "📚 Documentation: README.md"
echo "=================================="
