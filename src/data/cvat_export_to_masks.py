# src/data/cvat_export_to_masks.py
"""
Exportar anotações CVAT para máscaras PNG
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from tqdm import tqdm


def cvat_coco_to_masks(coco_json_path, images_dir, masks_dir):
    """
    Converter exportação COCO do CVAT para máscaras binárias

    CVAT → Export → COCO 1.0 → Download annotations.json
    """
    with open(coco_json_path, "r") as f:
        coco = json.load(f)

    masks_path = Path(masks_dir)
    masks_path.mkdir(parents=True, exist_ok=True)

    # Criar dicionário de imagens
    images_dict = {img["id"]: img for img in coco["images"]}

    # Agrupar anotações por imagem
    annotations_by_image = {}
    for ann in coco["annotations"]:
        img_id = ann["image_id"]
        if img_id not in annotations_by_image:
            annotations_by_image[img_id] = []
        annotations_by_image[img_id].append(ann)

    stats = {"total_images": 0, "with_bac": 0, "total_bac": 0}

    # Processar cada imagem
    for img_id, img_info in tqdm(images_dict.items()):
        width = img_info["width"]
        height = img_info["height"]
        filename = img_info["file_name"]

        # Criar máscara
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)

        # Desenhar anotações
        if img_id in annotations_by_image:
            for ann in annotations_by_image[img_id]:
                # COCO segmentation format: [x1,y1,x2,y2,...]
                seg = ann["segmentation"][0]
                points = [(seg[i], seg[i + 1]) for i in range(0, len(seg), 2)]
                draw.polygon(points, fill=255)
                stats["total_bac"] += 1
            stats["with_bac"] += 1

        # Salvar máscara
        mask_filename = Path(filename).stem + "_mask.png"
        mask.save(masks_path / mask_filename)
        stats["total_images"] += 1

    print(f"\n{'=' * 60}")
    print("EXPORT STATISTICS")
    print(f"{'=' * 60}")
    print(f"Total images: {stats['total_images']}")
    print(f"Images with BAC: {stats['with_bac']}")
    print(f"Total BAC annotations: {stats['total_bac']}")
    print(f"{'=' * 60}")

    return stats


if __name__ == "__main__":
    # Uso após exportar do CVAT
    cvat_coco_to_masks(
        coco_json_path="data/cvat_export/annotations.json",
        images_dir="data/inbreast/for_annotation",
        masks_dir="data/inbreast/processed/masks",
    )
