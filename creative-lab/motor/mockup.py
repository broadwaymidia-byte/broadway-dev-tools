"""Mockups de aprovação: artes dentro do celular (feed, carrossel, story, anúncio) + prancha com tudo."""
import html
import unicodedata
from pathlib import Path

ICONES = {
    "coracao": '<svg viewBox="0 0 24 24"><path d="M12 21s-7.5-4.6-9.6-9.2C.9 8.4 3 4.5 6.8 4.5c2.2 0 3.7 1.3 5.2 3.1 1.5-1.8 3-3.1 5.2-3.1 3.8 0 5.9 3.9 4.4 7.3C19.5 16.4 12 21 12 21z" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"/></svg>',
    "comentario": '<svg viewBox="0 0 24 24"><path d="M20.6 16.2A9 9 0 1 0 17 19.9L21 21l-.4-4.8z" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"/></svg>',
    "enviar": '<svg viewBox="0 0 24 24"><path d="M21.5 3 10 13.5M21.5 3l-7 18-4.5-7.5L2.5 9z" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"/></svg>',
    "salvar": '<svg viewBox="0 0 24 24"><path d="M19 21l-7-5-7 5V4.5A1.5 1.5 0 0 1 6.5 3h11A1.5 1.5 0 0 1 19 4.5z" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"/></svg>',
    "seta": '<svg viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>',
    "mais": '<svg viewBox="0 0 24 24"><circle cx="5" cy="12" r="1.7"/><circle cx="12" cy="12" r="1.7"/><circle cx="19" cy="12" r="1.7"/></svg>',
}

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;font-family:system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.palco{width:1080px;padding:90px 0 100px;display:flex;flex-direction:column;align-items:center;gap:40px;background:var(--palco)}
.rotulo{font-size:26px;font-weight:700;letter-spacing:.24em;text-transform:uppercase;color:var(--rotulo)}
.cel{width:760px;border-radius:92px;background:#0d0d0f;padding:22px;box-shadow:0 60px 120px rgba(0,0,0,.35),inset 0 0 0 3px #2b2b30}
.tela{border-radius:72px;overflow:hidden;background:#fff;position:relative;width:716px}
.status{height:78px;display:flex;align-items:center;justify-content:space-between;padding:0 54px;font-weight:700;font-size:26px;color:#111}
.status .ilha{width:190px;height:52px;border-radius:30px;background:#0d0d0f}
.status .dir{display:flex;gap:10px;align-items:center}
.bat{width:44px;height:22px;border:2.5px solid #111;border-radius:7px;position:relative}
.bat::after{content:"";position:absolute;inset:3px 8px 3px 3px;background:#111;border-radius:3px}
.barra{height:70px;display:flex;align-items:center;padding:0 26px;gap:18px;border-bottom:1px solid #eee;font-weight:800;font-size:28px;color:#111}
.cab{display:flex;align-items:center;gap:16px;padding:18px 22px}
.av{width:62px;height:62px;border-radius:50%;background:#fff center/contain no-repeat;border:2px solid #e3e3e3}
.cab b{font-size:24px;color:#111;display:block}
.cab small{font-size:20px;color:#666}
.cab .mais{margin-left:auto;width:34px;color:#111;fill:#111}
.midia{position:relative;width:716px}
.midia img{width:100%;display:block}
.dots{display:flex;gap:9px;justify-content:center;padding:16px 0 4px}
.dots i{width:11px;height:11px;border-radius:50%;background:#c9c9c9}
.dots i.on{background:#3897f0}
.contador{position:absolute;right:22px;top:22px;background:rgba(0,0,0,.6);color:#fff;font-size:22px;font-weight:700;padding:8px 16px;border-radius:30px}
.acoes{display:flex;gap:26px;padding:14px 24px;color:#111}
.acoes svg{width:46px;height:46px}
.acoes .salvar{margin-left:auto}
.leg{padding:0 24px 30px;font-size:23px;line-height:1.4;color:#111}
.leg .cinza{color:#8e8e8e}
.ctabar{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:18px 24px;background:#f2f4f7;color:#111;border-bottom:1px solid #e6e6e6}
.ctabar .ad-txt{display:flex;flex-direction:column;min-width:0}
.ctabar .ad-tit{font-weight:700;font-size:23px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ctabar .ad-desc{font-size:20px;color:#666;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ctabar .ad-bt{flex:none;background:#e4e6eb;border-radius:12px;padding:14px 22px;font-weight:700;font-size:22px;white-space:nowrap}
.ctabar svg{width:30px;height:30px}
.story{position:relative;width:716px;height:1273px;background:#000}
.story img.art{width:100%;height:100%;object-fit:cover;display:block}
.story .sombra-topo{position:absolute;left:0;right:0;top:0;height:190px;background:linear-gradient(rgba(0,0,0,.45),rgba(0,0,0,0))}
.story .sombra-base{position:absolute;left:0;right:0;bottom:0;height:200px;background:linear-gradient(rgba(0,0,0,0),rgba(0,0,0,.45))}
.story .prog{position:absolute;top:20px;left:18px;right:18px;display:flex;gap:6px}
.story .prog i{flex:1;height:5px;border-radius:3px;background:rgba(255,255,255,.45)}
.story .prog i.on{background:#fff}
.story .scab{position:absolute;top:44px;left:22px;right:22px;display:flex;align-items:center;gap:14px;color:#fff;text-shadow:0 1px 6px rgba(0,0,0,.5)}
.story .scab .av{width:58px;height:58px;border-color:rgba(255,255,255,.8)}
.story .scab b{font-size:23px}
.story .scab small{font-size:19px;opacity:.9}
.story .base{position:absolute;left:22px;right:22px;bottom:30px;display:flex;align-items:center;gap:18px;color:#fff}
.story .base .campo{flex:1;height:78px;border:2px solid rgba(255,255,255,.8);border-radius:40px;display:flex;align-items:center;padding:0 30px;font-size:24px}
.story .base svg{width:48px;height:48px}
.story .adcta{position:absolute;left:50%;bottom:44px;transform:translateX(-50%);white-space:nowrap;background:#fff;color:#111;font-weight:800;font-size:26px;padding:20px 44px;border-radius:40px;display:flex;gap:10px;align-items:center}
.story .adcta svg{width:28px;height:28px}
"""


def _handle(marca):
    h = marca.get("instagram", "")
    if h.startswith("@"):
        return h.lstrip("@")
    base = unicodedata.normalize("NFKD", marca["nome"]).encode("ascii", "ignore").decode()
    return "".join(ch for ch in base.lower() if ch.isalnum())


def _svg(nome, cls=""):
    return f'<span class="{cls}" style="display:inline-flex">{ICONES[nome]}</span>'


def _status():
    return ('<div class="status"><span>9:41</span><span class="ilha"></span>'
            '<span class="dir"><span>●●●</span><span class="bat"></span></span></div>')


def _pagina(corpo, marca):
    c = marca["cores"]
    escuro = c["fundo"].lower() in ("#000000", "#070708", "#161616", "#1c1c1c", "#12016f", "#063a62")
    palco = f"linear-gradient(160deg,{c['fundo2']},{c['fundo']})" if escuro else "linear-gradient(160deg,#f4f1ec,#e6e1d8)"
    rot = "rgba(255,255,255,.75)" if escuro else "rgba(0,0,0,.55)"
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>:root{{--palco:{palco};--rotulo:{rot}}}{CSS}</style>"
            f"</head><body>{corpo}</body></html>")


def _legenda_curta(marca, legenda):
    h = _handle(marca)
    primeira = (legenda or "").strip().split("\n")[0]
    if len(primeira) > 110:
        primeira = primeira[:110].rsplit(" ", 1)[0]
    return f'<b>{html.escape(h.lstrip("@"))}</b> {html.escape(primeira)} <span class="cinza">… mais</span>'


def _feed(marca, arte, total, legenda, anuncio):
    h = _handle(marca)
    logo = (Path(__file__).resolve().parent.parent / "marcas" / marca["slug"] / marca["logo"]["arquivo"]).as_uri()
    sub = "Patrocinado" if anuncio else marca.get("cidade", "").split("—")[0].strip()
    dots = ""
    cont = ""
    if total > 1:
        dots = '<div class="dots">' + "".join(f'<i class="{"on" if i == 0 else ""}"></i>' for i in range(min(total, 10))) + "</div>"
    cta = ""
    if anuncio:
        cta = (f'<div class="ctabar"><span class="ad-txt"><span class="ad-tit">{html.escape(anuncio.get("titulo", ""))}</span>'
               f'<span class="ad-desc">{html.escape(anuncio.get("descricao", ""))}</span></span>'
               f'<span class="ad-bt">{html.escape(anuncio.get("botao", "Saiba mais"))}</span></div>')
    return f"""<div class="cel"><div class="tela">{_status()}
      {'' if anuncio else '<div class="barra">‹&nbsp;&nbsp;Publicações</div>'}
      <div class="cab"><span class="av" style="background-image:url('{logo}')"></span><span><b>{html.escape(h)}</b><small>{html.escape(sub)}</small></span>{_svg('mais','mais')}</div>
      <div class="midia"><img src="{arte.as_uri()}">{cont}</div>{cta}{dots}
      <div class="acoes">{_svg('coracao')}{_svg('comentario')}{_svg('enviar')}{_svg('salvar','salvar')}</div>
      <div class="leg">{_legenda_curta(marca, anuncio.get('texto') if anuncio else legenda)}</div>
    </div></div>"""


def _story(marca, arte, total, anuncio):
    h = _handle(marca)
    logo = (Path(__file__).resolve().parent.parent / "marcas" / marca["slug"] / marca["logo"]["arquivo"]).as_uri()
    prog = '<div class="prog">' + "".join(f'<i class="{"on" if i == 0 else ""}"></i>' for i in range(max(total, 1))) + "</div>"
    sub = "Patrocinado" if anuncio else "2 h"
    if anuncio:
        base = f'<div class="adcta">{html.escape(anuncio.get("botao", "Saiba mais"))}{ICONES["seta"]}</div>'
    else:
        base = f'<div class="base"><span class="campo">Enviar mensagem</span>{_svg("coracao")}{_svg("enviar")}</div>'
    return f"""<div class="cel"><div class="tela"><div class="story"><img class="art" src="{arte.as_uri()}"><span class="sombra-topo"></span><span class="sombra-base"></span>{prog}
      <div class="scab"><span class="av" style="background-image:url('{logo}')"></span><span><b>{html.escape(h)}</b> <small>{sub}</small></span></div>
      {base}</div></div></div>"""


def _prancha(marca, artes, fmt, nome, legenda, rotulos=None, titulo=None):
    n = len(artes)
    cols = 1 if n == 1 else 2 if n in (2, 4) else 3
    larg = int((1080 - 120 - (cols - 1) * 30) / cols)
    itens = "".join(
        f'<figure style="width:{larg}px"><img src="{a.as_uri()}" style="width:100%;display:block;border-radius:14px;box-shadow:0 18px 40px rgba(0,0,0,.25)">'
        f'<figcaption style="margin-top:12px;font-size:22px;font-weight:700;color:var(--rotulo)">{(rotulos[i-1] if rotulos else f"{i:02d}")}</figcaption></figure>'
        for i, a in enumerate(artes, 1))
    leg = html.escape(legenda or "").replace("\n", "<br>")
    bloco_leg = (f'<div style="width:960px;background:rgba(255,255,255,.92);color:#222;border-radius:18px;padding:34px 40px;font-size:22px;line-height:1.5">'
                 f'<div style="font-weight:800;letter-spacing:.2em;font-size:18px;margin-bottom:12px;color:#777">LEGENDA</div>{leg}</div>') if legenda else ""
    corpo = f"""<div class="palco" style="padding:80px 60px 90px">
      <div class="rotulo">{html.escape(titulo or 'Aprovação · ' + marca['nome'])}</div>
      <div style="display:flex;flex-wrap:wrap;gap:30px;justify-content:center">{itens}</div>{bloco_leg}</div>"""
    return _pagina(corpo, marca)


def _shot(nav, doc, destino):
    tmp = destino.with_suffix(".html")
    tmp.write_text(doc, encoding="utf-8")
    pg = nav.new_page(viewport={"width": 1080, "height": 800}, device_scale_factor=1)
    pg.goto(tmp.as_uri())
    pg.wait_for_load_state("networkidle")
    pg.screenshot(path=str(destino), full_page=True)
    pg.close()
    tmp.unlink()
    return destino


def gerar(nav, marca, artes, fmt, saida, nome, legenda="", anuncios=None, tipo="organico", variacoes=False):
    saida = Path(saida)
    feitos = []
    total = len(artes)
    anuncios = (anuncios or []) if tipo == "anuncio" else []
    if variacoes:
        # cada arte é uma peça independente (teste A/B): um mockup por variação + prancha comparativa
        mks = []
        for k, arte in enumerate(artes):
            an = anuncios[k] if k < len(anuncios) else (anuncios[0] if anuncios else None)
            letra = chr(65 + k)
            if fmt == "story":
                corpo = f'<div class="palco"><div class="rotulo">Variação {letra} · {"Anúncio · Stories" if an else "Stories"}</div>{_story(marca, arte, 1, an)}</div>'
                mks.append(_shot(nav, _pagina(corpo, marca), saida / f"{nome}-{letra.lower()}-mockup-story.png"))
            else:
                corpo = f'<div class="palco"><div class="rotulo">Variação {letra} · {"Anúncio · Feed" if an else "Feed"}</div>{_feed(marca, arte, 1, legenda, an)}</div>'
                mks.append(_shot(nav, _pagina(corpo, marca), saida / f"{nome}-{letra.lower()}-mockup-feed.png"))
        feitos += mks
        if total > 1:
            rot = [f"Variação {chr(65 + k)}" for k in range(total)]
            feitos.append(_shot(nav, _prancha(marca, mks, fmt, nome, "", rot, f"Teste A/B · {marca['nome']} · {fmt}"), saida / f"{nome}-comparativo.png"))
        return feitos
    anuncio = anuncios[0] if anuncios else None
    if fmt == "story":
        corpo = f'<div class="palco"><div class="rotulo">{"Anúncio · Stories" if anuncio else "Stories"}</div>{_story(marca, artes[0], total, anuncio)}</div>'
        feitos.append(_shot(nav, _pagina(corpo, marca), saida / f"{nome}-mockup-story.png"))
    else:
        rot = "Anúncio · Feed" if anuncio else ("Carrossel · Feed" if total > 1 else "Post · Feed")
        corpo = f'<div class="palco"><div class="rotulo">{rot}</div>{_feed(marca, artes[0], total, legenda, anuncio)}</div>'
        feitos.append(_shot(nav, _pagina(corpo, marca), saida / f"{nome}-mockup-feed.png"))
    if total > 1:
        feitos.append(_shot(nav, _prancha(marca, artes, fmt, nome, legenda), saida / f"{nome}-prancha.png"))
    return feitos
