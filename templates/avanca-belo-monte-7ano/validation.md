# Validacao e calibracao

## O que foi calibrado

- Escala base travada em A4 com unidade `--u: 0.18568mm` (conversao direta da referencia 1131px -> 210mm).
- Posicoes principais aplicadas com os mesmos valores medidos na imagem de origem (cabecalho, campos, grade e rodape).
- Grade OMR definida com parametros ajustaveis (`--row-h`, `--bubble`, `--stroke`), mantendo 20 questoes e 2 blocos de 10.

## Como conferir overlay

1. Abrir `overlay-check.html` em navegador desktop.
2. Ajustar o slider de opacidade para 50%.
3. Confirmar alinhamento visual de:
   - logo e barcode superior;
   - 3 campos de identificacao;
   - caixas da grade de respostas;
   - logos e barcode do rodape.

## Checklist de aceite (A4)

- [x] Artboard em `210mm x 297mm` com `@page` para impressao.
- [x] Layout em HTML/CSS sem rasterizar pagina inteira.
- [x] Estrategia hibrida aplicada apenas para elementos graficos (assets recortados).
- [x] Grade OMR 20 questoes implementada com tamanho calibravel.
- [x] Mapa de dimensoes documentado em `dimensions.md`.
