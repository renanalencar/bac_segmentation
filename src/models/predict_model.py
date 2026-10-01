# -*- coding: utf-8 -*-
"""
Script para fazer predições com modelo treinado
"""
import click
import logging
from pathlib import Path
import torch
import numpy as np
from PIL import Image
import cv2
from tqdm import tqdm
import json
import sys

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.models.architecture import BACSegmentationModel


def calculate_bac_area(mask, pixel_spacing):
    """
    Calcular área de BAC em mm²
    
    Args:
        mask: Máscara binária (numpy array)
        pixel_spacing: [row_spacing, col_spacing] em mm
        
    Returns:
        area_mm2: Área em mm²
    """
    num_pixels = np.sum(mask > 0.5)
    pixel_area_mm2 = pixel_spacing[0] * pixel_spacing[1]
    area_mm2 = num_pixels * pixel_area_mm2
    
    return area_mm2


def classify_bac_severity(area_mm2):
    """
    Classificar severidade do BAC conforme artigo
    
    Zero: 0 mm²
    Mild: 0-10 mm²
    Moderate: 10-25 mm²
    Severe: ≥25 mm²
    """
    if area_mm2 == 0:
        return "Zero"
    elif area_mm2 < 10:
        return "Mild"
    elif area_mm2 < 25:
        return "Moderate"
    else:
        return "Severe"


def preprocess_image(image_path, target_size=1024):
    """Pré-processar imagem para inferência"""
    img = np.array(Image.open(image_path).convert('L'))
    img = img.astype(np.float32) / 255.0
    
    # Resize se necessário
    if img.shape != (target_size, target_size):
        img = cv2.resize(img, (target_size, target_size))
    
    # Para tensor (1, 1, H, W)
    img_tensor = torch.from_numpy(img).unsqueeze(0).unsqueeze(0)
    
    return img_tensor


@click.command()
@click.argument('model_path', type=click.Path(exists=True))
@click.argument('input_dir', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
@click.option('--threshold', default=0.5, help='Threshold for binary mask')
@click.option('--device', default='cuda', help='Device (cuda or cpu)')
@click.option('--save-masks', is_flag=True, help='Save prediction masks')
@click.option('--metadata-dir', default=None, help='Directory with metadata JSON files')
def main(model_path, input_dir, output_dir, threshold, device, save_masks, metadata_dir):
    """
    Fazer predições em imagens usando modelo treinado
    
    Args:
        model_path: Caminho para modelo treinado (.pth)
        input_dir: Diretório com imagens para processar
        output_dir: Diretório para salvar resultados
        
    Examples:
        python predict_model.py models/best_model.pth data/test/images outputs/ --save-masks
    """
    logger = logging.getLogger(__name__)
    logger.info('Starting predictions')
    
    # Setup
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    device = torch.device(device if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    
    # Carregar modelo
    logger.info(f"Loading model from {model_path}")
    checkpoint = torch.load(model_path, map_location=device)
    
    model_config = checkpoint.get('config', {
        "embed_dims": [64, 128, 320, 512],
        "num_heads": [1, 2, 5, 8],
        "mlp_ratios": [4, 4, 4, 4],
        "depths": [3, 4, 6, 3],
        "sr_ratios": [8, 4, 2, 1],
    })
    
    model = BACSegmentationModel(model_config).to(device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    logger.info("Model loaded successfully")
    
    # Listar imagens
    image_files = list(input_path.glob("*.png")) + list(input_path.glob("*.jpg"))
    logger.info(f"Found {len(image_files)} images")
    
    # Diretório para máscaras
    if save_masks:
        masks_dir = output_path / 'masks'
        masks_dir.mkdir(exist_ok=True)
    
    # Diretório para metadata se fornecido
    if metadata_dir:
        metadata_path = Path(metadata_dir)
    else:
        metadata_path = None
    
    # Predições
    results = []
    
    with torch.no_grad():
        for img_path in tqdm(image_files, desc="Processing images"):
            # Pré-processar
            img_tensor = preprocess_image(img_path).to(device)
            
            # Predição
            with torch.amp.autocast('cuda'):
                output = model(img_tensor)
            pred_mask = output.squeeze().cpu().numpy()
            
            # Binarizar
            binary_mask = (pred_mask > threshold).astype(np.uint8)
            
            # Carregar metadata se disponível
            pixel_spacing = [1.0, 1.0]  # Default
            if metadata_path:
                meta_file = metadata_path / f"{img_path.stem}.json"
                if meta_file.exists():
                    with open(meta_file, 'r') as f:
                        metadata = json.load(f)
                        pixel_spacing = metadata.get('pixel_spacing', [1.0, 1.0])
            
            # Calcular área em mm²
            area_mm2 = calculate_bac_area(binary_mask, pixel_spacing)
            severity = classify_bac_severity(area_mm2)
            
            # Salvar resultado
            result = {
                'filename': img_path.name,
                'bac_area_mm2': float(area_mm2),
                'severity': severity,
                'num_pixels': int(np.sum(binary_mask)),
                'pixel_spacing': pixel_spacing
            }
            results.append(result)
            
            logger.info(f"{img_path.name}: {area_mm2:.2f} mm² ({severity})")
            
            # Salvar máscara se solicitado
            if save_masks:
                mask_output = masks_dir / f"{img_path.stem}_pred.png"
                Image.fromarray((binary_mask * 255).astype(np.uint8)).save(mask_output)
    
    # Salvar resultados em JSON
    results_file = output_path / 'predictions.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Salvar resumo estatístico
    areas = [r['bac_area_mm2'] for r in results]
    severities = [r['severity'] for r in results]
    
    summary = {
        'total_images': len(results),
        'mean_bac_area': float(np.mean(areas)),
        'median_bac_area': float(np.median(areas)),
        'std_bac_area': float(np.std(areas)),
        'severity_distribution': {
            'Zero': severities.count('Zero'),
            'Mild': severities.count('Mild'),
            'Moderate': severities.count('Moderate'),
            'Severe': severities.count('Severe')
        }
    }
    
    summary_file = output_path / 'summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"\nPredictions complete!")
    logger.info(f"Results saved to {results_file}")
    logger.info(f"Summary: {summary}")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    main()