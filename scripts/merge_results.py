#!/usr/bin/env python3
"""
Mescla os CSVs do OMRChecker (Results_*.csv) com os CSVs de barcodes
extraídos por `extract_barcodes.py`, deriva matéria e série da subpasta de
input e gera:

1) um CSV geral consolidado; e
2) CSVs gerais por turma (ano) com nome da matéria.

Uso:
    python3 scripts/merge_results.py --outputs-dir outputs/ --final-dir final
"""

import argparse
import csv
from pathlib import Path

import pandas as pd


SUBJECT_LABELS = {
    "portugues": "Língua Portuguesa",
    "matematica": "Matemática",
}

GRADE_LABELS = {
    "6ano": "6º ano",
    "7ano": "7º ano",
    "8ano": "8º ano",
    "9ano": "9º ano",
}

QUESTION_COLS_OMR = [f"q{n}" for n in range(1, 21)]
QUESTION_COLS_OUT = [f"q{str(n).zfill(2)}" for n in range(1, 21)]


def slugify_subject(subject: str) -> str:
    lowered = subject.lower().strip()
    mapping = {
        "língua portuguesa": "portugues",
        "matemática": "matematica",
    }
    return mapping.get(lowered, lowered.replace(" ", "_"))


def parse_subfolder_name(name: str) -> tuple[str, str]:
    parts = name.split("_", 1)
    if len(parts) != 2:
        return name, ""
    subject_key, grade_key = parts
    materia = SUBJECT_LABELS.get(subject_key, subject_key.capitalize())
    serie = GRADE_LABELS.get(grade_key, grade_key)
    return materia, serie


def find_results_csv(subdir: Path) -> Path | None:
    candidates = sorted((subdir / "Results").glob("Results_*.csv"))
    if not candidates:
        return None
    return candidates[-1]


def normalize_response(value: object) -> str:
    """OMRChecker pode retornar '' (em branco) ou 'AB' (múltipla)."""
    if value is None:
        return "BLANK"
    text = str(value).strip()
    if text == "" or text.lower() == "nan":
        return "BLANK"
    if len(text) > 1:
        return "MULTI"
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outputs-dir", required=True, help="Pasta outputs/")
    parser.add_argument(
        "--final-dir",
        required=True,
        help="Diretório final para CSV consolidado e CSVs por turma",
    )
    args = parser.parse_args()

    outputs_dir = Path(args.outputs_dir)
    final_dir = Path(args.final_dir)
    final_dir.mkdir(parents=True, exist_ok=True)
    final_path = final_dir / "respostas_consolidadas.csv"

    rows: list[dict[str, str]] = []
    subdirs = [p for p in sorted(outputs_dir.iterdir()) if p.is_dir()]
    for subdir in subdirs:
        name = subdir.name
        materia, serie = parse_subfolder_name(name)

        results_csv = find_results_csv(subdir)
        barcodes_csv = subdir / "barcodes.csv"

        if results_csv is None:
            print(f"[AVISO] Sem Results_*.csv em {subdir}; pulando.")
            continue

        results_df = pd.read_csv(results_csv)
        for col in QUESTION_COLS_OMR:
            if col not in results_df.columns:
                results_df[col] = ""
        if "file_id" not in results_df.columns:
            print(f"[ERRO] file_id ausente em {results_csv}")
            continue

        if barcodes_csv.exists():
            barcodes_df = pd.read_csv(barcodes_csv, dtype=str).fillna("")
            id_map = dict(zip(barcodes_df["arquivo"], barcodes_df["student_id"]))
        else:
            print(f"[AVISO] {barcodes_csv} ausente; student_id ficará vazio.")
            id_map = {}

        for _, row in results_df.iterrows():
            arquivo = str(row["file_id"])
            entry: dict[str, str] = {
                "student_id": id_map.get(arquivo, ""),
                "arquivo": arquivo,
                "materia": materia,
                "serie": serie,
            }
            for src, dst in zip(QUESTION_COLS_OMR, QUESTION_COLS_OUT):
                entry[dst] = normalize_response(row.get(src, ""))
            rows.append(entry)

    if not rows:
        print("Nenhum resultado encontrado.")
        return

    fieldnames = ["student_id", "arquivo", "materia", "serie", *QUESTION_COLS_OUT]
    rows.sort(key=lambda r: (r["materia"], r["serie"], r["student_id"], r["arquivo"]))
    # utf-8-sig adiciona BOM para melhor compatibilidade com Excel no Windows.
    with final_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Gravado: {final_path} ({len(rows)} linhas)")

    # CSVs gerais por turma (ano), com nome da matéria no arquivo.
    by_grade_subject: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (row["serie"], row["materia"])
        by_grade_subject.setdefault(key, []).append(row)

    for (serie, materia), bucket in sorted(by_grade_subject.items()):
        grade_slug = serie.replace("º", "").replace(" ", "").lower()
        subject_slug = slugify_subject(materia)
        target_dir = final_dir / grade_slug
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"{subject_slug}.csv"

        grouped_fieldnames = ["student_id", *QUESTION_COLS_OUT]
        sorted_bucket = sorted(bucket, key=lambda r: (r["student_id"], r["arquivo"]))
        with target_file.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=grouped_fieldnames)
            writer.writeheader()
            for row in sorted_bucket:
                writer.writerow(
                    {"student_id": row["student_id"], **{q: row[q] for q in QUESTION_COLS_OUT}}
                )
        print(f"Gravado: {target_file} ({len(sorted_bucket)} linhas)")


if __name__ == "__main__":
    main()
