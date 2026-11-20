"""Frases com uma parte em destaque e quebra de linha para a tela do vídeo."""
from __future__ import annotations

import re
from dataclasses import dataclass

from PIL import ImageDraw, ImageFont


@dataclass(frozen=True)
class Frase:
    """O texto inteiro e, se houver, a parte que fica na cor de destaque da marca (um trecho do próprio texto)."""

    texto: str
    destaque: str | None = None

    def inteira(self) -> str:
        return self.texto


def frase_de(dado) -> Frase:
    """Aceita "texto" ou {"texto": "...", "destaque": "..."}."""
    if isinstance(dado, str):
        return Frase(dado.strip())
    texto = str(dado.get("texto", "")).strip()
    destaque = (dado.get("destaque") or "").strip() or None
    return Frase(texto, destaque)


def fichas(frase: Frase) -> list[tuple[str, bool]]:
    """Quebra a frase em palavras (ficha, em destaque?).

    Número e unidade ficam juntos numa ficha só ("20 minutos."): o destaque com algarismo nunca quebra de linha no meio.
    O destaque sem número ("seu anúncio?") anda palavra por palavra, como o resto do texto.
    """
    texto, dest = frase.texto, frase.destaque
    if not dest:
        return [(p, False) for p in texto.split()]
    i = texto.rfind(dest)
    if i < 0:
        return [(p, False) for p in texto.split()]
    antes, depois = texto[:i], texto[i + len(dest):]
    meio = [(dest, True)] if re.search(r"\d", dest) else [(p, True) for p in dest.split()]
    return [(p, False) for p in antes.split()] + meio + [(p, False) for p in depois.split()]


def quebra(dr: ImageDraw.ImageDraw, fichas_: list[tuple[str, bool]], fonte: ImageFont.FreeTypeFont, largura: int) -> list[list[tuple[str, bool]]]:
    """Distribui as fichas em linhas que cabem em `largura` (px). Ficha mais larga que a linha fica sozinha."""
    linhas: list[list[tuple[str, bool]]] = []
    atual: list[tuple[str, bool]] = []
    for ficha in fichas_:
        teste = atual + [ficha]
        if dr.textlength(" ".join(t for t, _ in teste), font=fonte) > largura and atual:
            linhas.append(atual)
            atual = [ficha]
        else:
            atual = teste
    if atual:
        linhas.append(atual)
    return linhas


def quebra_com_linhas(dr: ImageDraw.ImageDraw, texto: str, fonte: ImageFont.FreeTypeFont, largura: int) -> list[str]:
    """Texto simples (sem destaque) que respeita as quebras de linha escritas (\\n) e quebra o resto sozinho."""
    saida: list[str] = []
    for bloco in texto.split("\n"):
        for linha in quebra(dr, [(p, False) for p in bloco.split()], fonte, largura):
            saida.append(" ".join(t for t, _ in linha))
    return saida


def largura_maxima(dr: ImageDraw.ImageDraw, fichas_: list[tuple[str, bool]], fonte: ImageFont.FreeTypeFont) -> float:
    return max((dr.textlength(t, font=fonte) for t, _ in fichas_), default=0.0)
