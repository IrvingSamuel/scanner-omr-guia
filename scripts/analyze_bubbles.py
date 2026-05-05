#!/usr/bin/env python3
"""
Analisa a intensidade média de cada bolha numa imagem de gabarito usando o
template.json. Imprime as 4 médias por questão e a alternativa escolhida (a
mais escura). Útil para diagnosticar o threshold do OMRChecker.

Uso:
    python3 scripts/analyze_bubbles.py <template.json> <imagem.jpeg>
"""

import json
import sys
from pathlib import Path

import cv2
import numpy as np

LETTERS = ["A", "B", "C", "D"]


def parse_field_labels(label_strings: list[str]) -> list[str]:
    out: list[str] = []
    for label in label_strings:
        if ".." in label:
            prefix = "".join(c for c in label if not (c.isdigit() or c == "."))
            num_part = label[len(prefix) :]
            start_str, end_str = num_part.split("..")
            start, end = int(start_str), int(end_str)
            width = len(start_str)
            for n in range(start, end + 1):
                out.append(f"{prefix}{str(n).zfill(width)}")
        else:
            out.append(label)
    return out


def main(template_path: str, image_path: str) -> None:
    tpl = json.loads(Path(template_path).read_text())
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise SystemExit(f"Não consegui abrir {image_path}")

    bw, bh = tpl["bubbleDimensions"]
    blocks = tpl["fieldBlocks"]

    rows: list[tuple[str, list[float], str]] = []
    for block_name, block in blocks.items():
        ox, oy = block["origin"]
        bg = block["bubblesGap"]
        lg = block["labelsGap"]
        labels = parse_field_labels(block["fieldLabels"])
        for row_idx, label in enumerate(labels):
            row_y = oy + row_idx * lg
            means: list[float] = []
            for col_idx in range(4):
                col_x = ox + col_idx * bg
                # Recorta com pequena margem interna (3 px) para evitar a borda da bolha
                roi = img[row_y + 3 : row_y + bh - 3, col_x + 3 : col_x + bw - 3]
                means.append(float(roi.mean()))
            chosen = LETTERS[int(np.argmin(means))]
            rows.append((label, means, chosen))

    rows.sort(key=lambda r: r[0])
    print(f"{'Q':<5} {'A':>6} {'B':>6} {'C':>6} {'D':>6}  pick")
    for label, means, chosen in rows:
        cells = " ".join(f"{m:6.1f}" for m in means)
        print(f"{label:<5} {cells}  {chosen}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
