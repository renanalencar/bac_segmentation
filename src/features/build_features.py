# -*- coding: utf-8 -*-
"""
Script para criar splits de treino/validação/teste
e aplicar data augmentation
"""
import click
import logging
from pathlib import Path
import numpy as np
import json
import shutil
from sklearn.model_selection import train_test_split


@click.command()
@click.argument('input_filepath', type=click.Path(exists=True))
@click.argument('output_filepath', type=click.Path())
@click.option('--train-split', default=0.9, help='Train split ratio')
@click.option('--val-split', default=0.05, help='Validation split ratio')
@click.option('--test-split', default=0.05, help='Test split ratio')
@click.option('--seed', default=42, help='Random seed')
def main(input_filepath, output_filepath, train_split, val_split, test_split, seed):
    """
    Cria splits de dados e organiza dataset final
    
    Assumes:
        - input_filepath/images/*.png (preprocessed images)
        - input_filepath/masks/*.png (annotated masks)
    
    Creates:
        - output_filepath/train/{images, masks}
        - output_filepath/val/{images, masks}
        - output_filepath/test/{images, masks}
        
    Examples:
        python build_features.py data/interim data/processed
    """
    logger = logging.getLogger(__name__)
    logger.info('Building features and creating dataset splits')
    
    input_path = Path(input_filepath)
    output_path = Path(output_filepath)
    
    # Verificar diretórios
    images_dir = input_path / "images"
    masks_dir = input_path / "masks"
    
    if not images_dir.exists():
        logger.error(f"Images directory not found: {images_dir}")
        return
    
    if not masks_dir.exists():
        logger.error(f"Masks directory not found: {masks_dir}")
        return
    
    # Encontrar pares imagem-máscara
    image_files = sorted(list(images_dir.glob("*.png")))
    pairs = []
    
    for img_path in image_files:
        mask_path = masks_dir / f"{img_path.stem}_mask.png"
        if mask_path.exists():
            pairs.append((img_path, mask_path))
    
    logger.info(f"Found {len(pairs)} image-mask pairs")
    
    if len(pairs) == 0:
        logger.error("No valid image-mask pairs found!")
        return
    
    # Verificar que splits somam 1.0
    assert abs(train_split + val_split + test_split - 1.0) < 1e-6, \
        "Train/val/test splits must sum to 1.0"
    
    # Split em train/temp
    train_pairs, temp_pairs = train_test_split(
        pairs, 
        train_size=train_split, 
        random_state=seed
    )
    
    # Split temp em val/test
    val_ratio = val_split / (val_split + test_split)
    val_pairs, test_pairs = train_test_split(
        temp_pairs,
        train_size=val_ratio,
        random_state=seed
    )
    
    logger.info(f"Split sizes - Train: {len(train_pairs)}, Val: {len(val_pairs)}, Test: {len(test_pairs)}")
    
    # Criar estrutura de diretórios
    for split_name in ['train', 'val', 'test']:
        (output_path / split_name / 'images').mkdir(parents=True, exist_ok=True)
        (output_path / split_name / 'masks').mkdir(parents=True, exist_ok=True)
    
    # Copiar arquivos para splits
    def copy_pairs(pairs, split_name):
        for img_path, mask_path in pairs:
            # Copiar imagem
            shutil.copy(
                img_path,
                output_path / split_name / 'images' / img_path.name
            )
            # Copiar máscara
            shutil.copy(
                mask_path,
                output_path / split_name / 'masks' / mask_path.name
            )
    
    logger.info("Copying files to splits...")
    copy_pairs(train_pairs, 'train')
    copy_pairs(val_pairs, 'val')
    copy_pairs(test_pairs, 'test')
    
    # Salvar informações do split
    split_info = {
        'total_pairs': len(pairs),
        'train': len(train_pairs),
        'val': len(val_pairs),
        'test': len(test_pairs),
        'seed': seed,
        'train_split': train_split,
        'val_split': val_split,
        'test_split': test_split
    }
    
    with open(output_path / 'split_info.json', 'w') as f:
        json.dump(split_info, f, indent=2)
    
    logger.info(f"Dataset splits created successfully at {output_path}")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    main()