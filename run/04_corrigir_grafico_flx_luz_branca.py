"""
04_corrigir_grafico_flx_luz_branca.py

Objetivo:
Ler a curva branca já extraída do TOI-2076 d / NIRSpec / obs13 / NRS1
e gerar uma nova figura com o eixo Y recortado.

Este script NÃO altera a tabela original.
Ele apenas cria uma nova imagem para melhor visualização.
"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


BASE = Path(r"C:\Users\Pedro\Desktop\TOI_2076")

ARQUIVO_ENTRADA = (
    BASE
    / "outputs"
    / "fluxo de luz branca"
    / "NRS1"
    / "OBS 13"
    / "03_curva_branca_TOI_2076_d_NIRSpec_G395H_obs13_NRS1.csv"
)

PASTA_SAIDA = (
    BASE
    / "outputs"
    / "fluxo de luz branca"
    / "NRS1"
    / "OBS 13"
)

ARQUIVO_SAIDA = (
    PASTA_SAIDA
    / "03_curva_branca_TOI_2076_d_NIRSpec_G395H_obs13_NRS1_recortada.png"
)


if not ARQUIVO_ENTRADA.exists():
    raise FileNotFoundError(f"Arquivo de entrada não encontrado: {ARQUIVO_ENTRADA}")

df = pd.read_csv(ARQUIVO_ENTRADA)

plt.figure(figsize=(11, 5))

plt.plot(
    df["integration_index_global"],
    df["white_flux_normalizado"],
    marker=".",
    linestyle="-",
    linewidth=0.8,
    markersize=3,
)

plt.xlabel("Índice global da integração")
plt.ylabel("Fluxo branco normalizado")
plt.title("TOI-2076 d | NIRSpec/G395H | obs13 | NRS1")

# Recorte visual do eixo Y.
# Isso não remove dados, apenas melhora a visualização do gráfico.
plt.ylim(0.975, 1.025)

plt.tight_layout()
plt.savefig(ARQUIVO_SAIDA, dpi=150)
plt.close()

print("Figura recortada salva em:")
print(ARQUIVO_SAIDA)