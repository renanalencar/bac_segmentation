# run_train.py - Helper para executar treinamento
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Importar e executar
from src.models.train_model import main

if __name__ == '__main__':
    main()