# Estúdio de vídeo

Motor de edição da Broadway Mídia para montar vídeos verticais com
imagens, cortes, sobreposição de texto e cartela final. O exemplo usa
ilustrações geradas localmente e a marca fictícia Café Aurora.

Na pasta `video-studio`, com Python 3.10 ou posterior e `ffmpeg` e
`ffprobe` instalados:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python examples/gerar_entradas.py
python -m estudio fix-mudo examples/pedido.json --fotos examples/cenas --saida saida
```

O comando salva o MP4 e o relatório de conferência em `saida/` quando
o pedido passa nas verificações. O JSON do exemplo define o visual,
o texto e a duração. O vídeo sai em 1080 × 1920, a 30 fps, sem áudio.
