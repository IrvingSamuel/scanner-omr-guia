#!/usr/bin/env python3
"""
Detecta automaticamente as 80 bolhas (4 sub-blocos x 5 linhas x 4 alternativas)
de um gabarito de referência usando HoughCircles e imprime os parâmetros
necessários para o template.json do OMRChecker.

Uso:
    python3 scripts/measure_template.py <imagem_referencia.jpeg>
"""

import sys
import cv2
import numpy as np
from pathlib import Path


def main(path: str) -> None:
    img = cv2.imread(path)
    if img is None:
        raise SystemExit(f"Não consegui abrir: {path}")
    h, w = img.shape[:2]
    print(f"Imagem: {w}x{h} (W x H)")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 5)

    # HoughCircles na imagem inteira; depois filtramos pelos que estão na área
    # central onde ficam as bolhas (~y entre 0.50*h e 0.92*h, x entre 0.30*w e 0.75*w).
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=22,
        param1=80,
        param2=22,
        minRadius=12,
        maxRadius=22,
    )
    if circles is None:
        raise SystemExit("Nenhum círculo detectado.")
    circles = np.round(circles[0]).astype(int)
    print(f"Total de círculos detectados: {len(circles)}")

    cx_min, cx_max = int(0.30 * w), int(0.78 * w)
    cy_min, cy_max = int(0.48 * h), int(0.93 * h)
    bubbles = [
        (x, y, r)
        for (x, y, r) in circles
        if cx_min <= x <= cx_max and cy_min <= y <= cy_max
    ]
    print(f"Círculos na área OMR: {len(bubbles)}")

    # Ordena por y e agrupa em linhas: linhas próximas em y vão para o mesmo grupo.
    bubbles.sort(key=lambda b: (b[1], b[0]))
    rows: list[list[tuple[int, int, int]]] = []
    row_tol = 14
    for x, y, r in bubbles:
        if rows and abs(y - np.mean([b[1] for b in rows[-1]])) <= row_tol:
            rows[-1].append((x, y, r))
        else:
            rows.append([(x, y, r)])

    # Cada linha do gabarito tem 8 bolhas (4 da coluna esquerda + 4 da direita).
    # Mantém só linhas com pelo menos 6 bolhas (tolerante a falsos negativos).
    rows = [sorted(r, key=lambda b: b[0]) for r in rows if len(r) >= 6]
    print(f"Linhas válidas (>=6 bolhas): {len(rows)}")

    if len(rows) < 20:
        print("AVISO: esperava 20 linhas. Resultado pode estar incompleto.")

    # Separa cada linha em 'esquerda' (4 primeiras) e 'direita' (4 últimas).
    left_rows = [r[:4] for r in rows]
    right_rows = [r[-4:] for r in rows]

    avg_radius = int(np.mean([b[2] for b in bubbles]))
    print(f"Raio médio das bolhas: {avg_radius} -> bubbleDimensions ~ [{2*avg_radius}, {2*avg_radius}]")

    def block_stats(name: str, rows_block: list[list[tuple[int, int, int]]]) -> None:
        if not rows_block:
            return
        first_row = rows_block[0]
        ax, ay, _ = first_row[0]
        bx = first_row[1][0] if len(first_row) > 1 else ax + 24
        bubbles_gap = bx - ax
        if len(rows_block) > 1:
            labels_gap = rows_block[1][0][1] - first_row[0][1]
        else:
            labels_gap = 0
        print(
            f"  {name}: origin=[{ax}, {ay}] bubblesGap={bubbles_gap} labelsGap={labels_gap}"
        )

    print("\n=== Sub-blocos LEFT (Q01-05 e Q06-10) ===")
    block_stats("Q01-05", left_rows[:5])
    block_stats("Q06-10", left_rows[5:10])

    print("\n=== Sub-blocos RIGHT (Q11-15 e Q16-20) ===")
    block_stats("Q11-15", right_rows[:5])
    block_stats("Q16-20", right_rows[5:10])

    # Salva visualização
    vis = img.copy()
    for x, y, r in bubbles:
        cv2.circle(vis, (x, y), r, (0, 255, 0), 2)
    out = Path(path).with_suffix(".detected.jpg")
    cv2.imwrite(str(out), vis)
    print(f"\nVisualização salva em: {out}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
