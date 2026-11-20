"""Renderiza peças, confere legendas e lista perfis de marca."""
import json, os, re, sys, html, base64, shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MARCAS = RAIZ / "marcas"
FONTES = RAIZ / "fontes"
MOTOR = RAIZ / "motor"

FORMATOS = {"feed": (1080, 1350), "quadrado": (1080, 1080), "story": (1080, 1920), "retrato": (1080, 1440)}
# zonas seguras (topo, direita, base, esquerda) — texto e logo precisam ficar dentro
ZONAS = {
    "feed": (56, 70, 56, 70), "quadrado": (56, 70, 56, 70), "retrato": (56, 70, 56, 70),
    "story": (250, 70, 340, 70),   # Stories: 14% topo / ~18% base (interface do Instagram)
    "reels": (250, 70, 672, 70),   # Reels/anúncio em Reels: base 35% coberta pela interface
}
MIN_FONTE = {"titulo": 44, "texto": 28, "etiqueta": 20, "lista": 28, "cta": 24, "nota": 18, "handle": 18}
FAMILIA_PASTA = {"Montserrat": "montserrat", "Poppins": "poppins", "Fredoka": "fredoka", "Nunito": "nunito",
                 "Nunito Sans": "nunito-sans", "Gloock": "gloock", "Lora": "lora", "Anton": "anton",
                 "Cormorant Garamond": "cormorant-garamond", "Instrument Serif": "instrument-serif", "Syne": "syne", "Outfit": "outfit", "Quicksand": "quicksand", "Plus Jakarta Sans": "plus-jakarta-sans", "DM Sans": "dm-sans", "Baloo 2": "baloo-2", "Caveat": "caveat", "Archivo Black": "archivo-black", "JetBrains Mono": "jetbrains-mono", "Inter": "inter"}


# ---------------------------------------------------------------- utilidades
def carregar_marca(slug):
    if not re.fullmatch(r"[a-z0-9-]+", slug):
        raise SystemExit("Identificador de marca inválido.")
    p = MARCAS / slug / "marca.json"
    if not p.exists():
        disp = ", ".join(sorted(x.name for x in MARCAS.iterdir() if (x / "marca.json").exists()))
        sys.exit(f"ERRO: marca '{slug}' não existe. Marcas: {disp}")
    return json.loads(p.read_text(encoding="utf-8"))


def fontes_css():
    regras = []
    for fam, pasta in FAMILIA_PASTA.items():
        d = FONTES / pasta
        if not d.exists():
            continue
        for f in sorted(d.glob("*.woff2")):
            m = re.search(r"-latin-(\d+)-(normal|italic)\.woff2$", f.name)
            if not m:
                continue
            regras.append(f"@font-face{{font-family:'{fam}';font-weight:{m.group(1)};font-style:{m.group(2)};"
                          f"src:url('{f.as_uri()}') format('woff2');font-display:block}}")
    return "\n".join(regras)


def esc(t):
    return html.escape(str(t), quote=True)


def marcar(texto):
    """*palavra* vira destaque; quebra de linha vira <br>."""
    t = esc(texto)
    t = re.sub(r"\*(.+?)\*", r'<em class="dest">\1</em>', t)
    return t.replace("\n", "<br>")


def uri(caminho, base):
    if not caminho:
        return None
    p = Path(caminho)
    if not p.is_absolute():
        p = (base / p).resolve()
    if not p.exists():
        raise FileNotFoundError(f"imagem não encontrada: {p}")
    return p.as_uri()


# ---------------------------------------------------------------- montagem HTML
def montar_html(marca, peca, formato, idx, total, base, zona_nome):
    w, h = FORMATOS[formato]
    z = ZONAS[zona_nome]
    c, fnt = marca["cores"], marca["fontes"]
    slug = marca["slug"]
    tipo = peca.get("tipo", "conteudo")
    vars_css = ";".join(f"--{k.replace('_','-')}:{v}" for k, v in c.items() if isinstance(v, str))
    tf, xf, ef = fnt["titulo"], fnt["texto"], fnt.get("etiqueta", fnt["texto"])
    vars_css += (f";--fonte-titulo:'{tf['familia']}';--peso-titulo:{tf.get('peso',700)};"
                 f"--estilo-titulo:{tf.get('estilo','normal')};--caixa-titulo:{'uppercase' if tf.get('caixa')=='alta' else 'none'};"
                 f"--fonte-texto:'{xf['familia']}';--peso-texto:{xf.get('peso',400)};"
                 f"--fonte-etiqueta:'{ef['familia']}';--peso-etiqueta:{ef.get('peso',700)};--esp-etiqueta:{ef.get('espacamento','0.1em')};"
                 f"--w:{w}px;--h:{h}px;--zt:{z[0]}px;--zd:{z[1]}px;--zb:{z[2]}px;--ze:{z[3]}px")

    logo_arq = marca["logo"]["arquivo"]
    if peca.get("logo_alternativo") and marca["logo"].get("alternativo"):
        logo_arq = marca["logo"]["alternativo"]
    logo = (MARCAS / slug / logo_arq).as_uri()
    img = uri(peca.get("imagem"), base)
    prod = uri(peca.get("produto"), base)
    modo = peca.get("imagem_modo", "fundo")
    foco = peca.get("foco", "50% 50%")

    partes = []
    antes, depois = uri(peca.get("antes"), base), uri(peca.get("depois"), base)
    if antes and depois:
        partes.append(f'<div class="bg ad"><figure class="ad-antes"><img class="foto" src="{antes}"><figcaption><span class="t" data-p="etiqueta">{esc(peca.get("rotulo_antes","Antes"))}</span></figcaption></figure>'
                      f'<figure class="ad-depois"><img class="foto" src="{depois}"><figcaption><span class="t" data-p="etiqueta">{esc(peca.get("rotulo_depois","Depois"))}</span></figcaption></figure></div>')
        img = "ad"
    elif img:
        partes.append(f'<div class="bg modo-{modo}"><img class="foto" src="{img}" style="object-position:{esc(foco)}"><div class="veu"></div></div>')
    else:
        partes.append('<div class="bg sem-foto"></div>')
    partes.append('<div class="deco d1"></div><div class="deco d2"></div><div class="deco d3"></div><div class="deco d4"></div>')
    if total > 1 and peca.get("numeracao", marca.get("numeracao", True)):
        partes.append(f'<span class="num t" data-p="nota">{idx:02d} / {total:02d}</span>')
    partes.append(f'<div class="topo"><img class="logo" src="{logo}" alt="logo"></div>')

    m = ['<div class="miolo"><div class="cartao">']
    if peca.get("etiqueta"):
        m.append(f'<div class="etiqueta"><span class="t" data-p="etiqueta">{marcar(peca["etiqueta"])}</span></div>')
    if peca.get("titulo"):
        linhas = peca["titulo"] if isinstance(peca["titulo"], list) else [peca["titulo"]]
        spans = "".join(f'<span class="ln ln{i+1}">{marcar(l)}</span>' for i, l in enumerate(linhas))
        m.append(f'<h1 class="titulo t" data-p="titulo">{spans}</h1>')
    if prod:
        m.append(f'<div class="produto-box"><img class="produto" src="{prod}"></div>')
    if peca.get("texto"):
        m.append(f'<div class="texto t" data-p="texto">{marcar(peca["texto"])}</div>')
    if peca.get("cores"):
        chips = "".join(f'<div class="chip"><div class="amostra" style="background:{esc(cc.get("hex","#ccc"))}"></div>'
                        f'<div class="chip-info"><b class="t" data-p="nota">{esc(cc.get("nome",""))}</b>'
                        f'<span class="t" data-p="nota">{esc(cc.get("ref",""))}</span></div></div>' for cc in peca["cores"])
        m.append(f'<div class="cartela n{len(peca["cores"])}">{chips}</div>')
    if peca.get("comparar"):
        cp = peca["comparar"]
        m.append('<div class="comparar">'
                 f'<div class="cmp cmp-erro"><i>✕</i><b class="t" data-p="etiqueta">{esc(cp.get("rotulo_erro","Erro comum"))}</b><span class="t" data-p="texto">{marcar(cp.get("erro",""))}</span></div>'
                 f'<div class="cmp cmp-acerto"><i>✓</i><b class="t" data-p="etiqueta">{esc(cp.get("rotulo_acerto","Jeito certo"))}</b><span class="t" data-p="texto">{marcar(cp.get("acerto",""))}</span></div>'
                 '</div>')
    if peca.get("itens"):
        lis = "".join(f'<li class="t" data-p="lista"><i></i><span>{marcar(x)}</span></li>' for x in peca["itens"])
        m.append(f'<ul class="lista">{lis}</ul>')
    if tipo == "oferta" or peca.get("preco"):
        o = ['<div class="oferta">']
        if peca.get("produto_nome"):
            o.append(f'<div class="p-nome t" data-p="texto">{marcar(peca["produto_nome"])}</div>')
        if peca.get("preco_de"):
            o.append(f'<div class="p-de t" data-p="nota">de <s>{esc(peca["preco_de"])}</s> por</div>')
        if peca.get("preco"):
            v = str(peca["preco"]).replace("R$", "").strip()
            inteiro, _, cent = v.partition(",")
            o.append(f'<div class="p-valor t" data-p="titulo"><small>R$</small>{esc(inteiro)}<sup>{("," + esc(cent)) if cent else ""}</sup></div>')
        if peca.get("condicao"):
            o.append(f'<div class="p-cond t" data-p="etiqueta">{marcar(peca["condicao"])}</div>')
        o.append("</div>")
        m.append("".join(o))
    if peca.get("cta"):
        m.append(f'<div class="cta"><span class="t" data-p="cta">{marcar(peca["cta"])}</span></div>')
    m.append("</div></div>")
    partes.append("".join(m))
    rod = []
    rodape = peca.get("rodape")
    if rodape is None and peca.get("contato", True) and marca.get("rodape_padrao"):
        rodape = marca["rodape_padrao"]
    if rodape:
        rod.append(f'<span class="rod-txt t" data-p="nota">{marcar(rodape)}</span>')
    handle = marca.get("instagram", "")
    if peca.get("mostrar_handle", True) and handle.startswith("@"):
        rod.append(f'<span class="handle t" data-p="handle">{esc(handle)}</span>')
    if marca.get("tagline") and peca.get("selo", marca.get("selo_sempre", False) or tipo in ("capa", "cta")):
        rod.append(f'<span class="selo t" data-p="nota">{esc(marca["tagline"])}</span>')
    partes.append(f'<div class="rodape">{"".join(rod)}</div>')

    _reserv = {"peca","bg","veu","foto","topo","logo","miolo","cartao","etiqueta","titulo","texto","lista","oferta","cta","rodape","handle","selo","num","d1","d2","d3","d4","ln","dest"}
    _col = set(str(peca.get("variante","")).split()) & _reserv
    if _col:
        raise SystemExit(f"ERRO: variante usa nome reservado do motor: {', '.join(sorted(_col))}. Renomeie a variante no estilo.css/marca.json.")
    classes = f"peca m-{slug} f-{formato} z-{zona_nome} t-{tipo} {'com-foto' if img else 'sem-foto'} {'com-produto' if prod else ''} {peca.get('variante','')}"
    base_css = (MOTOR / "base.css").read_text(encoding="utf-8")
    skin = (MARCAS / slug / "estilo.css")
    skin_css = skin.read_text(encoding="utf-8") if skin.exists() else ""
    skin_css = skin_css.replace("marca:", (MARCAS / slug).as_uri() + "/")  # url("marca:arquivo.jpg") = arquivo da pasta da marca
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>
{fontes_css()}
:root{{{vars_css}}}
{base_css}
{skin_css}
</style></head><body><div id="peca" class="{classes}">{''.join(partes)}</div></body></html>"""


# ---------------------------------------------------------------- conferência no navegador
JS_AJUSTE = r"""
async () => {
  await document.fonts.ready;
  const res = {erros: [], avisos: [], caixas: []};
  const peca = document.getElementById('peca');
  const W = peca.clientWidth, H = peca.clientHeight;
  const cs = getComputedStyle(document.documentElement);
  const Z = {t: parseFloat(cs.getPropertyValue('--zt')), d: parseFloat(cs.getPropertyValue('--zd')),
             b: parseFloat(cs.getPropertyValue('--zb')), e: parseFloat(cs.getPropertyValue('--ze'))};
  // 1) imagens carregadas
  for (const im of document.querySelectorAll('img')) {
    if (!im.complete || im.naturalWidth === 0) res.erros.push('Imagem não carregou: ' + (im.className || im.src.slice(-40)));
  }
  // 2) fontes carregadas
  const faltando = new Set();
  for (const el of document.querySelectorAll('.t, .t *')) {
    if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
    if (!el.getClientRects().length) continue;  // escondido (display:none) não conta
    const c = getComputedStyle(el); const fam = c.fontFamily.split(',')[0].replace(/["']/g,'').trim();
    if (!document.fonts.check(`${c.fontStyle} ${c.fontWeight} 16px "${fam}"`)) faltando.add(`${fam} ${c.fontWeight} ${c.fontStyle}`);
  }
  for (const f of faltando) res.erros.push('Fonte não carregou (a arte sairia com letra errada): ' + f);
  // 3) auto-ajuste: diminui fonte até caber (título, texto, lista)
  const miolo = peca.querySelector('.miolo');
  const cartao = peca.querySelector('.cartao');
  const cabe = () => [miolo, cartao].every(el => el.scrollHeight <= el.clientHeight + 6 && el.scrollWidth <= el.clientWidth + 8);
  const encolher = (sel, papel) => {
    const el = peca.querySelector(sel); if (!el) return;
    let fs = parseFloat(getComputedStyle(el).fontSize);
    const maxL = parseInt(getComputedStyle(el).getPropertyValue('--max-linhas')) || 99;
    const lh = () => parseFloat(getComputedStyle(el).lineHeight) || fs * 1.1;
    const linhas = () => Math.round(el.getBoundingClientRect().height / lh());
    let guard = 0;
    while ((!cabe() || linhas() > maxL || el.scrollWidth > el.clientWidth + 1) && fs > MIN[papel] && guard++ < 200) {
      fs -= 2; el.style.fontSize = fs + 'px';
    }
  };
  const MIN = __MIN__;
  encolher('.titulo', 'titulo'); encolher('.p-valor', 'titulo'); encolher('.texto', 'texto');
  for (const li of peca.querySelectorAll('.lista li')) { if (!cabe()) { let fs = parseFloat(getComputedStyle(li).fontSize); while (!cabe() && fs > MIN.lista) { fs -= 2; li.style.fontSize = fs + 'px'; } } }
  const nLinhas = el => { const r = document.createRange(); r.selectNodeContents(el);
    const q = [...r.getClientRects()].filter(x => x.width > 2); if (!q.length) return 0;
    const h = Math.max(...q.map(x => x.bottom)) - Math.min(...q.map(x => x.top));
    const c = getComputedStyle(el); const lh = parseFloat(c.lineHeight) || parseFloat(c.fontSize) * 1.2;
    return Math.round(h / lh); };
  const tt = peca.querySelector('.titulo');
  if (tt) { const maxT = parseInt(getComputedStyle(tt).getPropertyValue('--max-linhas')) || 4; const n = nLinhas(tt);
    if (n > maxT) res.erros.push(`Título com ${n} linhas na arte (máximo ${maxT}) — encurte o título; o detalhe vai no texto ou na legenda.`); }
  const tx2 = peca.querySelector('.texto');
  if (tx2) { const n = nLinhas(tx2); if (n > 4) res.erros.push(`Texto de apoio com ${n} linhas (máximo 4) — encurte; explicação longa vai na legenda ou em outro slide.`); }
  if (!cabe()) res.erros.push('Conteúdo não cabe no espaço da arte mesmo no tamanho mínimo de letra — encurte o texto ou divida em mais slides.');
  // 4) cada texto: estouro, fora da zona segura, tamanho mínimo
  const els = [...peca.querySelectorAll('.t')].filter(e => e.offsetParent !== null && e.textContent.trim());
  for (const el of els) {
    const r = el.getBoundingClientRect(); const papel = el.dataset.p || 'texto';
    const fs = parseFloat(getComputedStyle(el).fontSize);
    const nome = `"${el.textContent.trim().slice(0, 28)}"`;
    if (el.scrollWidth > el.clientWidth + 2) res.erros.push(`Texto cortado na lateral: ${nome}`);
    if (r.left < Z.e - 1 || r.right > W - Z.d + 1 || r.top < Z.t - 1 || r.bottom > H - Z.b + 1)
      res.erros.push(`Texto fora da área segura (pode ser cortado pelo Instagram): ${nome}`);
    if (fs < (MIN[papel] || 18) - 0.5) res.avisos.push(`Letra pequena (${Math.round(fs)}px) em ${nome}`);
    // contraste medido em cada pedaço de texto com cor própria (linha do título, palavra destacada...)
    const folhas = [el, ...el.querySelectorAll('*')].filter(n => [...n.childNodes].some(c => c.nodeType === 3 && c.textContent.trim()));
    for (const n of folhas) {
      const rr = n.getBoundingClientRect(); const cs2 = getComputedStyle(n); const f2 = parseFloat(cs2.fontSize);
      if (rr.width < 4 || rr.height < 4) continue;
      res.caixas.push({papel, texto: n.textContent.trim().slice(0, 40), x: rr.left, y: rr.top, w: rr.width, h: rr.height,
                       cor: ((/rgba\([^)]*,\s*0\)/.test(cs2.color) || cs2.color==='transparent') && /gradient/.test(cs2.backgroundImage) ? ((cs2.backgroundImage.match(/rgba?\([^)]*\)/g)||[cs2.color]).slice(-1)[0]) : cs2.color), fs: f2, grande: f2 >= 36 || (f2 >= 24 && parseInt(cs2.fontWeight) >= 700)});
    }
  }
  // 5) logo dentro da área segura
  const lg = peca.querySelector('.logo');
  if (lg) { const r = lg.getBoundingClientRect(); if (r.width < 60) res.erros.push('Logo pequeno demais.');
    if (r.left < Z.e - 1 || r.right > W - Z.d + 1 || r.top < Z.t - 1 || r.bottom > H - Z.b + 1) res.erros.push('Logo fora da área segura.'); }
  // 6) sobreposição entre textos
  const bx = els.map(e => [e, e.getBoundingClientRect()]);
  for (let i = 0; i < bx.length; i++) for (let j = i + 1; j < bx.length; j++) {
    const [a, ra] = bx[i], [b, rb] = bx[j];
    if (a.contains(b) || b.contains(a)) continue;
    const ix = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left);
    const iy = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
    if (ix > 4 && iy > 4) res.erros.push(`Textos encavalados: "${a.textContent.trim().slice(0,20)}" e "${b.textContent.trim().slice(0,20)}"`);
  }
  // 6b) enfeite (estrela, lua, coração, rabisco, turminha) encostando em texto — margem de 14px
  const textoRects = [];
  for (const el of els) { const rg = document.createRange(); rg.selectNodeContents(el);
    for (const q of rg.getClientRects()) if (q.width > 2 && q.height > 2) textoRects.push([el, q]); }
  for (const dc of peca.querySelectorAll('.deco.d2, .deco.d3, .deco.d4')) {
    const c = getComputedStyle(dc); if (c.display === 'none' || c.visibility === 'hidden' || parseFloat(c.opacity) === 0) continue;
    if (c.backgroundImage === 'none' && /rgba\([^)]*,\s*0\)|transparent/.test(c.backgroundColor)) continue;
    const r = dc.getBoundingClientRect(); if (r.width * r.height > W * H * 0.2) continue;   // forma grande de fundo não conta
    const m = 14;
    for (const [el, q] of textoRects) {
      const ix = Math.min(r.right, q.right + m) - Math.max(r.left, q.left - m);
      const iy = Math.min(r.bottom, q.bottom + m) - Math.max(r.top, q.top - m);
      if (ix > 0 && iy > 0) { res.erros.push(`Enfeite encostando no texto "${el.textContent.trim().slice(0,24)}" — afaste o enfeite.`); break; }
    }
  }
  // 7) palavra sozinha na última linha do título
  const t = peca.querySelector('.titulo');
  if (t) for (const ln of t.querySelectorAll('.ln')) {
    const rg = document.createRange(); rg.selectNodeContents(ln);
    const rects = [...rg.getClientRects()]; const tops = [...new Set(rects.map(r => Math.round(r.top)))];
    if (tops.length > 1) { const ult = rects.filter(r => Math.round(r.top) === tops[tops.length-1]).reduce((s, r) => s + r.width, 0);
      if (ult < ln.getBoundingClientRect().width * 0.22) res.avisos.push(`Palavra sozinha quebrando linha no título: "${ln.textContent.trim().slice(0,30)}" — ajuste a quebra.`); }
  }
  const tx = peca.querySelector('.texto');
  if (tx) { const rg = document.createRange(); rg.selectNodeContents(tx); const rects = [...rg.getClientRects()];
    const tops = [...new Set(rects.map(r => Math.round(r.top)))];
    if (tops.length > 1) { const ult = rects.filter(r => Math.round(r.top) === tops[tops.length-1]).reduce((s, r) => s + r.width, 0);
      if (ult < tx.getBoundingClientRect().width * 0.18) res.avisos.push('Palavra sozinha na última linha do texto de apoio — reescreva ou quebre a linha com \\n.'); } }
  return res;
}
"""


def luminancia(rgb):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contraste(a, b):
    la, lb = luminancia(a), luminancia(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def cor_css(s):
    n = [float(x) for x in re.findall(r"[\d.]+", s)]
    return tuple(int(x) for x in n[:3]) if len(n) >= 3 else (0, 0, 0)


def conferir_contraste(fundo_png, caixas):
    """Compara a cor de cada texto com o fundo real por baixo dele (foto incluída)."""
    from PIL import Image
    im = Image.open(fundo_png).convert("RGB")
    out = []
    for c in caixas:
        # recorta 15%/22% das bordas: cantos de pílulas e blobs não contam como fundo do texto
        dx, dy = c["w"] * 0.15, c["h"] * 0.22
        x0, y0 = max(0, int(c["x"] + dx)), max(0, int(c["y"] + dy))
        x1, y1 = min(im.width, int(c["x"] + c["w"] - dx)), min(im.height, int(c["y"] + c["h"] - dy))
        if x1 - x0 < 4 or y1 - y0 < 4:
            continue
        reg = im.crop((x0, y0, x1, y1)).resize((24, 12))
        px = list(reg.get_flattened_data()) if hasattr(reg, 'get_flattened_data') else list(reg.getdata())
        cor = cor_css(c["cor"])
        # pior caso: 20% dos pixels de fundo mais parecidos com o texto
        ratios = sorted(contraste(cor, p) for p in px)
        pior = ratios[len(ratios) // 10]
        minimo = 3.0 if c["grande"] else 4.5
        enorme = c.get("fs", 0) >= 90
        if pior < (1.5 if enorme else minimo * 0.72):
            out.append(("erro", f'Pouco contraste ({pior:.1f}:1) em "{c["texto"][:28]}" — fundo compete com o texto.'))
        elif pior < minimo:
            out.append(("aviso", f'Contraste baixo ({pior:.1f}:1) em "{c["texto"][:28]}".'))
    return out


# ---------------------------------------------------------------- conferência de texto
ACEITAS = {"dani", "cleanto", "carreta", "direct", "marmitex", "delivery", "stories", "story", "reels", "feed", "whatsapp", "instagram", "insta", "pix",
           "online", "link", "bio", "combo", "kit", "site", "app", "drive", "ok", "wi-fi", "wifi", "cashback", "black", "friday",
           "carrossel", "post", "posts", "hashtag", "hashtags", "zap", "uber", "ifood", "google", "youtube", "tiktok"}
_DIC = None


def ortografia(texto, marca):
    global _DIC
    try:
        if _DIC is None:
            from spylls.hunspell import Dictionary
            _DIC = Dictionary.from_files(str(MOTOR / "dicionario" / "pt_BR"))
    except Exception:
        return None
    limpo = re.sub(r"https?://\S+|www\.\S+|[@#][\wÀ-ÿ.]+|\S+\.com(\.br)?", " ", texto)
    extras = {w.lower() for w in re.findall(r"[A-Za-zÀ-ÿ]+", " ".join([marca["nome"], marca.get("instagram", "")] + marca.get("vocabulario", [])))}
    ruins = []
    for w in re.findall(r"[A-Za-zÀ-ÿ]+(?:-[A-Za-zÀ-ÿ]+)*", limpo):
        lw = w.lower()
        if len(w) < 3 or lw in ACEITAS or lw in extras or w.isupper() and len(w) <= 4:
            continue
        if not (_DIC.lookup(w) or _DIC.lookup(lw) or _DIC.lookup(lw.capitalize())):
            if w not in ruins:
                ruins.append(w)
    return ruins


def conferir_texto(marca, textos, onde="arte"):
    erros, avisos = [], []
    r = marca["regras"]
    junto = "\n".join(textos)
    baixo = junto.lower()
    for p in r.get("palavras_proibidas", []):
        if re.search(r"(?<!\w)" + re.escape(p.lower()) + r"(?!\w)", baixo):
            erros.append(f'Palavra proibida para {marca["nome"]}: "{p}"')
    tel = re.search(r"(\(?\d{2}\)?\s?)?9?\d{4}[-\s]?\d{4}", junto)
    if onde == "arte" and tel and not r.get("telefone_na_arte", True):
        erros.append(f'Telefone na arte ({tel.group(0)}) — {marca["nome"]} não usa telefone na arte.')
    if re.search(r"[^\S\n]{2,}", junto):
        avisos.append("Espaço duplo no texto.")
    for a, b in (("(", ")"), ("“", "”"), ("[", "]")):
        if junto.count(a) != junto.count(b):
            avisos.append(f"Parênteses/aspas sem fechar: {a}{b}")
    if re.search(r"\s[,.!?;:]", junto):
        avisos.append("Espaço antes de pontuação.")
    if re.search(r"a confirmar|xxxx|lorem|\?\?\?", baixo):
        erros.append("Tem dado marcado como 'a confirmar' ou placeholder no texto.")
    # ortografia (dicionário pt_BR do LibreOffice) — aviso, porque nomes próprios e gírias aparecem
    desconhecidas = ortografia(junto, marca)
    if desconhecidas is None:
        avisos.append("Corretor ortográfico indisponível (instale: pip install spylls) — revise a grafia manualmente.")
    elif desconhecidas:
        avisos.append("Confira a grafia destas palavras (fora do dicionário): " + ", ".join(desconhecidas[:20]))
    return erros, avisos


def conferir_legenda(marca, texto):
    erros, avisos = conferir_texto(marca, [texto], onde="legenda")
    r = marca["regras"]
    if not r.get("asteriscos_legenda", False) and "*" in texto:
        erros.append("Asterisco na legenda (o Instagram não faz negrito — aparece o asterisco).")
    # regra de legenda Broadway (motor/LEGENDA.md): curta, SPIN, sem hashtag
    if re.search(r"(^|\s)#\w", texto):
        erros.append("Hashtag na legenda: a Broadway não usa mais hashtag.")
    if len(texto) > 800:
        erros.append(f"Legenda com {len(texto)} caracteres: longa demais. A legenda é curta (até ~350 + assinatura).")
    elif len(texto) > 500:
        avisos.append(f"Legenda com {len(texto)} caracteres: encurte (até ~350 + assinatura), SPIN em 3 a 5 linhas.")
    primeira = texto.strip().split("\n")[0]
    if len(primeira) > 90:
        avisos.append("A primeira linha passa de 90 caracteres: o gancho some no 'mais'.")
    return erros, avisos


# ---------------------------------------------------------------- render
def render(pedido_path):
    from playwright.sync_api import sync_playwright
    pedido_path = Path(pedido_path).resolve()
    base = pedido_path.parent
    ped = json.loads(pedido_path.read_text(encoding="utf-8"))
    marca = carregar_marca(ped["marca"])
    formatos = ped.get("formatos") or [ped.get("formato", "feed")]
    zona_pedido = ped.get("zona")
    saida = Path(ped.get("saida") or (base / f"saida-{marca['slug']}")).resolve()
    saida.mkdir(parents=True, exist_ok=True)
    nome = ped.get("nome", marca["slug"])
    if not re.fullmatch(r"[a-z0-9-]+", nome):
        raise SystemExit("Nome de saída inválido.")
    pecas = ped["pecas"]
    relatorio = {"marca": marca["nome"], "erros": [], "avisos": [], "arquivos": []}

    # conferência de texto da arte inteira
    textos = []
    for p in pecas:
        for k in ("etiqueta", "texto", "cta", "rodape", "produto_nome", "condicao"):
            if p.get(k):
                textos.append(str(p[k]).replace("*", ""))
        for k in ("titulo", "itens"):
            v = p.get(k)
            if v:
                textos += [str(x).replace("*", "") for x in (v if isinstance(v, list) else [v])]
    e, a = conferir_texto(marca, textos)
    relatorio["erros"] += e
    relatorio["avisos"] += a
    import imagem as _img
    for i, p in enumerate(pecas, 1):
        for campo, papel in (("imagem", "fundo"), ("produto", "produto")):
            if p.get(campo):
                cam = Path(p[campo]) if Path(p[campo]).is_absolute() else base / p[campo]
                if cam.exists():
                    fmt0 = formatos[0] if formatos[0] in FORMATOS else "feed"
                    av, _ = _img.avaliar(cam, FORMATOS[fmt0], papel)
                    relatorio["avisos"] += [f"[peça {i} · {campo}] {x}" for x in av]
    anuncios = ped.get("anuncios") or ([ped["anuncio"]] if ped.get("anuncio") else [])
    for k, an in enumerate(anuncios):
        rot = f"Anúncio {chr(65 + k)}: " if len(anuncios) > 1 else "Anúncio: "
        e, a = conferir_legenda(marca, "\n".join(str(an.get(c, "")) for c in ("texto", "titulo", "descricao")))
        relatorio["erros"] += [rot + x for x in e]
        relatorio["avisos"] += [rot + x for x in a if "primeira linha" not in x]
        for campo, lim in (("texto", 125), ("titulo", 40), ("descricao", 30)):
            if len(str(an.get(campo, ""))) > lim:
                relatorio["avisos"].append(f"{rot}{campo} com {len(str(an[campo]))} caracteres (o Meta corta depois de ~{lim}).")
        if not an.get("botao"):
            relatorio["erros"].append(rot + "falta o botão (ex.: Enviar mensagem, Saiba mais, Pedir agora).")
    if not str(marca.get("instagram", "")).startswith("@"):
        relatorio["avisos"].append("O @ do Instagram desta marca está 'a confirmar' — o mockup mostra um @ provisório.")
    if ped.get("legenda"):
        e, a = conferir_legenda(marca, ped["legenda"])
        relatorio["erros"] += ["Legenda: " + x for x in e]
        relatorio["avisos"] += ["Legenda: " + x for x in a]
        (saida / f"{nome}-legenda.txt").write_text(ped["legenda"], encoding="utf-8")

    with sync_playwright() as pw:
        nav = pw.chromium.launch(executable_path=os.environ.get("LAB_CHROMIUM") or None)
        for fmt in formatos:
            if fmt not in FORMATOS:
                sys.exit(f"ERRO: formato '{fmt}' não existe. Use: {', '.join(FORMATOS)}")
            w, h = FORMATOS[fmt]
            zona = zona_pedido if (zona_pedido and fmt == "story") else fmt
            pg = nav.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            gerados = []
            variacoes = bool(ped.get("variacoes"))
            tema = ped.get("tema")
            if tema and tema not in marca.get("temas", {}):
                sys.exit(f"ERRO: tema '{tema}' não existe para {marca['nome']}. Temas: {', '.join(marca.get('temas', {})) or 'nenhum'}")
            ciclo = marca.get("temas", {}).get(tema) if tema else marca.get("alternancia")
            alterna = ped.get("alternar", True) and ciclo and (len(pecas) > 1 or tema) and not variacoes
            for i, peca in enumerate(pecas, 1):
                if variacoes and tema and "variante" not in peca:
                    peca = {**peca, "variante": ciclo[0]}
                if alterna and "variante" not in peca:
                    peca = {**peca, "variante": ciclo[(i - 1) % len(ciclo)]}
                if variacoes:
                    peca = {"numeracao": False, **peca}
                doc = montar_html(marca, peca, fmt, i, len(pecas), base, zona)
                tmp = saida / f".tmp-{i}.html"
                tmp.write_text(doc, encoding="utf-8")
                pg.goto(tmp.as_uri())
                pg.wait_for_load_state("networkidle")
                res = pg.evaluate(JS_AJUSTE.replace("__MIN__", json.dumps(MIN_FONTE)))
                sufixo = "" if len(formatos) == 1 else f"-{fmt}"
                marca_i = chr(96 + i) if variacoes else f"{i:02d}"
                arq = saida / f"{nome}{sufixo}-{marca_i}.png"
                pg.screenshot(path=str(arq), clip={"x": 0, "y": 0, "width": w, "height": h})
                # fundo sem texto para medir contraste
                pg.evaluate("() => { for (const e of document.querySelectorAll('.t, .t *')) { const c = getComputedStyle(e); if ((c.webkitBackgroundClip || c.backgroundClip) === 'text') e.style.visibility = 'hidden'; } }")
                pg.add_style_tag(content=".t,.t *,.t::first-line,.t::first-letter,.t::before,.t::after,.t *::before,.t *::after{color:transparent!important;text-shadow:none!important;-webkit-text-stroke:0!important}")
                fundo = saida / f".fundo-{i}.png"
                pg.screenshot(path=str(fundo), clip={"x": 0, "y": 0, "width": w, "height": h})
                for nivel, msg in conferir_contraste(fundo, res["caixas"]):
                    res["erros" if nivel == "erro" else "avisos"].append(msg)
                fundo.unlink()
                tmp.unlink()
                rot = f"[{fmt} {marca_i}]"
                relatorio["erros"] += [f"{rot} {x}" for x in res["erros"]]
                relatorio["avisos"] += [f"{rot} {x}" for x in res["avisos"]]
                relatorio["arquivos"].append(str(arq))
                gerados.append(arq)
            pg.close()
            # mockups
            if ped.get("mockup", True):
                import mockup
                tipo_mk = ped.get("mockup_tipo") or ("anuncio" if anuncios else "organico")
                mk = mockup.gerar(nav, marca, gerados, fmt, saida, f"{nome}{'' if len(formatos)==1 else '-'+fmt}",
                                  legenda=ped.get("legenda", ""), anuncios=anuncios, tipo=tipo_mk, variacoes=variacoes)
                relatorio["arquivos"] += [str(x) for x in mk]
        nav.close()

    relatorio["status"] = "REPROVADO — corrigir antes de mostrar" if relatorio["erros"] else "APROVADO na conferência automática"
    (saida / f"{nome}-conferencia.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n== {relatorio['status']} ==")
    for x in relatorio["erros"]:
        print("  ERRO  ", x)
    for x in relatorio["avisos"]:
        print("  aviso ", x)
    print("\nArquivos:")
    for x in relatorio["arquivos"]:
        print("  ", x)
    return 1 if relatorio["erros"] else 0


def listar():
    for d in sorted(MARCAS.iterdir()):
        if (d / "marca.json").exists():
            m = json.loads((d / "marca.json").read_text(encoding="utf-8"))
            print(f"- {d.name}: {m['nome']} {m.get('instagram','')}")
            for x in m.get("a_confirmar", []):
                print(f"    a confirmar: {x}")


if __name__ == "__main__":
    sys.path.insert(0, str(MOTOR))
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "render":
        sys.exit(render(sys.argv[2]))
    elif cmd == "legenda":
        m = carregar_marca(sys.argv[2])
        e, a = conferir_legenda(m, Path(sys.argv[3]).read_text(encoding="utf-8"))
        print("APROVADA" if not e else "REPROVADA")
        [print("  ERRO  ", x) for x in e]
        [print("  aviso ", x) for x in a]
        sys.exit(1 if e else 0)
    elif cmd == "marcas":
        listar()
    else:
        raise SystemExit("Use render, legenda ou marcas.")
