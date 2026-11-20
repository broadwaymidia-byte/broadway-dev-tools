"""Avalia dimensões, nitidez e brilho de imagens."""
from PIL import Image, ImageFilter, ImageOps, ImageEnhance, ImageStat



def nitidez(im):
    """Variância do Laplaciano numa versão de 800px: < 60 costuma ser foto tremida/desfocada."""
    g = ImageOps.grayscale(im)
    g.thumbnail((800, 800))
    lap = g.filter(ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], 1, 128))
    return ImageStat.Stat(lap).var[0]


def avaliar(caminho, alvo=(1080, 1350), papel="fundo"):
    """Devolve (avisos, dados) sobre uma foto para o uso pretendido."""
    im = ImageOps.exif_transpose(Image.open(caminho))
    w, h = im.size
    avisos = []
    if papel == "fundo":
        escala = max(alvo[0] / w, alvo[1] / h)
    else:  # produto ocupa ~60% da largura
        escala = (alvo[0] * 0.6) / w
    if escala > 1.35:
        avisos.append(f"Foto pequena ({w}×{h}px): vai ser ampliada {escala:.1f}x e perder nitidez. Peça a original (WhatsApp como documento) ou gere na IA.")
    n = nitidez(im.convert("RGB"))
    if n < 60:
        avisos.append(f"Foto parece desfocada/tremida (nitidez {n:.0f}). Rode 'tratar' ou troque a foto.")
    lum = ImageStat.Stat(ImageOps.grayscale(im)).mean[0]
    if lum < 55:
        avisos.append("Foto escura demais. Rode 'tratar' ou use outra.")
    return avisos, {"largura": w, "altura": h, "nitidez": round(n), "brilho": round(lum)}

