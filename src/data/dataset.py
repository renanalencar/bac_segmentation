"""
Scripts para download e carregamento de dados
"""

from pathlib import Path

import albumentations as A
import boto3
import cv2
import numpy as np
import pydicom
import torch
from albumentations.pytorch import ToTensorV2
from PIL import Image
from torch.utils.data import Dataset

from .config import (
    EMBED_BUCKET,
    EMBED_REGION,
    IMAGE_SIZE,
    INTERIM_DATA_DIR,
    RAW_DATA_DIR,
)


def download_embed_mlo_images(max_images=1000):
    """
    Baixar mamografias MLO do EMBED dataset

    Args:
        max_images: Número máximo de imagens para baixar
    """
    s3 = boto3.client("s3", region_name=EMBED_REGION)
    paginator = s3.get_paginator("list_objects_v2")

    count = 0
    print(f"Downloading EMBED MLO images to {RAW_DATA_DIR}")

    for page in paginator.paginate(Bucket=EMBED_BUCKET):
        if count >= max_images:
            break

        for obj in page.get("Contents", []):
            if count >= max_images:
                break

            key = obj["Key"]
            # Filtrar apenas DICOMs MLO
            if ".dcm" in key.lower() and "mlo" in key.lower():
                local_path = RAW_DATA_DIR / Path(key).name

                if not local_path.exists():
                    try:
                        s3.download_file(EMBED_BUCKET, key, str(local_path))
                        count += 1
                        print(f"Downloaded {count}/{max_images}: {key}")
                    except Exception as e:
                        print(f"Error downloading {key}: {e}")

    print(f"Download complete! Total images: {count}")


def preprocess_dicom(dicom_path, target_size=IMAGE_SIZE):
    """
    Pré-processar DICOM para formato normalizado

    Args:
        dicom_path: Caminho para arquivo DICOM
        target_size: Tamanho alvo da imagem

    Returns:
        img_padded: Imagem preprocessada
        metadata: Metadata do DICOM (pixel spacing, etc)
    """
    dcm = pydicom.dcmread(dicom_path)
    img = dcm.pixel_array.astype(np.float32)

    # Normalizar intensidade
    img = (img - img.min()) / (img.max() - img.min() + 1e-8)

    # Resize mantendo aspect ratio
    h, w = img.shape
    scale = target_size / max(h, w)
    new_h, new_w = int(h * scale), int(w * scale)
    img_resized = cv2.resize(img, (new_w, new_h))

    # Padding central
    img_padded = np.zeros((target_size, target_size), dtype=np.float32)
    pad_h = (target_size - new_h) // 2
    pad_w = (target_size - new_w) // 2
    img_padded[pad_h : pad_h + new_h, pad_w : pad_w + new_w] = img_resized

    # Metadata
    pixel_spacing = dcm.get("PixelSpacing", [1.0, 1.0])
    metadata = {
        "pixel_spacing": pixel_spacing,
        "padding": (pad_h, pad_w),
        "scale": scale,
        "original_shape": (h, w),
    }

    return img_padded, metadata


def preprocess_all_dicoms():
    """
    Pré-processar todos os DICOMs em data/raw
    Salva em data/interim como PNG
    """
    print(f"Preprocessing DICOMs from {RAW_DATA_DIR}")

    dicom_files = list(RAW_DATA_DIR.glob("*.dcm"))
    print(f"Found {len(dicom_files)} DICOM files")

    for idx, dcm_path in enumerate(dicom_files):
        try:
            img, metadata = preprocess_dicom(dcm_path)

            # Salvar imagem como PNG (0-255)
            img_uint8 = (img * 255).astype(np.uint8)
            output_path = INTERIM_DATA_DIR / f"{dcm_path.stem}.png"
            Image.fromarray(img_uint8).save(output_path)

            # Salvar metadata como numpy
            np.save(INTERIM_DATA_DIR / f"{dcm_path.stem}_metadata.npy", metadata)

            if (idx + 1) % 100 == 0:
                print(f"Processed {idx + 1}/{len(dicom_files)}")

        except Exception as e:
            print(f"Error processing {dcm_path.name}: {e}")

    print("Preprocessing complete!")


class BACDataset(Dataset):
    """
    Dataset PyTorch para segmentação de BAC
    """

    def __init__(self, image_dir, mask_dir, transform=None, mode="train"):
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
        image = np.array(Image.open(img_path).convert("L"))
        mask = np.array(Image.open(mask_path).convert("L"))

        # Normalizar
        image = image.astype(np.float32) / 255.0
        mask = (mask > 127).astype(np.float32)  # Binarizar

        # Aplicar transformações
        if self.transform:
            augmented = self.transform(image=image, mask=mask)
            image = augmented["image"]
            mask = augmented["mask"]
        else:
            image = torch.from_numpy(image).unsqueeze(0)
            mask = torch.from_numpy(mask).unsqueeze(0)

        return {"image": image, "mask": mask, "filename": img_path.name}


def get_train_transforms():
    """Data augmentation para treino"""
    return A.Compose(
        [
            A.HorizontalFlip(p=0.5),
            A.ShiftScaleRotate(
                shift_limit=0.1, scale_limit=0.1, rotate_limit=15, p=0.5
            ),
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
            A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
            ToTensorV2(),
        ]
    )


def get_val_transforms():
    """Transformações para validação/teste"""
    return A.Compose([ToTensorV2()])
