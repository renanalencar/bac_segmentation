"""
Preparar dataset INbreast para anotação de BAC
"""

import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pydicom
from PIL import Image


def extract_dicoms_to_png(dicom_dir, output_dir):
    """
    Converter DICOMs do INbreast para PNG
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    dcm_files = list(Path(dicom_dir).rglob("*.dcm"))
    print(f"Found {len(dcm_files)} DICOM files")

    metadata_list = []

    for dcm_path in dcm_files:
        try:
            dcm = pydicom.dcmread(dcm_path)
            img = dcm.pixel_array.astype(np.float32)

            # Normalizar para 0-255
            img = (img - img.min()) / (img.max() - img.min() + 1e-8)
            img = (img * 255).astype(np.uint8)

            # Salvar PNG
            filename = dcm_path.stem
            png_path = output_path / f"{filename}.png"
            Image.fromarray(img).save(png_path)

            # Extrair metadata
            pixel_spacing = dcm.get("PixelSpacing", [1.0, 1.0])
            metadata = {
                "filename": filename,
                "pixel_spacing": [float(x) for x in pixel_spacing],
                "image_laterality": dcm.get("ImageLaterality", "Unknown"),
                "view_position": dcm.get("ViewPosition", "Unknown"),
                "original_path": str(dcm_path),
            }
            metadata_list.append(metadata)

        except Exception as e:
            print(f"Error processing {dcm_path}: {e}")

    # Salvar metadata
    with open(output_path / "metadata.json", "w") as f:
        json.dump(metadata_list, f, indent=2)

    print(f"Converted {len(metadata_list)} images to PNG")
    return metadata_list


def filter_cases_with_calcifications(xml_dir, images_dir, output_dir):
    """
    Filtrar apenas casos que têm calcificações no XML original
    (para reduzir workload do radiologista)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    calc_cases = []

    for xml_file in Path(xml_dir).glob("*.xml"):
        tree = ET.parse(xml_file)
        root = tree.getroot()

        has_calc = False
        for roi in root.findall(".//ROI"):
            finding = roi.find("finding")
            if finding is not None and "calc" in finding.text.lower():
                has_calc = True
                break

        if has_calc:
            case_id = xml_file.stem.split("_")[0]  # Extrair ID do caso
            calc_cases.append(case_id)

            # Copiar imagem
            for img_file in Path(images_dir).glob(f"{case_id}*.png"):
                shutil.copy(img_file, output_path / img_file.name)

    print(f"Filtered {len(calc_cases)} cases with calcifications")
    print(f"Total images to annotate: {len(list(output_path.glob('*.png')))}")

    # Salvar lista
    with open(output_path / "cases_with_calcifications.txt", "w") as f:
        f.write("\n".join(sorted(set(calc_cases))))

    return calc_cases


def create_annotation_guide(output_path):
    """
    Criar guia de anotação para o radiologista
    """
    guide = """
# GUIA DE ANOTAÇÃO - BREAST ARTERIAL CALCIFICATION (BAC)

## Objetivo
Anotar APENAS calcificações arteriais em mamografias para estudo de risco cardiovascular.

## O que ANOTAR (BAC - Breast Arterial Calcification):

✅ Calcificações VASCULARES com características:
   - Padrão LINEAR ou em "trilhos de trem" (parallel tracks)
   - Acompanham trajeto de vasos sanguíneos
   - Calcificações GROSSEIRAS nas paredes arteriais
   - Tipicamente BILATERAIS
   - Aspecto TUBULAR ou SERPIGINOSO

✅ Localização típica:
   - Artérias mamárias internas
   - Artérias subcutâneas
   - Artérias periféricas da mama

## O que NÃO anotar:

❌ Microcalcificações agrupadas (suspeitas de malignidade)
❌ Calcificações pleomórficas finas
❌ Calcificações em cluster
❌ Calcificações dentro de massas
❌ Calcificações cutâneas (skin)

## Como anotar no LabelMe:

1. Usar ferramenta "Create Polygons"
2. Contornar TODA a extensão da calcificação arterial
3. Label: "BAC"
4. Se incerto, marcar como "uncertain"
5. Se for microcalcificação maligna, ignorar (não anotar)

## Referências Visuais:
- BAC Tipo 1 (Linear): ||||||
- BAC Tipo 2 (Trilhos): ═════
- NÃO BAC (micro): • • • • •

## Critérios BI-RADS:
Calcificações arteriais = tipicamente BENIGNAS (BI-RADS 2)
Mas tem ALTO valor para predição cardiovascular!

## Tempo estimado:
- Caso SEM BAC: ~30 segundos (apenas verificar)
- Caso COM BAC: 2-5 minutos (anotar contornos)

## Dúvidas:
Contato: [rca2@ecomp.poli.br](rca2@ecomp.poli.br)
"""

    with open(output_path / "ANNOTATION_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide)

    print(f"Annotation guide saved to {output_path / 'ANNOTATION_GUIDE.md'}")


def main():
    """Pipeline completo de preparação"""
    print("=" * 60)
    print("INbreast Dataset Preparation for BAC Annotation")
    print("=" * 60)

    # Configurar caminhos
    inbreast_raw = Path("data/inbreast/raw")  # Onde estão os DICOMs
    inbreast_xml = Path("data/inbreast/xml")  # XMLs originais (se disponíveis)

    # 1. Converter DICOMs para PNG
    print("\n[1/4] Converting DICOMs to PNG...")
    images_dir = Path("data/inbreast/images")
    extract_dicoms_to_png(inbreast_raw, images_dir)

    # 2. Filtrar casos com calcificações (se tiver XMLs)
    if inbreast_xml.exists():
        print("\n[2/4] Filtering cases with calcifications...")
        annotation_dir = Path("data/inbreast/for_annotation")
        filter_cases_with_calcifications(inbreast_xml, images_dir, annotation_dir)
    else:
        print("\n[2/4] Skipping filtering (no XML files found)")
        annotation_dir = images_dir

    # 3. Criar guia de anotação
    print("\n[3/4] Creating annotation guide...")
    create_annotation_guide(annotation_dir)

    # 4. Instruções finais
    print("\n[4/4] Setup complete!")
    print("\n" + "=" * 60)
    print("NEXT STEPS FOR RADIOLOGIST:")
    print("=" * 60)
    print(f"1. Read annotation guide: {annotation_dir / 'ANNOTATION_GUIDE.md'}")
    print(f"2. Start LabelMe:")
    print(
        f"   labelme {annotation_dir} --output {annotation_dir / 'annotations'} --labels BAC,uncertain"
    )
    print(f"3. Annotate images following the guide")
    print(f"4. Save annotations (JSON files will be auto-created)")
    print("=" * 60)


if __name__ == "__main__":
    main()
