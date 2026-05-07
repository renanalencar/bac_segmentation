# -*- coding: utf-8 -*-
import json
import logging
from pathlib import Path

import boto3
import click
import cv2
import numpy as np
import pydicom
from dotenv import find_dotenv, load_dotenv
from PIL import Image
from tqdm import tqdm

# Configurações
EMBED_BUCKET = "emory-breast-imaging-dataset"
EMBED_REGION = "us-east-1"
IMAGE_SIZE = 1024


def download_embed_mlo_images(output_dir, max_images=1000):
    """
    Baixar mamografias MLO do EMBED dataset

    Args:
        output_dir: Diretório de saída
        max_images: Número máximo de imagens
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Downloading EMBED MLO images to {output_dir}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    s3 = boto3.client("s3", region_name=EMBED_REGION)
    paginator = s3.get_paginator("list_objects_v2")

    count = 0
    for page in paginator.paginate(Bucket=EMBED_BUCKET):
        if count >= max_images:
            break

        for obj in page.get("Contents", []):
            if count >= max_images:
                break

            key = obj["Key"]
            # Filtrar apenas DICOMs MLO
            if ".dcm" in key.lower() and "mlo" in key.lower():
                local_path = output_path / Path(key).name

                if not local_path.exists():
                    try:
                        s3.download_file(EMBED_BUCKET, key, str(local_path))
                        count += 1
                        logger.info(f"Downloaded {count}/{max_images}: {key}")
                    except Exception as e:
                        logger.error(f"Error downloading {key}: {e}")

    logger.info(f"Download complete! Total images: {count}")
    return count


def preprocess_dicom(dicom_path, target_size=IMAGE_SIZE):
    """
    Pré-processar DICOM para formato normalizado

    Args:
        dicom_path: Caminho para arquivo DICOM
        target_size: Tamanho alvo da imagem

    Returns:
        img_padded: Imagem preprocessada
        metadata: Metadata do DICOM
    """
    dcm = pydicom.dcmread(dicom_path)
    img = dcm.pixel_array.astype(np.float32)

    # Normalizar intensidade (0-1)
    img = (img - img.min()) / (img.max() - img.min() + 1e-8)

    # Resize mantendo aspect ratio
    h, w = img.shape
    scale = target_size / max(h, w)
    new_h, new_w = int(h * scale), int(w * scale)
    img_resized = cv2.resize(img, (new_w, new_h))

    # Padding central para quadrado
    img_padded = np.zeros((target_size, target_size), dtype=np.float32)
    pad_h = (target_size - new_h) // 2
    pad_w = (target_size - new_w) // 2
    img_padded[pad_h : pad_h + new_h, pad_w : pad_w + new_w] = img_resized

    # Extrair metadata (importante para calcular mm²)
    pixel_spacing = dcm.get("PixelSpacing", [1.0, 1.0])
    metadata = {
        "pixel_spacing": pixel_spacing,
        "padding": (pad_h, pad_w),
        "scale": scale,
        "original_shape": (h, w),
        "patient_id": str(dcm.get("PatientID", "unknown")),
        "study_date": str(dcm.get("StudyDate", "unknown")),
    }

    return img_padded, metadata


def process_dicoms(input_dir, output_dir):
    """
    Processar todos os DICOMs do diretório

    Args:
        input_dir: Diretório com DICOMs brutos
        output_dir: Diretório de saída para PNGs processados
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing DICOMs from {input_dir}")

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Criar subdiretório para metadados
    metadata_d
