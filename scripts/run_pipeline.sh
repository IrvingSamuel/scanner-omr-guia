#!/usr/bin/env bash
#
# Orquestra o pipeline: limpa outputs antigos, roda o OMRChecker e o
# extract_barcodes em cada subpasta de inputs/, depois mescla tudo em:
# - final/respostas_consolidadas.csv
# - final/<ano>/<materia>.csv
#
# Uso:
#   bash scripts/run_pipeline.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

INPUTS_DIR="inputs"
OUTPUTS_DIR="outputs"
FINAL_DIR="final"
TEMPLATE_UNIVERSAL_DIR="templates/universal"

if [[ ! -d "$INPUTS_DIR" ]]; then
  echo "ERRO: pasta '$INPUTS_DIR' não existe."
  exit 1
fi
if [[ ! -f "$TEMPLATE_UNIVERSAL_DIR/template.json" ]]; then
  echo "ERRO: template universal ausente em '$TEMPLATE_UNIVERSAL_DIR/template.json'."
  exit 1
fi
if [[ ! -f "$TEMPLATE_UNIVERSAL_DIR/config.json" ]]; then
  echo "ERRO: config universal ausente em '$TEMPLATE_UNIVERSAL_DIR/config.json'."
  exit 1
fi

PYTHON="${PYTHON:-python3}"
if [[ -x ".venv/bin/python" ]]; then
  PYTHON=".venv/bin/python"
fi

echo "Limpando '$OUTPUTS_DIR'..."
rm -rf "$OUTPUTS_DIR"
mkdir -p "$OUTPUTS_DIR" "$FINAL_DIR"

shopt -s nullglob
processed=0
for dir in "$INPUTS_DIR"/*/; do
  name="$(basename "$dir")"
  out_dir="$OUTPUTS_DIR/$name"
  mkdir -p "$out_dir"

  # Injeta template/config universal em cada turma.
  cp "$TEMPLATE_UNIVERSAL_DIR/template.json" "$dir/template.json"
  cp "$TEMPLATE_UNIVERSAL_DIR/config.json" "$dir/config.json"

  echo
  echo "=== [$name] OMRChecker ==="
  "$PYTHON" OMRChecker/main.py --inputDir "$dir" --outputDir "$out_dir"

  echo "--- [$name] extrair barcodes ---"
  "$PYTHON" scripts/extract_barcodes.py \
    --inputDir "$dir" \
    --output "$out_dir/barcodes.csv"

  processed=$((processed + 1))
done

if [[ "$processed" -eq 0 ]]; then
  echo "Nenhuma subpasta encontrada em '$INPUTS_DIR/'."
  exit 1
fi

echo
echo "=== Mesclando resultados ==="
"$PYTHON" scripts/merge_results.py \
  --outputs-dir "$OUTPUTS_DIR" \
  --final-dir "$FINAL_DIR"

echo
echo "Pronto. CSVs gerados em: $FINAL_DIR"
