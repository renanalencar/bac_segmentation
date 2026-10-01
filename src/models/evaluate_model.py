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

def calculate_metrics(pred_mask, true_mask):
    """
    Calcular TP, FP, TN, FN
    """
    pred = (pred_mask > 0).astype(np.uint8)
    true = (true_mask > 0).astype(np.uint8)
    
    tp = np.sum((pred == 1) & (true == 1))
    fp = np.sum((pred == 1) & (true == 0))
    tn = np.sum((pred == 0) & (true == 0))
    fn = np.sum((pred == 0) & (true == 1))
    
    return tp, fp, tn, fn

@click.command()
@click.argument('model_path', type=click.Path(exists=True))
@click.argument('data_dir', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
@click.option('--threshold', default=0.5, help='Limiar para máscara binária')
@click.option('--device', default='cuda', help='Device (cuda or cpu)')
def main(model_path, data_dir, output_dir, threshold, device):
    """
    Avalia as métricas do modelo treinado no conjunto de validação.
    
    Args:
        model_path: Caminho para o checkpoint (.pth)
        data_dir: Diretório base processado (data/processed/val)
        output_dir: Diretório para salvar resultados
    """
    logger = logging.getLogger(__name__)
    logger.info('Iniciando avaliação do modelo no conjunto de validação')
    
    val_images_dir = Path(data_dir) / 'images'
    val_masks_dir = Path(data_dir) / 'masks'
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    device = torch.device(device if torch.cuda.is_available() else 'cpu')
    
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    
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
    
    image_files = list(val_images_dir.glob("*.png"))
    
    global_tp, global_fp, global_tn, global_fn = 0, 0, 0, 0
    results = []
    
    with torch.no_grad():
        for img_path in tqdm(image_files, desc="Avaliando"):
            mask_path = val_masks_dir / f"{img_path.stem}_mask.png"
            if not mask_path.exists():
                continue
                
            img = np.array(Image.open(img_path).convert('L')).astype(np.float32) / 255.0
            img_tensor = torch.from_numpy(img).unsqueeze(0).unsqueeze(0).to(device)
            
            true_mask = np.array(Image.open(mask_path).convert('L'))
            
            # Autocast para acelerar a predição na avaliação também
            with torch.amp.autocast('cuda'):
                output = model(img_tensor)
                
            pred_mask = output.squeeze().cpu().numpy()
            binary_mask = (pred_mask > threshold).astype(np.uint8)
            
            tp, fp, tn, fn = calculate_metrics(binary_mask, true_mask)
            
            global_tp += tp
            global_fp += fp
            global_tn += tn
            global_fn += fn
            
            # Image-level metrics (opcional salvar)
            img_dice = (2 * tp) / (2 * tp + fp + fn + 1e-8)
            results.append({
                'image': img_path.name,
                'dice': float(img_dice)
            })

    # Métricas Globais (Pixel-level)
    sensitivity = global_tp / (global_tp + global_fn + 1e-8)
    specificity = global_tn / (global_tn + global_fp + 1e-8)
    precision = global_tp / (global_tp + global_fp + 1e-8)
    dice = (2 * global_tp) / (2 * global_tp + global_fp + global_fn + 1e-8)
    iou = global_tp / (global_tp + global_fp + global_fn + 1e-8)
    
    metrics = {
        'Global_Metrics': {
            'Sensitivity (Recall)': float(sensitivity),
            'Specificity': float(specificity),
            'Precision': float(precision),
            'Dice_Score': float(dice),
            'IoU': float(iou)
        },
        'Counts': {
            'TP': int(global_tp),
            'FP': int(global_fp),
            'TN': int(global_tn),
            'FN': int(global_fn)
        }
    }
    
    logger.info(f"Sensibilidade (Recall): {sensitivity:.4f}")
    logger.info(f"Especificidade: {specificity:.4f}")
    logger.info(f"Dice Score: {dice:.4f}")
    
    with open(output_path / 'evaluation_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=4)
        
    logger.info(f"Resultados detalhados salvos em {output_path / 'evaluation_metrics.json'}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    main()
