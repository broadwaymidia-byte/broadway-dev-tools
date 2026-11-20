---
name: criativos
description: Prepara um pedido de post, story ou carrossel para o motor do Broadway Creative Lab.
---

# Criativos

Use o exemplo em `exemplos/pedido.json` como referência. Escolha um perfil em
`marcas/` e escreva os textos por peça, mantendo títulos curtos e um objetivo
por slide. Crie um novo JSON para cada pedido.

Na raiz do plugin, execute `python motor/estudio.py render caminho/do/pedido.json`.
Confira o relatório JSON gerado ao lado das imagens. Se houver erros, ajuste
o pedido e rode novamente. Mostre o caminho dos arquivos ao usuário.
