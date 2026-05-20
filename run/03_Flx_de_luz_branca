"""
03_curvas_brancas_todos.py

Etapa 03 — Curvas brancas para todos os planetas e instrumentos.

Objetivo:
Construir curvas brancas a partir dos produtos x1dints.fits dos planetas
TOI-2076 b, c e d, usando NIRISS/SOSS e NIRSpec/G395H.

Nesta etapa, não salvamos mais a tabela completa pixel por pixel.
Para cada integração, somamos o fluxo válido em todos os comprimentos de onda
do HDU/detector escolhido.

Entradas:
- x1dints.fits principais em raw/

Saídas:
- outputs/tabelas/03_curvas_brancas_todos.csv
- outputs/tabelas/03_resumo_curvas_brancas_todos.csv
- outputs/figuras/curvas_brancas/*.png

Esta etapa ainda NÃO calcula:
- profundidade de trânsito;
- espectro de transmissão;
- retrieval.
"""

from pathlib import Path
import re

import numpy as np
import pandas as pd
from astropy.io import fits
import matplotlib.pyplot as plt


BASE = Path(r"C:\Users\Pedro\Desktop\TOI_2076")
RAW = BASE / "raw" / "TOI-2076_JWST_MAST"

OUT_TABELAS = BASE / "outputs" / "tabelas"
OUT_FIGURAS = BASE / "outputs" / "figuras" / "curvas_brancas"

OUT_TABELAS.mkdir(parents=True, exist_ok=True)
OUT_FIGURAS.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Observações principais
# ------------------------------------------------------------

observacoes = [
    # TOI-2076 b
    {
        "planeta": "TOI-2076_b",
        "instrumento": "NIRISS_SOSS",
        "obs": "obs10",
        "pasta": RAW / "TOI-2076_b" / "NIRISS_SOSS" / "obs10",
        "prefixo": "jw05959010001_04102_00001",
        "padrao_extra": "*nis*x1dints.fits",
        "partes": [
            {"nome_parte": "SOSS_HDU3_ordem_1", "hdu": 3},
            {"nome_parte": "SOSS_HDU4_ordem_2", "hdu": 4},
        ],
    },
    {
        "planeta": "TOI-2076_b",
        "instrumento": "NIRSpec_G395H",
        "obs": "obs09",
        "pasta": RAW / "TOI-2076_b" / "NIRSpec_G395H" / "obs09",
        "prefixo": "jw05959009001_04102_00001",
        "padrao_extra": "*nrs*x1dints.fits",
        "partes": [
            {"nome_parte": "NRS1", "hdu": 2, "filtro_nome": "nrs1"},
            {"nome_parte": "NRS2", "hdu": 2, "filtro_nome": "nrs2"},
        ],
    },

    # TOI-2076 c
    {
        "planeta": "TOI-2076_c",
        "instrumento": "NIRISS_SOSS",
        "obs": "obs12",
        "pasta": RAW / "TOI-2076_c" / "NIRISS_SOSS" / "obs12",
        "prefixo": "jw05959012001_04102_00001",
        "padrao_extra": "*nis*x1dints.fits",
        "partes": [
            {"nome_parte": "SOSS_HDU3_ordem_1", "hdu": 3},
            {"nome_parte": "SOSS_HDU4_ordem_2", "hdu": 4},
        ],
    },
    {
        "planeta": "TOI-2076_c",
        "instrumento": "NIRSpec_G395H",
        "obs": "obs11",
        "pasta": RAW / "TOI-2076_c" / "NIRSpec_G395H" / "obs11",
        "prefixo": "jw05959011001_04102_00001",
        "padrao_extra": "*nrs*x1dints.fits",
        "partes": [
            {"nome_parte": "NRS1", "hdu": 2, "filtro_nome": "nrs1"},
            {"nome_parte": "NRS2", "hdu": 2, "filtro_nome": "nrs2"},
        ],
    },

    # TOI-2076 d
    {
        "planeta": "TOI-2076_d",
        "instrumento": "NIRISS_SOSS",
        "obs": "obs14",
        "pasta": RAW / "TOI-2076_d" / "NIRISS_SOSS" / "obs14",
        "prefixo": "jw05959014001_04102_00001",
        "padrao_extra": "*nis*x1dints.fits",
        "partes": [
            {"nome_parte": "SOSS_HDU3_ordem_1", "hdu": 3},
            {"nome_parte": "SOSS_HDU4_ordem_2", "hdu": 4},
        ],
    },
    {
        "planeta": "TOI-2076_d",
        "instrumento": "NIRSpec_G395H",
        "obs": "obs13",
        "pasta": RAW / "TOI-2076_d" / "NIRSpec_G395H" / "obs13",
        "prefixo": "jw05959013001_04102_00001",
        "padrao_extra": "*nrs*x1dints.fits",
        "partes": [
            {"nome_parte": "NRS1", "hdu": 2, "filtro_nome": "nrs1"},
            {"nome_parte": "NRS2", "hdu": 2, "filtro_nome": "nrs2"},
        ],
    },
]


def extrair_segmento(nome_arquivo):
    match = re.search(r"(seg\d+)", nome_arquivo)
    if match:
        return match.group(1)
    return "sem_segmento"


def nome_seguro(texto):
    return (
        texto.replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace("-", "_")
    )


def obter_tempo(data, colunas, i):
    if "TDB-MID" in colunas:
        return float(data["TDB-MID"][i]), "TDB-MID"
    if "MJD-AVG" in colunas:
        return float(data["MJD-AVG"][i]), "MJD-AVG"
    return float(i), "integration_index"


linhas = []
resumos = []

print("=" * 90)
print("ETAPA 03 — CURVAS BRANCAS PARA TODOS OS HDUs/DETECTORES")
print("=" * 90)

for obs_item in observacoes:
    planeta = obs_item["planeta"]
    instrumento = obs_item["instrumento"]
    obs = obs_item["obs"]
    pasta = obs_item["pasta"]
    prefixo = obs_item["prefixo"]
    padrao_extra = obs_item["padrao_extra"]

    arquivos_base = sorted(pasta.glob(f"{prefixo}{padrao_extra}"))

    print("\n" + "=" * 90)
    print(f"{planeta} | {instrumento} | {obs}")
    print(f"Pasta: {pasta}")
    print(f"Arquivos encontrados: {len(arquivos_base)}")

    for parte in obs_item["partes"]:
        nome_parte = parte["nome_parte"]
        hdu_index = parte["hdu"]
        filtro_nome = parte.get("filtro_nome", None)

        if filtro_nome:
            arquivos = [a for a in arquivos_base if filtro_nome.lower() in a.name.lower()]
        else:
            arquivos = arquivos_base

        print(f"\n--- Parte: {nome_parte} | HDU {hdu_index} ---")
        print(f"Arquivos usados nesta parte: {len(arquivos)}")

        if not arquivos:
            print("AVISO: nenhum arquivo encontrado para esta parte.")
            continue

        linhas_parte = []

        for arquivo in arquivos:
            segmento = extrair_segmento(arquivo.name)
            print(f"Lendo {segmento}: {arquivo.name}")

            with fits.open(arquivo, memmap=True) as hdul:
                if hdu_index >= len(hdul):
                    print(f"AVISO: HDU {hdu_index} não existe em {arquivo.name}")
                    continue

                hdu = hdul[hdu_index]

                if not hasattr(hdu, "columns") or hdu.columns is None:
                    print(f"AVISO: HDU {hdu_index} não tem colunas em {arquivo.name}")
                    continue

                data = hdu.data
                colunas = hdu.columns.names

                wave_col = "WAVELENGTH"
                flux_col = "FLUX"
                err_col = "FLUX_ERROR"
                dq_col = "DQ"

                if wave_col not in colunas or flux_col not in colunas or err_col not in colunas:
                    print(f"AVISO: faltam colunas principais em {arquivo.name}")
                    continue

                n_integracoes = len(data)

                for i in range(n_integracoes):
                    wave = np.array(data[wave_col][i], dtype=float)
                    flux = np.array(data[flux_col][i], dtype=float)
                    erro = np.array(data[err_col][i], dtype=float)

                    if dq_col in colunas:
                        dq = np.array(data[dq_col][i])
                    else:
                        dq = np.zeros_like(flux, dtype=int)

                    tempo, tempo_coluna = obter_tempo(data, colunas, i)

                    valido = (
                        np.isfinite(wave)
                        & np.isfinite(flux)
                        & np.isfinite(erro)
                        & (dq == 0)
                    )

                    if np.any(valido):
                        white_flux = np.nansum(flux[valido])
                        white_flux_error = np.sqrt(np.nansum(erro[valido] ** 2))
                        wavelength_min = np.nanmin(wave[valido])
                        wavelength_max = np.nanmax(wave[valido])
                        n_validos = np.sum(valido)
                    else:
                        white_flux = np.nan
                        white_flux_error = np.nan
                        wavelength_min = np.nan
                        wavelength_max = np.nan
                        n_validos = 0

                    linha = {
                        "planeta": planeta,
                        "instrumento": instrumento,
                        "obs": obs,
                        "parte": nome_parte,
                        "arquivo": arquivo.name,
                        "segmento": segmento,
                        "hdu": hdu_index,
                        "integration_index_segmento": i,
                        "time_value": tempo,
                        "time_column": tempo_coluna,
                        "white_flux": white_flux,
                        "white_flux_error": white_flux_error,
                        "n_pixels_validos": int(n_validos),
                        "wavelength_min_um": wavelength_min,
                        "wavelength_max_um": wavelength_max,
                    }

                    linhas.append(linha)
                    linhas_parte.append(linha)

        # ------------------------------------------------------------
        # Salvar e plotar cada parte separadamente
        # ------------------------------------------------------------

        df_parte = pd.DataFrame(linhas_parte)

        if df_parte.empty:
            continue

        df_parte = df_parte.sort_values(
            ["time_value", "segmento", "integration_index_segmento"]
        ).reset_index(drop=True)

        df_parte["integration_index_global"] = np.arange(len(df_parte))

        mediana_global = np.nanmedian(df_parte["white_flux"])
        df_parte["white_flux_normalizado"] = df_parte["white_flux"] / mediana_global

        df_parte["white_flux_normalizado_por_segmento"] = np.nan

        for seg, sub in df_parte.groupby("segmento"):
            mediana_seg = np.nanmedian(sub["white_flux"])
            if np.isfinite(mediana_seg) and mediana_seg != 0:
                df_parte.loc[sub.index, "white_flux_normalizado_por_segmento"] = (
                    df_parte.loc[sub.index, "white_flux"] / mediana_seg
                )

        nome_base = f"03_curva_branca_{nome_seguro(planeta)}_{nome_seguro(instrumento)}_{nome_seguro(obs)}_{nome_seguro(nome_parte)}"

        saida_csv_parte = OUT_TABELAS / f"{nome_base}.csv"
        df_parte.to_csv(saida_csv_parte, index=False, encoding="utf-8-sig")

        plt.figure(figsize=(11, 5))
        plt.plot(
            df_parte["integration_index_global"],
            df_parte["white_flux_normalizado"],
            marker=".",
            linestyle="-",
            linewidth=0.8,
            markersize=3,
        )
        plt.xlabel("Índice global da integração")
        plt.ylabel("Fluxo branco normalizado")
        plt.title(f"{planeta} | {instrumento} | {obs} | {nome_parte}")
        plt.tight_layout()

        saida_fig = OUT_FIGURAS / f"{nome_base}.png"
        plt.savefig(saida_fig, dpi=150)
        plt.close()

        print(f"CSV salvo: {saida_csv_parte}")
        print(f"Figura salva: {saida_fig}")

        resumos.append({
            "planeta": planeta,
            "instrumento": instrumento,
            "obs": obs,
            "parte": nome_parte,
            "hdu": hdu_index,
            "n_arquivos": len(arquivos),
            "n_integracoes_total": len(df_parte),
            "wavelength_min_um": float(np.nanmin(df_parte["wavelength_min_um"])),
            "wavelength_max_um": float(np.nanmax(df_parte["wavelength_max_um"])),
            "saida_csv": str(saida_csv_parte),
            "saida_figura": str(saida_fig),
        })


# ------------------------------------------------------------
# Salvar tabela mestra e resumo
# ------------------------------------------------------------

df_todos = pd.DataFrame(linhas)

if not df_todos.empty:
    df_todos = df_todos.sort_values(
        ["planeta", "instrumento", "obs", "parte", "time_value"]
    ).reset_index(drop=True)

saida_todos = OUT_TABELAS / "03_curvas_brancas_todos.csv"
df_todos.to_csv(saida_todos, index=False, encoding="utf-8-sig")

df_resumo = pd.DataFrame(resumos)
saida_resumo = OUT_TABELAS / "03_resumo_curvas_brancas_todos.csv"
df_resumo.to_csv(saida_resumo, index=False, encoding="utf-8-sig")

print("\n" + "=" * 90)
print("ETAPA 03 FINALIZADA")
print("=" * 90)
print(f"Tabela mestra salva em: {saida_todos}")
print(f"Resumo salvo em: {saida_resumo}")
print(f"Figuras salvas em: {OUT_FIGURAS}")
print("\nEsta etapa gerou curvas brancas para SOSS HDU 3, SOSS HDU 4, NRS1 e NRS2.")
print("Ainda não foi calculada profundidade de trânsito nem espectro de transmissão.")