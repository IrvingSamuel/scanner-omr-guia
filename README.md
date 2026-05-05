# Scanner de Gabaritos (OMR + Barcode)

Sistema para leitura automática de gabaritos escaneados (20 questões A/B/C/D),
com identificação do aluno pelo código de barras e exportação para CSV.

Este projeto combina:
- [OMRChecker](https://github.com/Udayraj123/OMRChecker) para leitura das bolhas.
- [pyzbar](https://pypi.org/project/pyzbar/) para leitura do barcode do aluno.

## Pré-requisitos do sistema

```bash
sudo apt-get install -y libzbar0
```

(`libzbar0` é necessário para o `pyzbar`.)

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
git clone https://github.com/Udayraj123/OMRChecker.git OMRChecker
```

## Execução rápida

```bash
source .venv/bin/activate
bash scripts/run_pipeline.sh
```

## Formato dos dados de entrada

Crie subpastas em `inputs/` no padrão:

`<materia>_<serie>`

Exemplos:
- `portugues_6ano`
- `portugues_7ano`
- `matematica_6ano`
- `matematica_7ano`

Regras:
- `materia`: sem acento e minúsculo (`portugues`, `matematica`).
- `serie`: formato `6ano`, `7ano`, `8ano`, `9ano`.
- Coloque apenas imagens do gabarito na pasta (`jpg`, `jpeg`, `png`, `tif`).

## Template universal

O projeto usa um único template generalista em:

- `templates/universal/template.json`
- `templates/universal/config.json`

O `run_pipeline.sh` copia esse template automaticamente para cada pasta de
entrada antes de rodar o OMRChecker.

## Saídas geradas

### 1) Consolidado geral

- `final/respostas_consolidadas.csv`
- Colunas: `student_id,arquivo,materia,serie,q01..q20`

### 2) CSVs gerais por turma/matéria

- `final/<ano>/<materia>.csv`
- Colunas: `student_id,q01..q20`

Exemplos:
- `final/6ano/portugues.csv`
- `final/6ano/matematica.csv`
- `final/7ano/portugues.csv`
- `final/7ano/matematica.csv`

Observações:
- Resposta em branco -> `BLANK`
- Múltipla marcação -> `MULTI`
- CSVs são gravados com `UTF-8 BOM` para compatibilidade com Excel.

## Fluxo interno do pipeline

1. Lê cada pasta em `inputs/*/`.
2. Injeta `template.json` e `config.json` universais na pasta.
3. Roda OMRChecker e gera resultados brutos em `outputs/`.
4. Extrai `student_id` via barcode por imagem.
5. Faz merge e grava os CSVs finais em `final/`.

## Como recalibrar o template

Se as bolhas ficarem desalinhadas:

```bash
python3 OMRChecker/main.py --setLayout -i inputs/portugues_7ano/
```

Ajuste `origin`, `bubblesGap` e `labelsGap` dos `fieldBlocks` no
`templates/universal/template.json`.

## Estrutura do projeto

```text
Scanner/
├── OMRChecker/                     # upstream vendored
├── inputs/                         # subpastas por materia_serie
├── outputs/                        # resultados brutos do OMRChecker + barcodes.csv
├── templates/
│   └── universal/
│       ├── config.json
│       └── template.json
├── scripts/
│   ├── extract_barcodes.py
│   ├── merge_results.py
│   └── run_pipeline.sh
├── final/
│   ├── respostas_consolidadas.csv
│   └── <ano>/<materia>.csv
├── scans/                          # imagens originais (referência)
├── requirements.txt
└── README.md
```
