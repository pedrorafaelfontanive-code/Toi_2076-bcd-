"""
00_teste_ambiente.py

Teste inicial do ambiente do projeto TOI-2076.

Objetivo:
- Verificar se a venv está funcionando.
- Verificar se os pacotes científicos estão instalados.
- Verificar se a pasta raw/ existe.
- Contar arquivos FITS.
- Listar alguns arquivos x1dints.fits encontrados.

Este script não faz extração científica ainda.
"""

from pathlib import Path
import sys

import astropy
import numpy as np
import pandas as pd
import matplotlib

BASE = Path(r"C:\Users\Pedro\Desktop\TOI_2076")
RAW = BASE / "raw"


print("=" * 60)
print("TESTE DO AMBIENTE — TOI-2076")
print("=" * 60)

print("\n[1] Python em uso:")
print(sys.executable)

print("\n[2] Versões dos pacotes:")
print(f"Astropy: {astropy.__version__}")
print(f"NumPy: {np.__version__}")
print(f"Pandas: {pd.__version__}")
print(f"Matplotlib: {matplotlib.__version__}")

print("\n[3] Pasta base:")
print(BASE)

print("\n[4] Pasta raw existe?")
print(RAW.exists())

print("\n[5] Contando arquivos FITS em raw/:")
fits_files = list(RAW.rglob("*.fits"))
print(f"Total de FITS encontrados: {len(fits_files)}")

print("\n[6] Procurando arquivos x1dints.fits:")
x1dints_files = list(RAW.rglob("*x1dints.fits"))
print(f"Total de x1dints encontrados: {len(x1dints_files)}")

print("\n[7] Primeiros x1dints encontrados:")
for arquivo in x1dints_files[:10]:
    print("-", arquivo)

print("\n" + "=" * 60)
print("TESTE FINALIZADO")
print("=" * 60)