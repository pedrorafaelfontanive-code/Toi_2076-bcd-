"""
01_inspecionar_x1dints.py

Etapa 01 do projeto TOI-2076.

Objetivo:
Inspecionar os arquivos x1dints.fits principais do JWST para TOI-2076 b, c e d.

Este script ainda NÃO calcula espectro de transmissão.
Ele apenas verifica a estrutura dos arquivos:
- planeta;
- instrumento;
- observação;
- nome do arquivo;
- HDUs;
- colunas;
- número de linhas;
- faixa de comprimento de onda.

Saída:
metadata/01_inventario_x1dints.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd
from astropy.io import fits


BASE = Path(r"C:\Users\Pedro\Desktop\TOI_2076")
RAW = BASE / "raw" / "TOI-2076_JWST_MAST"
OUT = BASE / "outputs" / "tabelas"

OUT.mkdir(exist_ok=True)


observacoes = [
    {
        "planeta": "TOI-2076_b",
        "instrumento": "NIRSpec_G395H",
        "obs": "obs09",
        "pasta": RAW / "TOI-2076_b" / "NIRSpec_G395H" / "obs09",
        "prefixo": "jw05959009001_04102_00001",
    },
    {
        "planeta": "TOI-2076_b",
        "instrumento": "NIRISS_SOSS",
        "obs": "obs10",
        "pasta": RAW / "TOI-2076_b" / "NIRISS_SOSS" / "obs10",
        "prefixo": "jw05959010001_04102_00001",
    },
    {
        "planeta": "TOI-2076_c",
        "instrumento": "NIRSpec_G395H",
        "obs": "obs11",
        "pasta": RAW / "TOI-2076_c" / "NIRSpec_G395H" / "obs11",
        "prefixo": "jw05959011001_04102_00001",
    },
    {
        "planeta": "TOI-2076_c",
        "instrumento": "NIRISS_SOSS",
        "obs": "obs12",
        "pasta": RAW / "TOI-2076_c" / "NIRISS_SOSS" / "obs12",
        "prefixo": "jw05959012001_04102_00001",
    },
    {
        "planeta": "TOI-2076_d",
        "instrumento": "NIRSpec_G395H",
        "obs": "obs13",
        "pasta": RAW / "TOI-2076_d" / "NIRSpec_G395H" / "obs13",
        "prefixo": "jw05959013001_04102_00001",
    },
    {
        "planeta": "TOI-2076_d",
        "instrumento": "NIRISS_SOSS",
        "obs": "obs14",
        "pasta": RAW / "TOI-2076_d" / "NIRISS_SOSS" / "obs14",
        "prefixo": "jw05959014001_04102_00001",
    },
]


def achar_coluna(colunas, nomes_possiveis):
    """Procura uma coluna ignorando maiúsculas/minúsculas."""
    mapa = {c.upper(): c for c in colunas}

    for nome in nomes_possiveis:
        if nome.upper() in mapa:
            return mapa[nome.upper()]

    return None


def calcular_faixa_wavelength(dados, coluna_wave):
    """Calcula wavelength mínimo e máximo, se possível."""
    try:
        wave = np.array(dados[coluna_wave], dtype=float)
        return float(np.nanmin(wave)), float(np.nanmax(wave))
    except Exception:
        return None, None


linhas = []

print("\n=== ETAPA 01 — INSPEÇÃO DOS x1dints ===\n")

for item in observacoes:
    planeta = item["planeta"]
    instrumento = item["instrumento"]
    obs = item["obs"]
    pasta = item["pasta"]
    prefixo = item["prefixo"]

    print("=" * 80)
    print(f"{planeta} | {instrumento} | {obs}")
    print(f"Pasta: {pasta}")

    arquivos = sorted(pasta.glob(f"{prefixo}*x1dints.fits"))

    print(f"Arquivos x1dints encontrados: {len(arquivos)}")

    if len(arquivos) == 0:
        linhas.append({
            "planeta": planeta,
            "instrumento": instrumento,
            "obs": obs,
            "arquivo": "",
            "hdu_index": "",
            "hdu_nome": "",
            "status": "SEM_X1DINTS",
            "colunas": "",
            "n_linhas": "",
            "wavelength_min_um": "",
            "wavelength_max_um": "",
            "flux_coluna": "",
            "erro_coluna": "",
        })
        continue

    for arquivo in arquivos:
        print(f"\nArquivo: {arquivo.name}")

        with fits.open(arquivo, memmap=True) as hdul:
            print("HDUs encontrados:")
            hdul.info()

            for i, hdu in enumerate(hdul):
                hdu_nome = hdu.name

                if not hasattr(hdu, "columns") or hdu.columns is None:
                    continue

                colunas = list(hdu.columns.names)
                dados = hdu.data
                n_linhas = len(dados) if dados is not None else 0

                coluna_wave = achar_coluna(colunas, ["WAVELENGTH", "WAVE", "LAMBDA"])
                coluna_flux = achar_coluna(colunas, ["FLUX", "SURF_BRIGHT", "SB"])
                coluna_erro = achar_coluna(colunas, ["FLUX_ERROR", "FLUX_ERR", "ERROR", "ERR"])

                wmin, wmax = None, None
                if coluna_wave is not None:
                    wmin, wmax = calcular_faixa_wavelength(dados, coluna_wave)

                print(f"\n  HDU {i}: {hdu_nome}")
                print(f"    colunas: {colunas}")
                print(f"    n_linhas: {n_linhas}")
                print(f"    coluna wavelength: {coluna_wave}")
                print(f"    coluna fluxo: {coluna_flux}")
                print(f"    coluna erro: {coluna_erro}")
                print(f"    faixa wavelength: {wmin} até {wmax} µm")

                linhas.append({
                    "planeta": planeta,
                    "instrumento": instrumento,
                    "obs": obs,
                    "arquivo": arquivo.name,
                    "hdu_index": i,
                    "hdu_nome": hdu_nome,
                    "status": "OK",
                    "colunas": "; ".join(colunas),
                    "n_linhas": n_linhas,
                    "wavelength_min_um": wmin,
                    "wavelength_max_um": wmax,
                    "flux_coluna": coluna_flux,
                    "erro_coluna": coluna_erro,
                })


df = pd.DataFrame(linhas)

saida = OUT / "01_inventario_x1dints.csv"
df.to_csv(saida, index=False, encoding="utf-8-sig")

print("\n=== FINALIZADO ===")
print(f"Inventário salvo em: {saida}")