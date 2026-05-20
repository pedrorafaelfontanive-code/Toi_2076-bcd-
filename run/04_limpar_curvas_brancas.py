"""
04_limpar_curvas_brancas.py

Etapa 04 — Limpeza diagnóstica das curvas brancas.

Objetivo:
Ler as curvas brancas já extraídas e identificar pontos discrepantes
(outliers) de forma simples e reprodutível.

Este script NÃO calcula profundidade de trânsito.
Este script NÃO gera espectro de transmissão.
Ele apenas prepara as curvas brancas para diagnóstico.

Entrada:
outputs/fluxo de luz branca/

Saídas:
Para cada curva branca encontrada:
- *_limpa.csv
- *_bruta_vs_limpa.png

A curva original não é apagada.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


BASE = Path(r"C:\Users\Pedro\Desktop\TOI_2076")

PASTA_CURVAS = BASE / "outputs" / "fluxo de luz branca_bruta"

if not PASTA_CURVAS.exists():
    raise FileNotFoundError(f"Pasta não encontrada: {PASTA_CURVAS}")


def sigma_robusto(valores):
    """
    Calcula uma estimativa robusta de dispersão usando MAD.
    MAD = median absolute deviation.
    """
    valores = np.asarray(valores, dtype=float)
    valores = valores[np.isfinite(valores)]

    if len(valores) == 0:
        return np.nan

    mediana = np.nanmedian(valores)
    mad = np.nanmedian(np.abs(valores - mediana))

    if mad == 0 or not np.isfinite(mad):
        return np.nanstd(valores)

    return 1.4826 * mad


def escolher_coluna_fluxo(df):
    """
    Escolhe a melhor coluna normalizada para diagnóstico.
    Preferimos normalização por segmento, se existir.
    """
    if "white_flux_normalizado_por_segmento" in df.columns:
        return "white_flux_normalizado_por_segmento"

    if "white_flux_normalizado" in df.columns:
        return "white_flux_normalizado"

    if "white_flux" in df.columns:
        mediana = np.nanmedian(df["white_flux"])
        df["white_flux_normalizado"] = df["white_flux"] / mediana
        return "white_flux_normalizado"

    raise ValueError("Não encontrei white_flux nem coluna normalizada.")


def limpar_curva(arquivo_csv):
    print("\n" + "=" * 80)
    print(f"Lendo: {arquivo_csv}")

    df = pd.read_csv(arquivo_csv)

    if len(df) < 10:
        print("Arquivo pequeno demais. Pulando.")
        return

    if "integration_index_global" not in df.columns:
        df["integration_index_global"] = np.arange(len(df))

    coluna_fluxo = escolher_coluna_fluxo(df)

    y = df[coluna_fluxo].astype(float)

    # Janela da mediana móvel.
    # Usa tamanho ímpar e adapta ao tamanho da curva.
    janela = 31
    if len(df) < janela:
        janela = max(5, len(df) // 5)
        if janela % 2 == 0:
            janela += 1

    tendencia = y.rolling(window=janela, center=True, min_periods=5).median()

    # Onde a tendência ficou NaN nas bordas, usa mediana global.
    tendencia = tendencia.fillna(np.nanmedian(y))

    residuo = y - tendencia
    sig = sigma_robusto(residuo)

    if not np.isfinite(sig) or sig == 0:
        sig = np.nanstd(residuo)

    LIMIAR_SIGMA = 5.0

    outlier = np.abs(residuo) > LIMIAR_SIGMA * sig

    # Também marca pontos sem fluxo válido.
    invalido = ~np.isfinite(y)

    usar = ~(outlier | invalido)

    df["fluxo_usado_no_diagnostico"] = y
    df["tendencia_mediana_movel"] = tendencia
    df["residuo"] = residuo
    df["sigma_robusto"] = sig
    df["outlier_sigma"] = outlier
    df["ponto_invalido"] = invalido
    df["usar_na_etapa_seguinte"] = usar

    n_total = len(df)
    n_outliers = int(outlier.sum())
    n_invalidos = int(invalido.sum())
    n_usados = int(usar.sum())

    print(f"Coluna usada: {coluna_fluxo}")
    print(f"Total de pontos: {n_total}")
    print(f"Outliers marcados: {n_outliers}")
    print(f"Pontos inválidos: {n_invalidos}")
    print(f"Pontos mantidos: {n_usados}")
    print(f"Sigma robusto: {sig}")

    # Salvar CSV limpo ao lado do original
    saida_csv = arquivo_csv.with_name(f"{arquivo_csv.stem}_limpa.csv")
    df.to_csv(saida_csv, index=False, encoding="utf-8-sig")

    # Figura
    plt.figure(figsize=(11, 5))

    plt.plot(
        df["integration_index_global"],
        df["fluxo_usado_no_diagnostico"],
        marker=".",
        linestyle="-",
        linewidth=0.7,
        markersize=3,
        label="curva branca bruta",
    )

    plt.plot(
        df.loc[df["usar_na_etapa_seguinte"], "integration_index_global"],
        df.loc[df["usar_na_etapa_seguinte"], "fluxo_usado_no_diagnostico"],
        marker=".",
        linestyle="None",
        markersize=4,
        label="pontos mantidos",
    )

    if n_outliers > 0:
        plt.plot(
            df.loc[df["outlier_sigma"], "integration_index_global"],
            df.loc[df["outlier_sigma"], "fluxo_usado_no_diagnostico"],
            marker="x",
            linestyle="None",
            markersize=6,
            label="outliers marcados",
        )

    titulo = arquivo_csv.stem.replace("_", " ")
    plt.title(titulo)
    plt.xlabel("Índice global da integração")
    plt.ylabel("Fluxo branco normalizado")
    plt.legend()

    # Recorte visual automático para não deixar um outlier destruir a escala.
    y_mantido = df.loc[df["usar_na_etapa_seguinte"], "fluxo_usado_no_diagnostico"]
    if len(y_mantido) > 0:
        y_med = np.nanmedian(y_mantido)
        y_sig = sigma_robusto(y_mantido)
        if np.isfinite(y_sig) and y_sig > 0:
            plt.ylim(y_med - 6 * y_sig, y_med + 6 * y_sig)

    plt.tight_layout()

    saida_fig = arquivo_csv.with_name(f"{arquivo_csv.stem}_bruta_vs_limpa.png")
    plt.savefig(saida_fig, dpi=150)
    plt.close()

    print(f"CSV limpo salvo em: {saida_csv}")
    print(f"Figura salva em: {saida_fig}")


# Procura CSVs de curvas brancas dentro da pasta organizada pelo usuário.
arquivos_csv = sorted(PASTA_CURVAS.rglob("*.csv"))

# Evita reprocessar arquivos já limpos ou resumos.
arquivos_csv = [
    arq for arq in arquivos_csv
    if "_limpa" not in arq.stem.lower()
    and "resumo" not in arq.stem.lower()
]

print("=" * 80)
print("ETAPA 04 — LIMPEZA DAS CURVAS BRANCAS")
print("=" * 80)
print(f"Pasta de entrada: {PASTA_CURVAS}")
print(f"Arquivos CSV encontrados: {len(arquivos_csv)}")

for arquivo in arquivos_csv:
    try:
        limpar_curva(arquivo)
    except Exception as erro:
        print(f"\nERRO ao processar {arquivo}")
        print(erro)

print("\n" + "=" * 80)
print("ETAPA 04 FINALIZADA")
print("=" * 80)
print("Foram geradas versões limpas/diagnósticas das curvas brancas.")
print("Os dados originais não foram apagados.")