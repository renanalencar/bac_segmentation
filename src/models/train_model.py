# -*- coding: utf-8 -*-
"""
Script para treinar o modelo de segmentação de BAC
"""
import click
import logging
from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm
import json
import numpy as np

from src.models.architecture import BACSegmentationModel
from src.models.dataset import BACDataset, get_train_transforms, get_val_transforms


class DiceLoss(nn.Module):
    """Dice Loss para segmentação"""
    def __init__(self, smooth=1.0):
        super().__init__()
        self.smooth = smooth
    
    def forward(self, pred, target):
        # Flatten tudo
        pred = pred.contiguous().view(-1)
        target = target.contiguous().view(-1)
        
        intersection = (pred * target).sum()
        
        dice = (2. * intersection + self.smooth) / (
            pred.sum() + target.sum() + self.smooth
        )
        
        return 1 - dice


class CombinedLoss(nn.Module):
    """Dice Loss + Binary Cross Entropy (with logits and pos_weight)"""
    def __init__(self, dice_weight=0.5, bce_weight=0.5, pos_weight=868.0):
        super().__init__()
        self.dice = DiceLoss()
        # pos_weight to handle extreme class imbalance (99.88% background)
        self.bce = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pos_weight]))
        self.dice_weight = dice_weight
        self.bce_weight = bce_weight
    
    def forward(self, pred, target):
        # BCE with logits
        pred_flat = pred.contiguous().view(-1)
        target_flat = target.contiguous().view(-1)
        
        # Move pos_weight to the correct device
        if self.bce.pos_weight.device != pred.device:
            self.bce.pos_weight = self.bce.pos_weight.to(pred.device)
            
        bce_loss = self.bce(pred_flat, target_flat)
        
        # Dice needs probabilities
        pred_probs = torch.sigmoid(pred)
        dice_loss = self.dice(pred_probs, target)
        
        return self.dice_weight * dice_loss + self.bce_weight * bce_loss


def calculate_metrics(pred, target, threshold=0.5):
    """Calcular métricas de segmentação"""
    pred_probs = torch.sigmoid(pred)
    pred_binary = (pred_probs > threshold).float()
    target_binary = target.float()
    
    # Flatten
    pred_flat = pred_binary.view(-1)
    target_flat = target_binary.view(-1)
    
    intersection = (pred_flat * target_flat).sum()
    union = pred_flat.sum() + target_flat.sum() - intersection
    
    iou = (intersection + 1e-8) / (union + 1e-8)
    dice = (2 * intersection + 1e-8) / (pred_flat.sum() + target_flat.sum() + 1e-8)
    
    correct = (pred_flat == target_flat).sum()
    total = pred_flat.numel()
    pixel_acc = correct / total
    
    return {
        'iou': iou.item(),
        'dice': dice.item(),
        'pixel_accuracy': pixel_acc.item()
    }


def train_epoch(model, dataloader, criterion, optimizer, device, epoch, writer):
    """Treinar uma época"""
    model.train()
    running_loss = 0.0
    metrics_sum = {'iou': 0.0, 'dice': 0.0, 'pixel_accuracy': 0.0}
    
    pbar = tqdm(dataloader, desc=f"Epoch {epoch} [Train]")
    
    for batch_idx, batch in enumerate(pbar):
        images = batch['image'].to(device)
        masks = batch['mask'].to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, masks)
        
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
        batch_metrics = calculate_metrics(outputs.detach(), masks.detach())
        
        for key in metrics_sum:
            metrics_sum[key] += batch_metrics[key]
        
        pbar.set_postfix({
            'loss': f"{loss.item():.4f}",
            'dice': f"{batch_metrics['dice']:.4f}"
        })
        
        if batch_idx % 10 == 0:
            global_step = epoch * len(dataloader) + batch_idx
            writer.add_scalar('Train/Loss_step', loss.item(), global_step)
    
    num_batches = len(dataloader)
    avg_loss = running_loss / num_batches
    avg_metrics = {k: v / num_batches for k, v in metrics_sum.items()}
    
    return avg_loss, avg_metrics


def validate_epoch(model, dataloader, criterion, device, epoch, writer):
    """Validar uma época"""
    model.eval()
    running_loss = 0.0
    metrics_sum = {'iou': 0.0, 'dice': 0.0, 'pixel_accuracy': 0.0}
    
    pbar = tqdm(dataloader, desc=f"Epoch {epoch} [Val]")
    
    with torch.no_grad():
        for batch in pbar:
            images = batch['image'].to(device)
            masks = batch['mask'].to(device)
            
            outputs = model(images)
            loss = criterion(outputs, masks)
            
            running_loss += loss.item()
            batch_metrics = calculate_metrics(outputs, masks)
            
            for key in metrics_sum:
                metrics_sum[key] += batch_metrics[key]
            
            pbar.set_postfix({
                'loss': f"{loss.item():.4f}",
                'dice': f"{batch_metrics['dice']:.4f}"
            })
    
    num_batches = len(dataloader)
    avg_loss = running_loss / num_batches
    avg_metrics = {k: v / num_batches for k, v in metrics_sum.items()}
    
    return avg_loss, avg_metrics


@click.command()
@click.argument('data_dir', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
@click.option('--batch-size', default=4, help='Batch size')
@click.option('--epochs', default=100, help='Number of epochs')
@click.option('--lr', default=1e-4, help='Learning rate')
@click.option('--device', default='cuda', help='Device (cuda or cpu)')
@click.option('--num-workers', default=4, help='Number of data loader workers')
@click.option('--seed', default=42, help='Random seed')
@click.option('--resume', default=None, help='Path to checkpoint to resume from')
def main(data_dir, output_dir, batch_size, epochs, lr, device, num_workers, seed, resume):
    """
    Treinar modelo de segmentação de BAC
    
    Examples:
        python train_model.py data/processed models/ --epochs 100 --batch-size 4
    """
    logger = logging.getLogger(__name__)
    logger.info('Starting model training')
    
    torch.manual_seed(seed)
    np.random.seed(seed)
    
    data_path = Path(data_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    device = torch.device(device if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    
    train_dataset = BACDataset(
        image_dir=data_path / 'train' / 'images',
        mask_dir=data_path / 'train' / 'masks',
        transform=get_train_transforms(),
        mode='train'
    )
    
    val_dataset = BACDataset(
        image_dir=data_path / 'val' / 'images',
        mask_dir=data_path / 'val' / 'masks',
        transform=get_val_transforms(),
        mode='val'
    )
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )
    
    logger.info(f"Train samples: {len(train_dataset)}, Val samples: {len(val_dataset)}")
    
    model_config = {
        "embed_dims": [64, 128, 320, 512],
        "num_heads": [1, 2, 5, 8],
        "mlp_ratios": [4, 4, 4, 4],
        "depths": [3, 4, 6, 3],
        "sr_ratios": [8, 4, 2, 1],
    }
    
    model = BACSegmentationModel(model_config).to(device)
    
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Total parameters: {total_params:,}")
    logger.info(f"Trainable parameters: {trainable_params:,}")
    
    criterion = CombinedLoss(dice_weight=0.5, bce_weight=0.5)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5
    )
    
    writer = SummaryWriter(log_dir=output_path / 'runs')
    
    start_epoch = 0
    best_val_dice = 0.0
    
    if resume:
        logger.info(f"Resuming from checkpoint: {resume}")
        checkpoint = torch.load(resume)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        best_val_dice = checkpoint.get('best_val_dice', 0.0)
    
    training_history = []
    
    for epoch in range(start_epoch, epochs):
        logger.info(f"\nEpoch {epoch+1}/{epochs}")
        
        train_loss, train_metrics = train_epoch(
            model, train_loader, criterion, optimizer, device, epoch, writer
        )
        
        val_loss, val_metrics = validate_epoch(
            model, val_loader, criterion, device, epoch, writer
        )
        
        scheduler.step(val_loss)
        
        writer.add_scalar('Epoch/Train_Loss', train_loss, epoch)
        writer.add_scalar('Epoch/Val_Loss', val_loss, epoch)
        writer.add_scalar('Epoch/Train_Dice', train_metrics['dice'], epoch)
        writer.add_scalar('Epoch/Val_Dice', val_metrics['dice'], epoch)
        writer.add_scalar('Epoch/Learning_Rate', optimizer.param_groups[0]['lr'], epoch)
        
        logger.info(f"Train Loss: {train_loss:.4f}, Train Dice: {train_metrics['dice']:.4f}")
        logger.info(f"Val Loss: {val_loss:.4f}, Val Dice: {val_metrics['dice']:.4f}")
        
        training_history.append({
            'epoch': epoch,
            'train_loss': train_loss,
            'val_loss': val_loss,
            'train_metrics': train_metrics,
            'val_metrics': val_metrics,
            'lr': optimizer.param_groups[0]['lr']
        })
        
        if val_metrics['dice'] > best_val_dice:
            best_val_dice = val_metrics['dice']
            logger.info(f"New best model! Val Dice: {best_val_dice:.4f}")
            
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_val_dice': best_val_dice,
                'config': model_config
            }, output_path / 'best_model.pth')
        
        if (epoch + 1) % 5 == 0:
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_val_dice': best_val_dice,
                'config': model_config
            }, output_path / f'checkpoint_epoch_{epoch+1}.pth')
    
    with open(output_path / 'training_history.json', 'w') as f:
        json.dump(training_history, f, indent=2)
    
    writer.close()
    logger.info(f"Training complete! Best Val Dice: {best_val_dice:.4f}")
    logger.info(f"Model saved to {output_path / 'best_model.pth'}")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    main()