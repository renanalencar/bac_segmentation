# -*- coding: utf-8 -*-
"""
Script para visualização de resultados
"""
import click
import logging
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from PIL import Image
import json


def plot_training_history(history_file, output_dir):
    """Plotar curvas de treinamento"""
    with open(history_file, 'r') as f:
        history = json.load(f)
    
    epochs = [h['epoch'] for h in history]
    train_loss = [h['train_loss'] for h in history]
    val_loss = [h['val_loss'] for h in history]
    train_dice = [h['train_metrics']['dice'] for h in history]
    val_dice = [h['val_metrics']['dice'] for h in history]
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Loss
    axes[0].plot(epochs, train_loss, label='Train Loss', marker='o', markersize=3)
    axes[0].plot(epochs, val_loss, label='Val Loss', marker='s', markersize=3)
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training and Validation Loss')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Dice
    axes[1].plot(epochs, train_dice, label='Train Dice', marker='o', markersize=3)
    axes[1].plot(epochs, val_dice, label='Val Dice', marker='s', markersize=3)
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Dice Score')
    axes[1].set_title('Training and Validation Dice Score')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'training_curves.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Training curves saved to {output_path}")


def plot_predictions(image_dir, mask_dir, pred_dir, output_dir, num_samples=5):
    """Plotar comparação entre GT e predições"""
    image_path = Path(image_dir)
    mask_path = Path(mask_dir) if mask_dir else None
    pred_path = Path(pred_dir)
    output_path = Path(output_dir)
    
    image_files = sorted(list(image_path.glob("*.png")))[:num_samples]
    
    for img_file in image_files:
        # Carregar imagem
        img = np.array(Image.open(img_file).convert('L'))
        
        # Carregar GT mask se disponível
        if mask_path:
            mask_file = mask_path / f"{img_file.stem}_mask.png"
            gt_mask = np.array(Image.open(mask_file).convert('L')) if mask_file.exists() else None
        else:
            gt_mask = None
        
        # Carregar predição
        pred_file = pred_path / f"{img_file.stem}_pred.png"
        pred_mask = np.array(Image.open(pred_file).convert('L')) if pred_file.exists() else None
        
        # Plot
        if gt_mask is not None and pred_mask is not None:
            fig, axes = plt.subplots(1, 3, figsize=(15, 5))
            axes[0].imshow(img, cmap='gray')
            axes[0].set_title('Original Image')
            axes[0].axis('off')
            
            axes[1].imshow(gt_mask, cmap='hot')
            axes[1].set_title('Ground Truth')
            axes[1].axis('off')
            
            axes[2].imshow(pred_mask, cmap='hot')
            axes[2].set_title('Prediction')
            axes[2].axis('off')
        else:
            fig, axes = plt.subplots(1, 2, figsize=(10, 5))
            axes[0].imshow(img, cmap='gray')
            axes[0].set_title('Original Image')
            axes[0].axis('off')
            
            if pred_mask is not None:
                axes[1].imshow(pred_mask, cmap='hot')
                axes[1].set_title('Prediction')
                axes[1].axis('off')
        
        plt.tight_layout()
        output_file = output_path / f'prediction_{img_file.stem}.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logging.info(f"Saved visualization to {output_file}")


def plot_severity_distribution(predictions_file, output_dir):
    """Plotar distribuição de severidade"""
    with open(predictions_file, 'r') as f:
        predictions = json.load(f)
    
    severities = [p['severity'] for p in predictions]
    areas = [p['bac_area_mm2'] for p in predictions]
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Distribuição de severidade
    severity_counts = {s: severities.count(s) for s in ['Zero', 'Mild', 'Moderate', 'Severe']}
    colors = ['#2ecc71', '#f39c12', '#e67e22', '#e74c3c']
    
    axes[0].bar(severity_counts.keys(), severity_counts.values(), color=colors, alpha=0.7)
    axes[0].set_xlabel('Severity')
    axes[0].set_ylabel('Count')
    axes[0].set_title('BAC Severity Distribution')
    axes[0].grid(True, alpha=0.3, axis='y')
    
    # Histograma de áreas
    axes[1].hist(areas, bins=30, color='steelblue', alpha=0.7, edgecolor='black')
    axes[1].axvline(10, color='orange', linestyle='--', label='Mild/Moderate threshold')
    axes[1].axvline(25, color='red', linestyle='--', label='Moderate/Severe threshold')
    axes[1].set_xlabel('BAC Area (mm²)')
    axes[1].set_ylabel('Frequency')
    axes[1].set_title('BAC Area Distribution')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    output_path = Path(output_dir) / 'severity_distribution.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Severity distribution saved to {output_path}")


@click.command()
@click.option('--training-history', type=click.Path(exists=True), help='Path to training_history.json')
@click.option('--predictions', type=click.Path(exists=True), help='Path to predictions.json')
@click.option('--image-dir', type=click.Path(exists=True), help='Directory with original images')
@click.option('--mask-dir', type=click.Path(), help='Directory with GT masks (optional)')
@click.option('--pred-dir', type=click.Path(exists=True), help='Directory with prediction masks')
@click.option('--output-dir', type=click.Path(), default='reports/figures', help='Output directory for plots')
@click.option('--num-samples', default=5, help='Number of samples to visualize')
def main(training_history, predictions, image_dir, mask_dir, pred_dir, output_dir, num_samples):
    """
    Criar visualizações dos resultados
    
    Examples:
        # Plotar curvas de treinamento
        python visualize.py --training-history models/training_history.json --output-dir reports/figures
        
        # Plotar predições
        python visualize.py --image-dir data/test/images --pred-dir outputs/masks --output-dir reports/figures
        
        # Plotar distribuição de severidade
        python visualize.py --predictions outputs/predictions.json --output-dir reports/figures
    """
    logger = logging.getLogger(__name__)
    logger.info('Creating visualizations')
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Plotar curvas de treinamento
    if training_history:
        logger.info("Plotting training curves")
        plot_training_history(training_history, output_path)
    
    # Plotar predições
    if image_dir and pred_dir:
        logger.info("Plotting predictions")
        plot_predictions(image_dir, mask_dir, pred_dir, output_path, num_samples)
    
    # Plotar distribuição de severidade
    if predictions:
        logger.info("Plotting severity distribution")
        plot_severity_distribution(predictions, output_path)
    
    logger.info(f"Visualizations saved to {output_path}")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    main()