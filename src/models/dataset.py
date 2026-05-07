"""
Dataset PyTorch para treinamento
"""
import numpy as np
import torch
from torch.utils.data import Dataset
from PIL import Image
from pathlib import Path
import albumentations as A
from albumentations.pytorch import ToTensorV2


class BACDataset(Dataset):
    """Dataset PyTorch para segmentação de BAC"""
    def __init__(self, image_dir, mask_dir, transform=None, mode='train'):
        """
        Args:
            image_dir: Diretório com imagens preprocessadas
            mask_dir: Diretório com máscaras anotadas
            transform: Transformações Albumentations
            mode: 'train', 'val', ou 'test'
        """
        self.image_dir = Path(image_dir)
        self.mask_dir = Path(mask_dir)
        self.transform = transform
        self.mode = mode
        
        # Listar imagens que têm máscaras correspondentes
        self.image_files = []
        for img_path in sorted(self.image_dir.glob("*.png")):
            mask_path = self.mask_dir / f"{img_path.stem}_mask.png"
            if mask_path.exists():
                self.image_files.append(img_path)
        
        print(f"[{mode.upper()}] Found {len(self.image_files)} image-mask pairs")
    
    def __len__(self):
        return len(self.image_files)
    
    def __getitem__(self, idx):
        img_path = self.image_files[idx]
        mask_path = self.mask_dir / f"{img_path.stem}_mask.png"
        
        # Carregar imagem e máscara
        image = np.array(Image.open(img_path).convert('L'))
        mask = np.array(Image.open(mask_path).convert('L'))
        
        # Normalizar
        image = image.astype(np.float32) / 255.0
        mask = (mask > 127).astype(np.float32)
        
        # Aplicar transformações
        if self.transform:
            augmented = self.transform(image=image, mask=mask)
            image = augmented['image']
            mask = augmented['mask']
        else:
            image = torch.from_numpy(image).unsqueeze(0)
            mask = torch.from_numpy(mask).unsqueeze(0)
        
        return {
            'image': image,
            'mask': mask,
            'filename': img_path.name
        }


def get_train_transforms():
    """Data augmentation para treino"""
    return A.Compose([
        A.HorizontalFlip(p=0.5),
        A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.1, rotate_limit=15, p=0.5),
        A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
        A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
        ToTensorV2()
    ])


def get_val_transforms():
    """Transformações para validação/teste"""
    return A.Compose([
        ToTensorV2()
    ])