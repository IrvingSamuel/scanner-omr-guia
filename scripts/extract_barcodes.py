#!/usr/bin/env python3
"""
Extrai o ID do aluno (Code39/Code128 no topo direito do gabarito) de cada imagem
da pasta indicada e grava um CSV `arquivo,student_id`.

Filtros:
- Ignora o barcode estático do rodapé (valor `ABC0123456789ABC`).
- Considera apenas barcodes na metade superior da imagem.
- Em caso de múltiplos candidatos, escolhe o de maior largura
  (o do topo é grande e impresso; o estático do rodapé é menor).

Uso:
    python3 scripts/extract_barcodes.py --inputDir <pasta> --output <csv>
"""

import argparse
import csv
from pathlib import Path

import cv2
from pyzbar.pyzbar import decode


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}
STATIC_FOOTER_BARCODE = "ABC0123456789ABC"


def detect_student_id(image_path: Path) -> str | None:
    img = cv2.imread(str(image_path))
    if img is None:
        return None
    height = img.shape[0]
    upper_half_max_y = height // 2

    candidates: list[tuple[int, str]] = []
    for code in decode(img):
        value = code.data.decode("utf-8", errors="ignore").strip()
        if not value or value == STATIC_FOOTER_BARCODE:
            continue
        if code.rect.top > upper_half_max_y:
            continue
        candidates.append((code.rect.width, value))

    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputDir", required=True, help="Pasta com as imagens")
    parser.add_argument("--output", required=True, help="Caminho do CSV de saída")
    args = parser.parse_args()

    input_dir = Path(args.inputDir)
    if not input_dir.is_dir():
        raise SystemExit(f"Pasta não encontrada: {input_dir}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for image_path in sorted(input_dir.iterdir()):
        if image_path.suffix.lower() not in IMAGE_EXTS:
            continue
        student_id = detect_student_id(image_path) or ""
        rows.append({"arquivo": image_path.name, "student_id": student_id})
        status = student_id if student_id else "<não detectado>"
        print(f"  {image_path.name} -> {status}")

    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["arquivo", "student_id"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Gravado: {output_path} ({len(rows)} linhas)")


if __name__ == "__main__":
    main()
