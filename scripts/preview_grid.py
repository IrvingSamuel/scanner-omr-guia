#!/usr/bin/env python3
"""
Sobrepõe a grade de bolhas definida no template.json sobre uma imagem de
gabarito, salvando uma imagem `_grid.jpg` para validação visual da calibração.

Uso:
    python3 scripts/preview_grid.py <template.json> <imagem.jpeg>
"""

import json
import sys
from pathlib import Path

import cv2


LETTERS = ["A", "B", "C", "D"]


def parse_field_labels(label_strings: list[str]) -> list[str]:
    """Imita o parser do OMRChecker para 'q01..5' -> ['q01','q02',...]"""
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
    img = cv2.imread(image_path)
    if img is None:
        raise SystemExit(f"Não consegui abrir {image_path}")

    bw, bh = tpl["bubbleDimensions"]
    blocks = tpl["fieldBlocks"]

    for block_name, block in blocks.items():
        ox, oy = block["origin"]
        bg = block["bubblesGap"]
        lg = block["labelsGap"]
        labels = parse_field_labels(block["fieldLabels"])
        for row_idx, label in enumerate(labels):
            row_y = oy + row_idx * lg
            for col_idx, letter in enumerate(LETTERS):
                col_x = ox + col_idx * bg
                cv2.rectangle(
                    img,
                    (col_x, row_y),
                    (col_x + bw, row_y + bh),
                    (0, 255, 0),
                    1,
                )
                cv2.putText(
                    img,
                    letter,
                    (col_x + 4, row_y - 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (255, 0, 0),
                    1,
                )
            cv2.putText(
                img,
                label,
                (ox - 50, row_y + bh - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 0, 255),
                1,
            )

    out_path = Path(image_path).with_suffix(".grid.jpg")
    cv2.imwrite(str(out_path), img)
    print(f"Salvo: {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
