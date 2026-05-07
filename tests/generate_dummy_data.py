"""
Gerar dados dummy para testar o pipeline
"""
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
import json
from tqdm import tqdm


def generate_mammogram_background(size=1024):
    """Gerar fundo realista de mamografia"""
    # Gradiente radial simulando tecido mamário
    y, x = np.ogrid[:size, :size]
    center_y, center_x = size // 2, size // 2
    
    # Distância do centro
    distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    
    # Gradiente + ruído
    background = 255 - (distance / distance.max() * 80)
    noise = np.random.normal(0, 15, (size, size))
    
    mammogram = np.clip(background + noise, 0, 255).astype(np.uint8)
    
    return mammogram


def add_calcifications(image, mask, num_calcs=None):
    """Adicionar calcificações simuladas"""
    size = image.shape[0]
    
    if num_calcs is None:
        # Distribuição realista: 60% zero, 25% mild, 10% moderate, 5% severe
        rand = np.random.random()
        if rand < 0.60:
            num_calcs = 0  # Zero
        elif rand < 0.85:
            num_calcs = np.random.randint(1, 5)  # Mild (0-10 mm²)
        elif rand < 0.95:
            num_calcs = np.random.randint(5, 15)  # Moderate (10-25 mm²)
        else:
            num_calcs = np.random.randint(15, 40)  # Severe (≥25 mm²)
    
    for _ in range(num_calcs):
        # Posição aleatória (evitar bordas)
        center_x = np.random.randint(100, size - 100)
        center_y = np.random.randint(100, size - 100)
        
        # Tamanho aleatório da calcificação (2-8 pixels)
        calc_size = np.random.randint(2, 8)
        
        # Criar calcificação como círculo branco
        y, x = np.ogrid[-calc_size:calc_size, -calc_size:calc_size]
        circle = x**2 + y**2 <= calc_size**2
        
        # Adicionar à imagem
        y_min = max(0, center_y - calc_size)
        y_max = min(size, center_y + calc_size)
        x_min = max(0, center_x - calc_size)
        x_max = min(size, center_x + calc_size)
        
        circle_crop = circle[:y_max-y_min, :x_max-x_min]
        
        image[y_min:y_max, x_min:x_max][circle_crop] = 255
        mask[y_min:y_max, x_min:x_max][circle_crop] = 1
    
    return image, mask


def calculate_bac_area_pixels(mask, pixel_spacing=[0.1, 0.1]):
    """Calcular área em mm² (simulado)"""
    num_pixels = np.sum(mask)
    pixel_area_mm2 = pixel_spacing[0] * pixel_spacing[1]
    area_mm2 = num_pixels * pixel_area_mm2
    return area_mm2


def classify_severity(area_mm2):
    """Classificar severidade"""
    if area_mm2 == 0:
        return "Zero"
    elif area_mm2 < 10:
        return "Mild"
    elif area_mm2 < 25:
        return "Moderate"
    else:
        return "Severe"


def generate_dummy_dataset(output_dir, num_samples=100, split_ratios=(0.7, 0.15, 0.15)):
    """
    Gerar dataset dummy completo
    
    Args:
        output_dir: Diretório de saída
        num_samples: Número total de amostras
        split_ratios: (train, val, test)
    """
    print(f"🎨 Generating {num_samples} dummy mammogram samples...")
    
    output_path = Path(output_dir)
    
    # Criar estrutura de diretórios
    for split in ['train', 'val', 'test']:
        (output_path / split / 'images').mkdir(parents=True, exist_ok=True)
        (output_path / split / 'masks').mkdir(parents=True, exist_ok=True)
    
    (output_path / 'metadata').mkdir(exist_ok=True)
    
    # Calcular quantidades por split
    num_train = int(num_samples * split_ratios[0])
    num_val = int(num_samples * split_ratios[1])
    num_test = num_samples - num_train - num_val
    
    splits = ['train'] * num_train + ['val'] * num_val + ['test'] * num_test
    
    # Estatísticas
    stats = {'Zero': 0, 'Mild': 0, 'Moderate': 0, 'Severe': 0}
    
    # Gerar amostras
    for idx in tqdm(range(num_samples), desc="Generating samples"):
        split = splits[idx]
        
        # Gerar mamografia
        mammogram = generate_mammogram_background(1024)
        mask = np.zeros((1024, 1024), dtype=np.uint8)
        
        # Adicionar calcificações
        mammogram, mask = add_calcifications(mammogram, mask)
        
        # Calcular área e severidade
        pixel_spacing = [0.1, 0.1]  # 0.1mm por pixel (típico)
        area_mm2 = calculate_bac_area_pixels(mask, pixel_spacing)
        severity = classify_severity(area_mm2)
        stats[severity] += 1
        
        # Salvar imagem
        filename = f"dummy_{idx:04d}"
        img_path = output_path / split / 'images' / f"{filename}.png"
        Image.fromarray(mammogram).save(img_path)
        
        # Salvar máscara
        mask_path = output_path / split / 'masks' / f"{filename}_mask.png"
        Image.fromarray((mask * 255).astype(np.uint8)).save(mask_path)
        
        # Salvar metadata
        metadata = {
            'filename': filename,
            'pixel_spacing': pixel_spacing,
            'bac_area_mm2': float(area_mm2),
            'severity': severity,
            'num_pixels': int(np.sum(mask)),
            'split': split
        }
        
        metadata_path = output_path / 'metadata' / f"{filename}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    # Salvar estatísticas do dataset
    dataset_info = {
        'total_samples': num_samples,
        'splits': {
            'train': num_train,
            'val': num_val,
            'test': num_test
        },
        'severity_distribution': stats,
        'pixel_spacing': [0.1, 0.1],
        'image_size': [1024, 1024]
    }
    
    with open(output_path / 'dataset_info.json', 'w') as f:
        json.dump(dataset_info, f, indent=2)
    
    print("\n✅ Dummy dataset generated successfully!")
    print(f"📊 Distribution: {stats}")
    print(f"📁 Location: {output_path}")
    print(f"   - Train: {num_train} samples")
    print(f"   - Val: {num_val} samples")
    print(f"   - Test: {num_test} samples")


if __name__ == '__main__':
    # Gerar dataset dummy
    generate_dummy_dataset(
        output_dir='data/processed',
        num_samples=100,  # Começar pequeno para teste
        split_ratios=(0.7, 0.15, 0.15)
    )