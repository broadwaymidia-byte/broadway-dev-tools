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

## Imagens e chave do Gemini

A versão pública monta as peças usando imagens fornecidas no pedido JSON.
Ela funciona sem chave e sem conta do Gemini. Gere ou selecione as imagens
que quer usar, salve os arquivos e informe seus caminhos no campo `imagem`.

A edição interna que inclui o conector do Nano Banana usa a variável
`GEMINI_API_KEY` no ambiente que executa a geração. Cada pessoa deve usar
uma chave do próprio projeto Google. No Terminal do Mac com zsh, configure
a variável para a janela atual com:

```zsh
read -rs 'GEMINI_API_KEY?Cole a chave do Gemini e aperte Enter: ' && export GEMINI_API_KEY
```

A chave fica invisível durante a digitação. Guarde-a fora do repositório
e dos arquivos do pedido.
