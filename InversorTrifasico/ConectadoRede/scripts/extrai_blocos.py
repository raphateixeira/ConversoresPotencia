#!/usr/bin/env python3
"""Extrai o código dos blocos MATLAB Function de cada modelo Simulink do repositório.

O .slx é um zip binário: o git não mostra o que mudou na lei de controle. Este script
grava, ao lado de cada modelo, VSI*/blocos/<função>.m com o código de cada bloco
MATLAB Function (cópia somente leitura: edite sempre no Simulink e rode de novo).

Uso (na raiz do repositório):  python3 scripts/extrai_blocos.py
"""
import html
import re
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CABECALHO = "% Extraído de {modelo} por scripts/extrai_blocos.py (não editar: edite o bloco no Simulink).\n\n"


def blocos(slx: Path):
    """Retorna [(nome_da_funcao, codigo)] dos blocos MATLAB Function do modelo."""
    with zipfile.ZipFile(slx) as z:
        for nome in sorted(z.namelist()):
            if not nome.startswith("simulink/stateflow/") or not nome.endswith(".xml"):
                continue
            xml = z.read(nome).decode("utf-8", errors="ignore")
            for script in re.findall(r'<P Name="script"[^>]*>(.*?)</P>', xml, re.S):
                codigo = html.unescape(script).strip() + "\n"
                m = re.search(r"function\s+(?:\[?[^=]*\]?\s*=\s*)?(\w+)", codigo)
                yield (m.group(1) if m else Path(nome).stem), codigo


def main():
    for slx in sorted(RAIZ.glob("VSI*/*.slx")):
        destino = slx.parent / "blocos"
        for funcao, codigo in blocos(slx):
            destino.mkdir(exist_ok=True)
            arq = destino / f"{funcao}.m"
            arq.write_text(CABECALHO.format(modelo=slx.name) + codigo, encoding="utf-8")
            print(f"{slx.relative_to(RAIZ)} -> {arq.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
