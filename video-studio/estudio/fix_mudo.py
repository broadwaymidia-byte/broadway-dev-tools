"""Monta vídeos verticais com imagens, texto sobreposto e cartela final."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

try:  # fotos HEIC do iPhone (opcional: sem a biblioteca, só JPG e PNG)
    import pillow_heif

    pillow_heif.register_heif_opener()
except Exception:  # pragma: no cover
    pass

from . import conferir as conf
from .marca import ErroMarca, Marca, carregar
from .texto import Frase, fichas, frase_de, largura_maxima, quebra, quebra_com_linhas

W, H, FPS = 1080, 1920, 30
FFMPEG = os.environ.get("ESTUDIO_FFMPEG", "ffmpeg")
FFPROBE = os.environ.get("ESTUDIO_FFPROBE", "ffprobe")

CARTELA_FIX = {
    "meta": "CAFÉ AURORA",
    "etiqueta": "GUIA DE PREPARO",
    "titulo": {"texto": "Café sem pressa", "destaque": "Café"},
    "subtitulo": "Reserve um momento para o seu café.",
    "chamada": "Salve para mais tarde.",
}


@dataclass(frozen=True)
class Layout:
    """Geometria e ritmo do modelo de vídeo."""

    margem: int = 72
    corpo: int = 92  # tamanho da letra do texto dos cortes
    entre_linhas: int = 104
    fim_texto: float = 0.64  # o texto termina a 70% da altura
    logo_esq: int = 60
    logo_topo: int = 250
    logo_tam: int = 96
    zoom_fim: float = 1.05  # empurrão leve: 1,00 → 1,05
    saturacao: float = 1.08
    contraste: float = 1.03


LAYOUT = Layout()


class ErroPedido(Exception):
    """Frase curta, pronta para a tela."""


@dataclass
class Pedido:
    marca: str
    fotos: list[dict]  # {"arquivo", "anunciante_legivel", "autorizado"}; a primeira é a do começo
    gancho: Frase
    textos: list[Frase]  # cada um fica em 2 cortes
    cartela: dict
    duracao_gancho: float = 2.6
    duracao_corte: float = 0.9
    duracao_cartela: float = 3.6
    logo_nas_cenas: bool = False  # só quando a equipe pede; a cartela final sempre leva a logo


def _texto(dado, campo: str, limite: int, obrigatorio=True) -> str:
    v = str(dado or "").strip()
    if obrigatorio and not v:
        raise ErroPedido(f"Escreva {campo}.")
    if len(v) > limite:
        raise ErroPedido(f"{campo[0].upper() + campo[1:]} passou de {limite} letras. Encurte.")
    return v


def ler_pedido(dados: dict) -> Pedido:
    """Valida o pedido que vem da tela. Tudo que a tela confere é conferido de novo aqui (server action é endereço público)."""
    marca = str(dados.get("marca", ""))
    fotos_in = dados.get("fotos") or []
    if not 3 <= len(fotos_in) <= 40:
        raise ErroPedido("Escolha de 3 a 40 fotos.")
    fotos = []
    for f in fotos_in:
        nome = str(f.get("arquivo", ""))
        if not nome or nome != os.path.basename(nome) or nome.startswith("."):
            raise ErroPedido("Nome de foto inválido.")
        fotos.append({"arquivo": nome, "anunciante_legivel": bool(f.get("anunciante_legivel")), "autorizado": bool(f.get("autorizado"))})
    gancho = frase_de(dados.get("gancho") or "")
    _texto(gancho.texto, "a frase do começo", 120)
    textos = [frase_de(t) for t in (dados.get("textos") or [])]
    if not 1 <= len(textos) <= 12:
        raise ErroPedido("Escreva de 1 a 12 textos para os cortes.")
    for t in textos:
        _texto(t.texto, "o texto do corte", 90)
    cart = dict(CARTELA_FIX)
    cart.update({k: v for k, v in (dados.get("cartela") or {}).items() if v not in (None, "")})
    titulo = frase_de(cart["titulo"])
    _texto(titulo.texto, "o título da cartela", 60)
    cart["titulo"] = {"texto": titulo.texto, "destaque": titulo.destaque}
    for campo, limite in (("meta", 40), ("etiqueta", 30), ("subtitulo", 90), ("chamada", 70)):
        cart[campo] = _texto(cart[campo], f"a cartela ({campo})", limite)
    ped = Pedido(marca, fotos, gancho, textos, cart, logo_nas_cenas=bool(dados.get("logo_nas_cenas", False)))
    for campo, (lo, hi), rotulo in (("duracao_gancho", (1.5, 4.0), "a duração do começo"), ("duracao_corte", (0.5, 2.0), "a duração dos cortes"), ("duracao_cartela", (2.0, 6.0), "a duração da cartela")):
        if campo in dados:
            try:
                v = float(dados[campo])
            except (TypeError, ValueError):
                raise ErroPedido(f"Valor inválido em {rotulo}.")
            if not lo <= v <= hi:
                raise ErroPedido(f"Use {lo:g} a {hi:g} s em {rotulo}.")
            setattr(ped, campo, v)
    return ped


# ---------------------------------------------------------------- imagens

def capa_916(img: Image.Image, w: int, h: int) -> Image.Image:
    """Preenche w × h cortando o excesso no centro."""
    r = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * r), round(img.height * r)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def abrir_foto(caminho: Path) -> Image.Image:
    try:
        img = Image.open(caminho)
        img = ImageOps.exif_transpose(img)
        return img.convert("RGB")
    except Exception:
        raise ErroPedido(f"Não deu para abrir a foto {caminho.name}. Troque por outra.")


def _misturar(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def _cor(marca: Marca, nome: str, *reserva: str):
    for n in (nome, *reserva):
        if n in marca.cores:
            return marca.cores[n]
    raise ErroMarca(f"A marca {marca.nome} não tem a cor \"{nome}\".")


def _logo(marca: Marca, tam: int) -> Image.Image:
    return Image.open(marca.logo).convert("RGBA").resize((tam, tam), Image.LANCZOS)


def _sombra(marca: Marca) -> Image.Image:
    """Escurecimento só embaixo, atrás do texto (direção da marca: nada de moldura nem efeito borrado)."""
    grad = Image.new("L", (1, H))
    for yy in range(H):
        t = max(0, (yy - H * 0.28) / (H * 0.72))
        grad.putpixel((0, yy), int(225 * min(1, t * 2.4)))
    sombra = Image.new("RGBA", (W, H), marca.cor("fundo") + (0,))
    sombra.putalpha(grad.resize((W, H)))
    return sombra


def camada_texto(marca: Marca, frase: Frase, lay: Layout = LAYOUT, com_logo: bool = False) -> tuple[Image.Image, dict]:
    """Camada transparente com o texto dos cortes: barra azul curta e frase com destaque. A logo no topo só com `com_logo`."""
    cam = Image.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 0)), _sombra(marca))
    dr = ImageDraw.Draw(cam)
    fonte = marca.fonte("titulo", lay.corpo)
    largura = W - 2 * lay.margem - 6
    linhas = quebra(dr, fichas(frase), fonte, largura)
    fim = int(H * lay.fim_texto)
    y0 = fim - len(linhas) * lay.entre_linhas
    dr.rectangle((lay.margem, y0 - 46, lay.margem + 90, y0 - 40), fill=_cor(marca, "neon_azul", "primaria"))
    _escrever(dr, lay.margem, y0, linhas, fonte, lay.entre_linhas, marca)
    if com_logo:
        cam.alpha_composite(_logo(marca, lay.logo_tam), (lay.logo_esq, lay.logo_topo))
    return cam, {"fim_texto": fim, "ficha_larga": largura_maxima(dr, fichas(frase), fonte), "largura_util": largura}


def _escrever(dr, x, y, linhas, fonte, entre, marca: Marca) -> int:
    branco, destaque = marca.cor("texto"), marca.cor("destaque")
    for linha in linhas:
        cx = x
        for t, dest in linha:
            dr.text((cx, y), t, font=fonte, fill=destaque if dest else branco)
            cx += dr.textlength(t + " ", font=fonte)
        y += entre
    return y


def cartela_final(marca: Marca, c: dict, lay: Layout = LAYOUT) -> tuple[Image.Image, dict]:
    """Cartela de fechamento: marinho com brilho azul, número grande e chamada. Tudo da marca."""
    fundo, branco = marca.cor("fundo"), marca.cor("texto")
    vermelho, cinza = marca.cor("destaque"), marca.cor("texto_suave")
    neon, ouro = _cor(marca, "neon_azul", "primaria"), _cor(marca, "ouro", "destaque")
    brilho_cor = _misturar(fundo, marca.cor("primaria"), 0.42)
    img = Image.new("RGB", (W, H), fundo)
    brilho = Image.new("RGB", (W, H), fundo)
    ImageDraw.Draw(brilho).ellipse((W - 520, -420, W + 420, 520), fill=brilho_cor)
    img = Image.blend(img, brilho.filter(ImageFilter.GaussianBlur(220)), 0.9)
    cam = img.convert("RGBA")
    dr = ImageDraw.Draw(cam)
    cam.alpha_composite(_logo(marca, 110), (lay.margem, lay.logo_topo))
    fm = marca.fonte("etiqueta", 30)
    dr.text((W - lay.margem - dr.textlength(c["meta"], font=fm), 250), c["meta"], font=fm, fill=cinza)
    y = 580
    dr.rectangle((lay.margem, y, lay.margem + 90, y + 6), fill=neon)
    dr.text((lay.margem, y + 30), c["etiqueta"], font=fm, fill=ouro)
    ft = marca.fonte("titulo", 150)
    titulo = frase_de(c["titulo"])
    linhas = []
    for bloco in titulo.texto.split("\n"):  # quebra de linha escrita vale (o número grande fica sozinho, quando necessário)
        parte = Frase(bloco, titulo.destaque if titulo.destaque and titulo.destaque in bloco else None)
        linhas += quebra(dr, fichas(parte), ft, W - 66 - lay.margem)
    y = _escrever(dr, 66, y + 100, linhas, ft, 162, marca)
    fr = marca.fonte("texto", 50)
    y = y + 30
    for linha in quebra_com_linhas(dr, c["subtitulo"], fr, W - 2 * lay.margem):
        dr.text((lay.margem, y), linha, font=fr, fill=cinza)
        y += 66
    fc = marca.fonte("etiqueta", 46)
    linhas_ch = quebra_com_linhas(dr, c["chamada"], fc, W - 124 - lay.margem)
    dr.rectangle((lay.margem, y + 84, lay.margem + 34, y + 90), fill=vermelho)
    yc = y + 62
    for linha in linhas_ch:
        dr.text((124, yc), linha, font=fc, fill=branco)
        yc += 62
    fim_texto = yc - 62 + 46
    dr.line((lay.margem, 1170, W - lay.margem, 1170), fill=_misturar(fundo, cinza, 0.18), width=2)
    rodape = f"{marca.nome.upper()} · {marca.instagram}".strip(" ·")
    dr.text((lay.margem, 1195), rodape, font=marca.fonte("etiqueta", 28), fill=cinza)
    return cam.convert("RGB"), {"fim_texto": fim_texto}


# ---------------------------------------------------------------- ffmpeg

def _roda(args: list[str]) -> None:
    r = subprocess.run([FFMPEG, "-y", "-loglevel", "error"] + args, capture_output=True, text=True)
    if r.returncode != 0:
        raise ErroPedido("Não deu para montar o vídeo agora. Tente de novo.\n[ffmpeg] " + r.stderr[-600:])


def medir(caminho: Path) -> dict:
    r = subprocess.run(
        [FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(caminho)],
        capture_output=True, text=True, check=True,
    )
    d = json.loads(r.stdout)
    s = d["streams"][0]
    n, den = s["r_frame_rate"].split("/")
    return {"largura": int(s["width"]), "altura": int(s["height"]), "fps": int(n) / int(den), "duracao": float(d["format"]["duration"])}


def _clip(i: int, foto: Path, camada: Path, frames: int, trabalho: Path, lay: Layout) -> Path:
    zw, zh = int(W * 1.6), int(H * 1.6)
    src = trabalho / f"foto{i:02d}.jpg"
    capa_916(abrir_foto(foto), zw, zh).save(src, quality=95)
    zp = (f"zoompan=z='1+{lay.zoom_fim - 1:g}*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},"
          f"eq=saturation={lay.saturacao:g}:contrast={lay.contraste:g},format=yuv420p")
    saida = trabalho / f"clip{i:02d}.mp4"
    _roda(["-i", str(src), "-i", str(camada), "-filter_complex", f"[0:v]{zp}[b];[b][1:v]overlay=0:0,format=yuv420p",
           "-frames:v", str(frames), "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-r", str(FPS), "-pix_fmt", "yuv420p", str(saida)])
    return saida


def gerar(pedido: Pedido, pasta_fotos: Path, saida: Path, ensaio: bool = False, log=lambda m: None) -> dict:
    """Monta o vídeo. Devolve {"ok": True, "arquivos": {...}, "conferencia": [...], ...} ou {"ok": False, "erro": "frase curta"}.

    ensaio: só para a equipe testar com foto que mostra anunciante sem autorização. O arquivo sai com "-ENSAIO" no nome
    e a conferência lembra de não postar. A tela nunca liga isto.
    """
    t0 = time.time()
    lay = LAYOUT
    marca = carregar(pedido.marca)
    for f in pedido.fotos:
        if not (pasta_fotos / f["arquivo"]).is_file():
            raise ErroPedido(f"A foto {f['arquivo']} não chegou ao Estúdio. Escolha de novo.")

    # camadas de texto (uma por texto) e cartela
    gancho_img, geo = camada_texto(marca, pedido.gancho, lay, pedido.logo_nas_cenas)
    camadas = {"gancho": gancho_img}
    fim_cortes = geo["fim_texto"]
    larga = geo["ficha_larga"]
    for k, t in enumerate(pedido.textos):
        camadas[k], g = camada_texto(marca, t, lay, pedido.logo_nas_cenas)
        larga = max(larga, g["ficha_larga"])
    cartela_img, geo_c = cartela_final(marca, pedido.cartela, lay)

    textos_todos = [pedido.gancho.texto] + [t.texto for t in pedido.textos] + [
        pedido.cartela["titulo"]["texto"], pedido.cartela["subtitulo"], pedido.cartela["chamada"], pedido.cartela["etiqueta"], pedido.cartela["meta"]]
    conferencia = conf.conferir_pedido(
        marca, textos_todos, pedido.fotos,
        {"fim_texto_cortes": fim_cortes, "fim_texto_cartela": geo_c["fim_texto"],
         "topo_logo_cenas": lay.logo_topo if pedido.logo_nas_cenas else None, "topo_logo_cartela": lay.logo_topo,
         "ficha_mais_larga": larga, "largura_util": geo["largura_util"]},
        H, ensaio=ensaio)
    if conf.tem_erro(conferencia):
        primeiro = next(a["texto"] for a in conferencia if a["nivel"] == "erro")
        return {"ok": False, "erro": primeiro, "conferencia": conferencia}

    n = len(pedido.fotos)
    quadros = [round(pedido.duracao_gancho * FPS)] + [round(pedido.duracao_corte * FPS)] * (n - 1)
    quadros_cartela = round(pedido.duracao_cartela * FPS)
    esperado = {"largura": W, "altura": H, "fps": FPS, "duracao": (sum(quadros) + quadros_cartela) / FPS}

    saida.mkdir(parents=True, exist_ok=True)
    sufixo = "-ENSAIO" if ensaio else ""
    trabalho = Path(tempfile.mkdtemp(prefix="estudio-"))
    try:
        log("camadas de texto prontas")
        arq_camadas: dict = {}
        for chave, img in camadas.items():
            p = trabalho / f"camada-{chave}.png"
            img.save(p)
            arq_camadas[chave] = p

        def tarefa(i):
            if i == 0:
                camada = arq_camadas["gancho"]
            else:
                camada = arq_camadas[min((i - 1) // 2, len(pedido.textos) - 1)]
            return _clip(i, pasta_fotos / pedido.fotos[i]["arquivo"], camada, quadros[i], trabalho, lay)

        with ThreadPoolExecutor(max_workers=max(1, min(4, os.cpu_count() or 1))) as pool:
            clips = list(pool.map(tarefa, range(n)))
        log(f"{n} cortes montados")

        cartela_png = trabalho / "cartela.png"
        cartela_img.save(cartela_png)
        fim_mp4 = trabalho / "fim.mp4"
        _roda(["-loop", "1", "-i", str(cartela_png), "-vf", "format=yuv420p,fade=t=in:st=0:d=0.25", "-frames:v", str(quadros_cartela),
               "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-r", str(FPS), "-pix_fmt", "yuv420p", str(fim_mp4)])
        clips.append(fim_mp4)

        lista = trabalho / "lista.txt"
        lista.write_text("".join(f"file '{p}'\n" for p in clips), encoding="utf-8")
        video = saida / f"video{sufixo}.mp4"
        # sem corte de áudio de verdade: trilha de silêncio (redes aceitam melhor arquivo com áudio); o áudio em alta entra ao postar
        _roda(["-f", "concat", "-safe", "0", "-i", str(lista), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
               "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(video)])
        medidas = medir(video)
        if abs(medidas["duracao"] - esperado["duracao"]) > 0.15:  # a emenda sem recodificar saiu torta: recodifica
            log("duração fora do esperado, recodificando a emenda")
            _roda(["-f", "concat", "-safe", "0", "-i", str(lista), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
                   "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(video)])
            medidas = medir(video)
        log("vídeo pronto")

        previa = saida / f"previa{sufixo}.mp4"
        _roda(["-i", str(video), "-vf", "scale=720:1280", "-c:v", "libx264", "-crf", "27", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart", str(previa)])
        capa = saida / f"capa{sufixo}.jpg"
        _roda(["-ss", "1.3", "-i", str(video), "-frames:v", "1", "-q:v", "2", str(capa)])
    finally:
        shutil.rmtree(trabalho, ignore_errors=True)

    conferencia += conf.conferir_saida(medidas, esperado)
    relatorio = {
        "ok": not conf.tem_erro(conferencia),
        "marca": marca.slug,
        "ensaio": ensaio,
        "fotos": n,
        "duracao_s": round(medidas["duracao"], 2),
        "resolucao": f"{medidas['largura']}x{medidas['altura']}",
        "fps": medidas["fps"],
        "tamanho_mb": round(video.stat().st_size / 1e6, 1),
        "tempo_geracao_s": round(time.time() - t0, 1),
        "arquivos": {"video": video.name, "previa": previa.name, "capa": capa.name},
        "conferencia": conferencia,
    }
    (saida / f"relatorio{sufixo}.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
    return relatorio
