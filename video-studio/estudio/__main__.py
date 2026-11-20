"""Linha de comando do motor.

Uso:
  python -m estudio fix-mudo PEDIDO.json --fotos PASTA --saida PASTA [--ensaio]

O PEDIDO.json está descrito no README do Estúdio. Sai um JSON com o relatório (ou {"ok": false, "erro": "..."}).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .fix_mudo import ErroPedido, gerar, ler_pedido
from .marca import ErroMarca


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="estudio")
    sub = ap.add_subparsers(dest="modelo", required=True)
    fm = sub.add_parser("fix-mudo", help="vídeo mudo com frase na tela (receita da Fix)")
    fm.add_argument("pedido")
    fm.add_argument("--fotos", required=True)
    fm.add_argument("--saida", required=True)
    fm.add_argument("--ensaio", action="store_true", help="só equipe: deixa sair foto com anunciante sem autorização, marcada -ENSAIO")
    a = ap.parse_args(argv)
    try:
        with open(a.pedido, encoding="utf-8") as f:
            pedido = ler_pedido(json.load(f))
        rel = gerar(pedido, Path(a.fotos), Path(a.saida), ensaio=a.ensaio, log=lambda m: print(f"[estudio] {m}", file=sys.stderr))
    except (ErroPedido, ErroMarca) as e:
        rel = {"ok": False, "erro": str(e).split("\n")[0]}
        print(json.dumps(rel, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(rel, ensure_ascii=False, indent=2))
    return 0 if rel.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
