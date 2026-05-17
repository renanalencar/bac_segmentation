"""
Criar amostra aleatória de imagens para anotação
"""

import random
import shutil
from pathlib import Path

# Seed para reprodutibilidade
random.seed(42)

images_dir = Path("data/inbreast/images")
output_dir = Path("data/inbreast/for_annotation")
output_dir.mkdir(parents=True, exist_ok=True)

# Listar todas as imagens
all_images = list(images_dir.glob("*.png"))

# Amostra de 100 imagens (ou 150, 200 - ajuste conforme orçamento)
sample_size = 100
sampled = random.sample(all_images, min(sample_size, len(all_images)))

# Copiar imagens
for img in sampled:
    shutil.copy(img, output_dir / img.name)

print(f"Sampled {len(sampled)} images from {len(all_images)} total")
print(f"Output: {output_dir}")
