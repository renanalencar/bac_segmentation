import os
import shutil
import random
from pathlib import Path

def split_dataset(processed_dir, train_ratio=0.8, seed=42):
    random.seed(seed)
    
    proc_path = Path(processed_dir)
    src_images = proc_path / 'images'
    src_masks = proc_path / 'masks'
    
    # Destinos
    train_images = proc_path / 'train' / 'images'
    train_masks = proc_path / 'train' / 'masks'
    val_images = proc_path / 'val' / 'images'
    val_masks = proc_path / 'val' / 'masks'
    
    for p in [train_images, train_masks, val_images, val_masks]:
        p.mkdir(parents=True, exist_ok=True)
        
    all_images = list(src_images.glob('*.png'))
    # Ensure corresponding masks exist
    valid_images = [img for img in all_images if (src_masks / img.name).exists()]
    
    valid_images.sort()
    random.shuffle(valid_images)
    
    split_idx = int(len(valid_images) * train_ratio)
    train_list = valid_images[:split_idx]
    val_list = valid_images[split_idx:]
    
    for img_path in train_list:
        shutil.move(str(img_path), str(train_images / img_path.name))
        shutil.move(str(src_masks / img_path.name), str(train_masks / img_path.name))
        
    for img_path in val_list:
        shutil.move(str(img_path), str(val_images / img_path.name))
        shutil.move(str(src_masks / img_path.name), str(val_masks / img_path.name))
        
    print(f"Total de imagens: {len(valid_images)}")
    print(f"Treino: {len(train_list)} imagens")
    print(f"Validação: {len(val_list)} imagens")
    
if __name__ == '__main__':
    split_dataset('data/processed')
