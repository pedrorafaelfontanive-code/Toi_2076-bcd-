from pathlib import Path

import numpy as np
import pandas as pd
from astropy.io import fits
import matplotlib.pyplot as plt


BASE = Path(r"C:\Users\Pedro\Desktop\TOI_2076")
RAW = BASE / "raw" / "TOI-2076_JWST_MAST"

OUT_TABELAS = BASE / "outputs" / "tabelas"
OUT_FIGURAS = BASE / "outputs" / "figuras"

OUT_TABELAS.mkdir(parents=True, exist_ok=True)
OUT_FIGURAS.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# 1. Escolha didática do primeiro caso
# ------------------------------------------------------------

PASTA = RAW / "TOI-2076_b" / "NIRISS_SOSS" / "obs10"
PREFIXO = "jw05959010001_04102_00001"
PADRAO = f"{PREFIXO}*seg001*nis*x1dints.fits"

arquivos = sorted(PASTA.glob(PADRAO))

if not arquivos:
    raise FileNotFoundError(f"Nenhum arquivo encontrado com o padrão: {PADRAO}")

arquivo = arquivos[0]

# Pelo inventário, no NIRISS/SOSS o HDU 3 é um EXTRACT1D principal.
HDU_EXTRACT1D = 3


print("=" * 80)
print("ETAPA 02 — EXTRAÇÃO DIDÁTICA DE UM x1dints")
print("=" * 80)
print(f"Arquivo usado: {arquivo}")
print(f"HDU usado: {HDU_EXTRACT1D}")


# ------------------------------------------------------------
# 2. Abrir o FITS
# ------------------------------------------------------------

with fits.open(arquivo, memmap=True) as hdul:
    hdu = hdul[HDU_EXTRACT1D]
    data = hdu.data

    print("\nColunas disponíveis:")
    print(hdu.columns.names)

    wave_col = "WAVELENGTH"
    flux_col = "FLUX"
    err_col = "FLUX_ERROR"
    dq_col = "DQ"

    n_integracoes = len(data)

    print(f"\nNúmero de integrações: {n_integracoes}")

    # Pega a primeira integração só para descobrir quantos pixels espectrais existem.
    wave0 = np.array(data[wave_col][0], dtype=float)
    n_pixels = len(wave0)

    print(f"Número de pixels espectrais por integração: {n_pixels}")
    print(f"Faixa espectral aproximada: {np.nanmin(wave0):.4f} a {np.nanmax(wave0):.4f} µm")

    # ------------------------------------------------------------
    # 3. Criar tabela didática pequena
    # ------------------------------------------------------------
    # A tabela completa tempo × wavelength × flux pode ficar muito grande.
    # Para fins pedagógicos, salvamos uma amostra:
    # - primeiras 5 integrações
    # - um ponto espectral a cada 10 pixels

    linhas_fluxo = []

    integracoes_amostra = range(min(5, n_integracoes))
    passo_pixel = 10

    for i in integracoes_amostra:
        wave = np.array(data[wave_col][i], dtype=float)
        flux = np.array(data[flux_col][i], dtype=float)
        erro = np.array(data[err_col][i], dtype=float)

        if dq_col in hdu.columns.names:
            dq = np.array(data[dq_col][i])
        else:
            dq = np.zeros_like(flux, dtype=int)

        # Tempo: primeiro tenta usar TDB-MID no próprio EXTRACT1D.
        # Se não existir, usa o índice da integração.
        if "TDB-MID" in hdu.columns.names:
            tempo = data["TDB-MID"][i]
            tempo_coluna = "TDB-MID"
        elif "MJD-AVG" in hdu.columns.names:
            tempo = data["MJD-AVG"][i]
            tempo_coluna = "MJD-AVG"
        else:
            tempo = i
            tempo_coluna = "integration_index"

        for j in range(0, n_pixels, passo_pixel):
            linhas_fluxo.append({
                "integration_index": i,
                "time_value": float(tempo),
                "time_column": tempo_coluna,
                "pixel_index": j,
                "wavelength_um": float(wave[j]) if np.isfinite(wave[j]) else np.nan,
                "flux": float(flux[j]) if np.isfinite(flux[j]) else np.nan,
                "flux_error": float(erro[j]) if np.isfinite(erro[j]) else np.nan,
                "dq": int(dq[j]) if np.isfinite(dq[j]) else -1,
            })

    df_fluxo = pd.DataFrame(linhas_fluxo)

    saida_fluxo = OUT_TABELAS / "02_exemplo_fluxo_x1dints_b_niriss_hdu3.csv"
    df_fluxo.to_csv(saida_fluxo, index=False, encoding="utf-8-sig")

    print(f"\nTabela didática salva em:")
    print(saida_fluxo)

    # ------------------------------------------------------------
    # 4. Criar curva branca simples do mesmo arquivo
    # ------------------------------------------------------------
    # Curva branca = soma do fluxo em todos os comprimentos de onda válidos
    # para cada integração.

    linhas_curva = []

    for i in range(n_integracoes):
        wave = np.array(data[wave_col][i], dtype=float)
        flux = np.array(data[flux_col][i], dtype=float)
        erro = np.array(data[err_col][i], dtype=float)

        if dq_col in hdu.columns.names:
            dq = np.array(data[dq_col][i])
        else:
            dq = np.zeros_like(flux, dtype=int)

        if "TDB-MID" in hdu.columns.names:
            tempo = data["TDB-MID"][i]
            tempo_coluna = "TDB-MID"
        elif "MJD-AVG" in hdu.columns.names:
            tempo = data["MJD-AVG"][i]
            tempo_coluna = "MJD-AVG"
        else:
            tempo = i
            tempo_coluna = "integration_index"

        valido = np.isfinite(wave) & np.isfinite(flux) & (dq == 0)

        white_flux = np.nansum(flux[valido])
        white_error = np.sqrt(np.nansum(erro[valido] ** 2))
        n_validos = np.sum(valido)

        linhas_curva.append({
            "integration_index": i,
            "time_value": float(tempo),
            "time_column": tempo_coluna,
            "white_flux": float(white_flux),
            "white_flux_error": float(white_error),
            "n_pixels_validos": int(n_validos),
            "wavelength_min_um": float(np.nanmin(wave[valido])) if np.any(valido) else np.nan,
            "wavelength_max_um": float(np.nanmax(wave[valido])) if np.any(valido) else np.nan,
        })

    df_curva = pd.DataFrame(linhas_curva)

    # Normalização simples para visualização.
    # Isso facilita enxergar a variação relativa do fluxo.
    mediana_fluxo = np.nanmedian(df_curva["white_flux"])
    df_curva["white_flux_normalizado"] = df_curva["white_flux"] / mediana_fluxo

    saida_curva = OUT_TABELAS / "02_curva_branca_exemplo_b_niriss_hdu3.csv"
    df_curva.to_csv(saida_curva, index=False, encoding="utf-8-sig")

    print(f"\nCurva branca salva em:")
    print(saida_curva)

    # ------------------------------------------------------------
    # 5. Salvar resumo do arquivo
    # ------------------------------------------------------------

    resumo = pd.DataFrame([{
        "planeta": "TOI-2076_b",
        "instrumento": "NIRISS_SOSS",
        "obs": "obs10",
        "arquivo": arquivo.name,
        "hdu_usado": HDU_EXTRACT1D,
        "n_integracoes": n_integracoes,
        "n_pixels_espectrais": n_pixels,
        "wavelength_min_um": float(np.nanmin(wave0)),
        "wavelength_max_um": float(np.nanmax(wave0)),
        "coluna_wavelength": wave_col,
        "coluna_flux": flux_col,
        "coluna_flux_error": err_col,
        "coluna_dq": dq_col,
    }])

    saida_resumo = OUT_TABELAS / "02_resumo_exemplo_x1dints_b_niriss_hdu3.csv"
    resumo.to_csv(saida_resumo, index=False, encoding="utf-8-sig")

    print(f"\nResumo salvo em:")
    print(saida_resumo)


# ------------------------------------------------------------
# 6. Gerar figura simples da curva branca
# ------------------------------------------------------------

plt.figure(figsize=(10, 5))
plt.plot(
    df_curva["integration_index"],
    df_curva["white_flux_normalizado"],
    marker=".",
    linestyle="-",
)

plt.xlabel("Índice da integração")
plt.ylabel("Fluxo branco normalizado")
plt.title("TOI-2076 b — NIRISS/SOSS — obs10 — seg001 — HDU 3")
plt.tight_layout()

saida_figura = OUT_FIGURAS / "02_curva_branca_exemplo_b_niriss_hdu3.png"
plt.savefig(saida_figura, dpi=150)
plt.close()

print(f"\nFigura salva em:")
print(saida_figura)

print("\n" + "=" * 80)
print("ETAPA 02 FINALIZADA")
print("=" * 80)
print("Esta etapa gerou uma tabela didática tempo × wavelength × flux")
print("e uma curva branca simples para um único arquivo x1dints.")
print("Ainda não foi calculado espectro de transmissão.")