"""Carrega cores, fontes, logo e regras do guia de marca."""
from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from PIL import ImageFont

# Raiz do Estúdio de vídeo.
RAIZ = Path(__file__).resolve().parents[1]
MARCAS = Path(os.environ.get("ESTUDIO_MARCAS", RAIZ / "examples"))
LOGOS = Path(os.environ.get("ESTUDIO_LOGOS", RAIZ / "examples" / "logos"))
FONTES = Path(os.environ.get("ESTUDIO_FONTES", RAIZ / "examples" / "fonts"))


class ErroMarca(Exception):
    """Frase curta, pronta para a tela."""


def hex_rgb(cor: str) -> tuple[int, int, int]:
    cor = cor.lstrip("#")
    return int(cor[0:2], 16), int(cor[2:4], 16), int(cor[4:6], 16)


def sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn").lower()


@dataclass(frozen=True)
class Marca:
    slug: str
    nome: str
    instagram: str
    cores: dict[str, tuple[int, int, int]]
    fontes: dict[str, tuple[str, int]]  # papel (titulo, texto, etiqueta) -> (família, peso)
    proibidas: tuple[str, ...]
    logo: Path

    def cor(self, nome: str) -> tuple[int, int, int]:
        if nome not in self.cores:
            raise ErroMarca(f"A marca {self.nome} não tem a cor \"{nome}\" no design system.")
        return self.cores[nome]

    def fonte(self, papel: str, tamanho: int) -> ImageFont.FreeTypeFont:
        familia, peso = self.fontes[papel]
        arquivo = _arquivo_fonte(familia, peso)
        if arquivo is None:
            return ImageFont.load_default(size=tamanho)
        return ImageFont.truetype(str(arquivo), tamanho)

    def palavras_proibidas_em(self, texto: str) -> list[str]:
        """Palavras ou expressões proibidas da marca que aparecem no texto (sem diferença de acento nem de caixa)."""
        base = sem_acento(texto)
        achadas = []
        for p in self.proibidas:
            if re.search(r"(?<!\w)" + re.escape(sem_acento(p)) + r"(?!\w)", base):
                achadas.append(p)
        return achadas


def _arquivo_fonte(familia: str, peso: int) -> Path | None:
    if familia == "Pillow Default":
        return None
    pasta = FONTES / re.sub(r"[^a-z0-9]+", "-", familia.lower()).strip("-")
    pesos = {}
    for arq in pasta.glob("*-latin-*-normal.woff2"):
        achou = re.search(r"-latin-(\d+)-normal\.woff2$", arq.name)
        if achou:
            pesos[int(achou.group(1))] = arq
    if not pesos:
        raise ErroMarca(f"A fonte {familia} ainda não está no Estúdio.")
    return pesos[min(pesos, key=lambda p: abs(p - peso))]


def carregar(slug: str, com_logo: bool = True) -> Marca:
    """`com_logo=False`: o vídeo com fala só usa cor, fonte e palavras proibidas (texto por cima); a logo é da receita da Fix."""
    if not re.fullmatch(r"[a-z0-9-]+", slug):
        raise ErroMarca("Marca inválida.")
    arquivo = MARCAS / f"{slug}.json"
    if not arquivo.exists():
        raise ErroMarca("Essa marca ainda não tem design system no Estúdio.")
    with open(arquivo, encoding="utf-8") as f:
        dados = json.load(f)["marca"]
    logo = LOGOS / slug / "logo.png"
    if com_logo and not logo.exists():
        raise ErroMarca(f"A logo de {dados['nome']} ainda não está no Estúdio.")
    fontes = {papel: (v["familia"], int(v["peso"])) for papel, v in dados["fontes"].items()}
    return Marca(
        slug=slug,
        nome=dados["nome"],
        instagram=dados.get("instagram", ""),
        cores={k: hex_rgb(v) for k, v in dados["cores"].items()},
        fontes=fontes,
        proibidas=tuple(dados.get("regras", {}).get("palavras_proibidas", [])),
        logo=logo,
    )
