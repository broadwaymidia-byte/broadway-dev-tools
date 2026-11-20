# Broadway Creative Lab

Motor em Python e Playwright para montar posts, stories e carrosséis a
partir de um guia de marca. Renderiza PNGs e mockups e confere contraste,
texto cortado e área segura. O exemplo usa a marca fictícia Café Aurora.

Na pasta `creative-lab`, com Python 3.10 ou posterior:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
python motor/estudio.py render exemplos/pedido.json
```

As imagens e o relatório ficam em `exemplos/saida-cafe-aurora/`. Se você
tiver Chromium instalado no sistema, pode indicar o executável pela
variável `LAB_CHROMIUM`. Use arquivos de entrada de sua confiança. A
checagem de ortografia é opcional e requer Spylls e um dicionário Hunspell
pt-BR em `motor/dicionario/`.

Para experimentar a skill localmente com Claude Code, use
`claude --plugin-dir ./creative-lab` a partir da raiz do repositório.
