"""
Converter anotações LabelMe JSON para máscaras binárias PNG
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from tqdm import tqdm


def labelme_json_to_mask(json_path, output_path, image_size=None, label_name="BAC"):
    """
    Converter um JSON do LabelMe para máscara binária

    Args:
        json_path: Caminho para arquivo .json do LabelMe
        output_path: Onde salvar a máscara PNG
        image_size: (width, height) - se None, pega do JSON
        label_name: Nome do label a converter (default: "BAC")
    """
    with open(json_path, "r") as f:
        data = json.load(f)

    # Dimensões da imagem
    if image_size is None:
        img_height = data["imageHeight"]
        img_width = data["imageWidth"]
    else:
        img_width, img_height = image_size

    # Criar máscara vazia
    mask = Image.new("L", (img_width, img_height), 0)
    draw = ImageDraw.Draw(mask)

    # Desenhar polígonos
    bac_count = 0
    for shape in data["shapes"]:
        if shape["label"] == label_name:
            points = [tuple(p) for p in shape["points"]]
            if len(points) >= 3:  # Precisa de pelo menos 3 pontos
                draw.polygon(points, fill=255)
                bac_count += 1

    # Salvar máscara
    mask.save(output_path)

    return bac_count


def process_all_annotations(json_dir, masks_dir, images_dir=None):
    """
    Processar todas as anotações JSON

    Args:
        json_dir: Diretório com JSONs do LabelMe
        masks_dir: Onde salvar máscaras
        images_dir: Diretório com imagens originais (para copiar)
    """
    json_path = Path(json_dir)
    masks_path = Path(masks_dir)
    masks_path.mkdir(parents=True, exist_ok=True)

    json_files = list(json_path.glob("*.json"))

    stats = {
        "total_images": len(json_files),
        "with_bac": 0,
        "without_bac": 0,
        "total_bac_regions": 0,
    }

    print(f"Processing {len(json_files)} annotations...")

    for json_file in tqdm(json_files):
        mask_file = masks_path / f"{json_file.stem}_mask.png"

        bac_count = labelme_json_to_mask(json_file, mask_file, label_name="BAC")

        if bac_count > 0:
            stats["with_bac"] += 1
            stats["total_bac_regions"] += bac_count
        else:
            stats["without_bac"] += 1

    # Copiar imagens correspondentes se solicitado
    if images_dir:
        images_path = Path(images_dir)
        images_output = masks_path.parent / "images"
        images_output.mkdir(exist_ok=True)

        for json_file in json_files:
            img_file = images_path / f"{json_file.stem}.png"
            if img_file.exists():
                import shutil

                shutil.copy(img_file, images_output / img_file.name)

    # Salvar estatísticas
    print("\n" + "=" * 60)
    print("ANNOTATION STATISTICS")
    print("=" * 60)
    print(f"Total images annotated: {stats['total_images']}")
    print(
        f"Images WITH BAC: {stats['with_bac']} ({stats['with_bac'] / stats['total_images'] * 100:.1f}%)"
    )
    print(
        f"Images WITHOUT BAC: {stats['without_bac']} ({stats['without_bac'] / stats['total_images'] * 100:.1f}%)"
    )
    print(f"Total BAC regions annotated: {stats['total_bac_regions']}")
    print(
        f"Average BAC regions per positive case: {stats['total_bac_regions'] / max(stats['with_bac'], 1):.2f}"
    )
    print("=" * 60)

    # Salvar JSON de estatísticas
    with open(masks_path.parent / "annotation_stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    return stats


if __name__ == "__main__":
    # Processar anotações
    process_all_annotations(
        json_dir="data/inbreast/annotations",
        masks_dir="data/inbreast/processed/masks",
        images_dir="data/inbreast/for_annotation",
    )
