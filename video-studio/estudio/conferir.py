"""Conferências do vídeo: o que a tela mostra no passo "Gerar e conferir".

Cada item é {"nivel": "ok" | "aviso" | "erro", "texto": "frase curta"}. "erro" trava (o vídeo não sai); "aviso" deixa sair
e a equipe decide. Nada é "corrigido" em silêncio: a equipe vê o que foi conferido.
"""
from __future__ import annotations

from .marca import Marca

# Área que o Instagram cobre no Reels, em pixels de uma tela 1080 × 1920. Valor do Creative Lab (motor/estudio.py, "reels").
AREA_SEGURA = {"topo": 250, "base": 672}


def item(nivel: str, texto: str) -> dict:
    return {"nivel": nivel, "texto": texto}


def conferir_pedido(marca: Marca, textos: list[str], fotos: list[dict], geometria: dict, altura: int, ensaio: bool = False) -> list[dict]:
    """Conferências feitas antes de gerar.

    geometria: fim_texto_cortes e fim_texto_cartela (px, onde o texto termina), topo_logo_cenas (None quando o vídeo sai sem a
    logo nas cenas) e topo_logo_cartela, ficha_mais_larga e largura_util.
    ensaio: só a equipe, por linha de comando. Anunciante sem autorização vira aviso e o arquivo sai marcado "-ENSAIO".
    """
    achados: list[dict] = []

    # 1. palavras proibidas da marca (regras.palavras_proibidas do design system)
    proibidas: list[str] = []
    for t in textos:
        for p in marca.palavras_proibidas_em(t):
            if p not in proibidas:
                proibidas.append(p)
    if proibidas:
        lista = ", ".join(f"\"{p}\"" for p in proibidas)
        achados.append(item("erro", f"Palavra que {marca.nome} não usa: {lista}. Troque no texto."))
    else:
        achados.append(item("ok", "Nenhuma palavra proibida da marca."))

    # 2. anunciante legível só com autorização
    sem_autorizacao = [i + 1 for i, f in enumerate(fotos) if f.get("anunciante_legivel") and not f.get("autorizado")]
    if sem_autorizacao:
        nums = ", ".join(str(n) for n in sem_autorizacao)
        sujeito = f"A foto {nums} mostra" if len(sem_autorizacao) == 1 else f"As fotos {nums} mostram"
        if ensaio:
            achados.append(item("aviso", f"ENSAIO: {sujeito} anunciante legível sem autorização. Não poste nem mande a ninguém."))
        else:
            achados.append(item("erro", f"{sujeito} anunciante legível sem autorização. Troque a foto ou marque que tem a autorização."))
    else:
        achados.append(item("ok", "Nenhuma foto com anunciante legível sem autorização."))

    # 3. área do Instagram (aviso, não trava: ver a divergência acima)
    limite_base = altura - AREA_SEGURA["base"]
    avisos_area = []
    if geometria["fim_texto_cortes"] > limite_base:
        avisos_area.append(f"o texto dos cortes termina em {geometria['fim_texto_cortes']} px")
    if geometria["fim_texto_cartela"] > limite_base:
        avisos_area.append(f"a chamada da cartela termina em {geometria['fim_texto_cartela']} px")
    if geometria.get("topo_logo_cenas") is not None and geometria["topo_logo_cenas"] < AREA_SEGURA["topo"]:
        avisos_area.append(f"a logo das cenas começa em {geometria['topo_logo_cenas']} px")
    if geometria["topo_logo_cartela"] < AREA_SEGURA["topo"]:
        avisos_area.append(f"a logo da cartela começa em {geometria['topo_logo_cartela']} px")
    if avisos_area:
        achados.append(item(
            "aviso",
            f"Passa da área segura do Reels (regra do Creative Lab: de {AREA_SEGURA['topo']} a {limite_base} px): " + "; ".join(avisos_area) + "."))
    else:
        achados.append(item("ok", "Texto e logo fora da área que o Instagram cobre."))

    # 4. texto que não cabe na largura
    if geometria["ficha_mais_larga"] > geometria["largura_util"]:
        achados.append(item("aviso", "Tem palavra mais larga que a tela. Encurte o texto."))

    return achados


def conferir_saida(medidas: dict, esperado: dict) -> list[dict]:
    """Conferências do arquivo pronto (medidas vêm do ffprobe)."""
    achados = []
    if (medidas["largura"], medidas["altura"]) == (esperado["largura"], esperado["altura"]):
        achados.append(item("ok", f"Em pé, {medidas['largura']} × {medidas['altura']}."))
    else:
        achados.append(item("erro", f"Tamanho {medidas['largura']} × {medidas['altura']}; devia ser {esperado['largura']} × {esperado['altura']}."))
    if abs(medidas["fps"] - esperado["fps"]) < 0.01:
        achados.append(item("ok", f"{esperado['fps']:g} quadros por segundo."))
    else:
        achados.append(item("erro", f"{medidas['fps']:g} quadros por segundo; devia ser {esperado['fps']:g}."))
    if abs(medidas["duracao"] - esperado["duracao"]) <= 0.15:
        achados.append(item("ok", f"Dura {medidas['duracao']:.1f} s, como o combinado."))
    else:
        achados.append(item("erro", f"Dura {medidas['duracao']:.1f} s; devia durar {esperado['duracao']:.1f} s."))
    return achados


def tem_erro(achados: list[dict]) -> bool:
    return any(a["nivel"] == "erro" for a in achados)
