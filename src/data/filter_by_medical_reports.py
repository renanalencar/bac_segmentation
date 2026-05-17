"""
Filtrar imagens baseado em relatórios médicos que mencionam calcificação
"""

import re
import shutil
from pathlib import Path

# Diretórios
reports_dir = Path("data/inbreast/raw/INbreast Release 1.0/MedicalReports")
images_dir = Path("data/inbreast/images")
output_dir = Path("data/inbreast/for_annotation")
output_dir.mkdir(parents=True, exist_ok=True)

# Palavras-chave para calcificação (português e inglês)
calc_keywords = [
    "calcif",  # calcificação, calcification
    "calc ",  # calc
    "calcs",  # calcs (plural)
    "microcalc",
    "macrocalc",
    "arterial",
    "vascular",
    "bi-rads 2",  # Calcificações benignas
]

cases_with_calc = []
reports_found = 0

# Processar cada relatório
for report_file in reports_dir.glob("*.txt"):
    try:
        with open(report_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().lower()

        # Verificar se menciona calcificação
        has_calc = any(keyword in content for keyword in calc_keywords)

        if has_calc:
            # Extrair ID do caso (parte antes de _ no nome do arquivo)
            case_id = report_file.stem.split("_")[0]
            cases_with_calc.append(case_id)

            print(f"✅ Found calcification mention in: {report_file.name}")

        reports_found += 1

    except Exception as e:
        print(f"⚠️  Error reading {report_file.name}: {e}")

# Copiar imagens correspondentes
images_copied = 0
for case_id in set(cases_with_calc):
    # Procurar todas as imagens deste caso
    for img_file in images_dir.glob(f"*{case_id}*.png"):
        shutil.copy(img_file, output_dir / img_file.name)
        images_copied += 1

print(f"\n{'=' * 60}")
print(f"FILTERING SUMMARY")
print(f"{'=' * 60}")
print(f"Medical reports processed: {reports_found}")
print(f"Cases with calcification mentions: {len(set(cases_with_calc))}")
print(f"Images copied for annotation: {images_copied}")
print(f"Output directory: {output_dir}")
print(f"{'=' * 60}")

# Salvar lista de casos
with open(output_dir / "cases_with_calcifications.txt", "w") as f:
    f.write("\n".join(sorted(set(cases_with_calc))))
