# setup.ps1 - BAC Segmentation Setup Script para Windows

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "BAC Segmentation - Setup Script" -ForegroundColor Cyan
Write-Host "Python 3.13.5" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Verificar versão do Python
try {
    $pythonVersion = (python --version 2>&1) -replace "Python ", ""
    Write-Host "🐍 Detected Python version: $pythonVersion" -ForegroundColor Green
    
    if (-not ($pythonVersion -match "^3\.13")) {
        Write-Host "⚠️  Warning: This project requires Python 3.13.x" -ForegroundColor Yellow
        Write-Host "   Current version: $pythonVersion" -ForegroundColor Yellow
        Write-Host "   Recommended: Python 3.13.5" -ForegroundColor Yellow
        
        $continue = Read-Host "Continue anyway? (y/n)"
        if ($continue -ne "y") {
            exit 1
        }
    }
} catch {
    Write-Host "❌ Python not found. Please install Python 3.13.5" -ForegroundColor Red
    Write-Host "   Download from: https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# Verificar se uv está instalado
Write-Host ""
try {
    $uvVersion = (uv --version 2>&1)
    Write-Host "✅ uv found: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ uv not found. Installing uv..." -ForegroundColor Yellow
    
    # Instalar uv no Windows
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    
    # Atualizar PATH para sessão atual
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Host "✅ uv installed successfully!" -ForegroundColor Green
}

# Criar ambiente virtual
Write-Host ""
Write-Host "📦 Creating virtual environment with Python 3.13.5..." -ForegroundColor Cyan
uv venv --python 3.13.5

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
    Write-Host "   Make sure Python 3.13.5 is installed on your system" -ForegroundColor Red
    exit 1
}

# Ativar ambiente
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Cyan
& ".\.venv\Scripts\Activate.ps1"

# Verificar versão do Python no venv
$venvPythonVersion = (.\.venv\Scripts\python --version 2>&1) -replace "Python ", ""
Write-Host "✅ Virtual environment Python: $venvPythonVersion" -ForegroundColor Green

# Criar estrutura de código fonte
Write-Host ""
Write-Host "📁 Creating source code structure..." -ForegroundColor Cyan

$srcDirectories = @(
    "src",
    "src\data",
    "src\features",
    "src\models",
    "src\visualization"
)

foreach ($dir in $srcDirectories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Criar __init__.py files
$initFiles = @(
    "src\__init__.py",
    "src\data\__init__.py",
    "src\features\__init__.py",
    "src\models\__init__.py",
    "src\visualization\__init__.py"
)

foreach ($file in $initFiles) {
    if (-not (Test-Path $file)) {
        New-Item -ItemType File -Path $file -Force | Out-Null
    }
}

# Instalar dependências
Write-Host ""
Write-Host "📥 Installing dependencies..." -ForegroundColor Cyan
uv pip install -e ".[dev]"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Criar estrutura de diretórios de dados
Write-Host ""
Write-Host "📁 Creating data directory structure..." -ForegroundColor Cyan

$dataDirectories = @(
    "data\raw",
    "data\interim",
    "data\interim\metadata",
    "data\processed",
    "models",
    "outputs",
    "reports\figures",
    "notebooks"
)

foreach ($dir in $dataDirectories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Criar .gitkeep files
$gitkeepFiles = @(
    "data\raw\.gitkeep",
    "data\interim\.gitkeep",
    "data\processed\.gitkeep",
    "models\.gitkeep",
    "outputs\.gitkeep"
)

foreach ($file in $gitkeepFiles) {
    if (-not (Test-Path $file)) {
        New-Item -ItemType File -Path $file -Force | Out-Null
    }
}

# Criar arquivo .env de exemplo
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file..." -ForegroundColor Cyan
    
    $envContent = @"
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
"@
    
    Set-Content -Path ".env" -Value $envContent
    Write-Host "✅ .env file created (edit as needed)" -ForegroundColor Green
}

# Verificar instalação do PyTorch com CUDA
Write-Host ""
Write-Host "🔍 Checking PyTorch installation..." -ForegroundColor Cyan

$torchCheck = python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())" 2>&1
$torchVersion = $torchCheck[0]
$cudaAvailable = $torchCheck[1]

Write-Host "  PyTorch version: $torchVersion" -ForegroundColor White
Write-Host "  CUDA available: $cudaAvailable" -ForegroundColor White

if ($cudaAvailable -eq "False") {
    Write-Host ""
    Write-Host "⚠️  PyTorch CPU-only detected!" -ForegroundColor Yellow
    Write-Host "   For GPU training, reinstall PyTorch with CUDA:" -ForegroundColor Yellow
    Write-Host "   uv pip uninstall torch torchvision" -ForegroundColor White
    Write-Host "   uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121" -ForegroundColor White
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Project Information:" -ForegroundColor Yellow
Write-Host "  Python version: $venvPythonVersion" -ForegroundColor White
Write-Host "  Virtual env: .venv\" -ForegroundColor White
Write-Host "  Package manager: uv" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Activate environment: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  2. (Optional) Install CUDA PyTorch: See warning above" -ForegroundColor White
Write-Host "  3. Download data: python src/data/make_dataset.py data/raw data/interim --download" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation: README.md" -ForegroundColor Yellow
Write-Host "==================================" -ForegroundColor Cyan