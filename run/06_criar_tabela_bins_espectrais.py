"""
05a_criar_tabela_bins_espectrais.py

Etapa 05A — Criação da tabela de bins espectrais.

Objetivo:
Criar uma tabela editável de bins espectrais que será usada nas próximas etapas
para extrair curvas de luz por intervalo de comprimento de onda.

Esta etapa ainda NÃO extrai fluxo por bin.
Ela apenas define as faixas espectrais que serão usadas depois.

Saída:
outputs/tabelas/05_bins_espectrais.csv
"""

from pathlib import Path
import numpy as np
import pandas as pd


BASE = Path(r"C:\Users\Pedro\Desktop\TOI_2076")
OUT = BASE / "outputs" / "tabelas"
OUT.mkdir(parents=True, exist_ok=True)


# Faixas iniciais conservadoras, evitando bordas muito extremas.
# Depois podemos ajustar com base na qualidade das curvas.
componentes = [
    {
        "instrumento": "NIRISS_SOSS",
        "parte": "HDU3",
        "descricao": "SOSS ordem/faixa principal",
        "wmin": 0.90,
        "wmax": 2.80,
        "largura_bin": 0.10,
    },
    {
        "instrumento": "NIRISS_SOSS",
        "parte": "HDU4",
        "descricao": "SOSS ordem/faixa curta",
        "wmin": 0.60,
        "wmax": 1.40,
        "largura_bin": 0.10,
    },
    {
        "instrumento": "NIRSpec_G395H",
        "parte": "NRS1",
        "descricao": "Detector NRS1",
        "wmin": 3.05,
        "wmax": 3.70,
        "largura_bin": 0.10,
    },
    {
        "instrumento": "NIRSpec_G395H",
        "parte": "NRS2",
        "descricao": "Detector NRS2",
        "wmin": 3.85,
        "wmax": 4.50,
        "largura_bin": 0.10,
    },
]


linhas = []

for comp in componentes:
    instrumento = comp["instrumento"]
    parte = comp["parte"]
    descricao = comp["descricao"]
    wmin = comp["wmin"]
    wmax = comp["wmax"]
    largura = comp["largura_bin"]

    bordas = np.arange(wmin, wmax + 0.0001, largura)

    bin_id = 1

    for i in range(len(bordas) - 1):
        bmin = round(float(bordas[i]), 5)
        bmax = round(float(bordas[i + 1]), 5)
        centro = round((bmin + bmax) / 2, 5)

        linhas.append({
            "instrumento": instrumento,
            "parte": parte,
            "descricao": descricao,
            "bin_id": bin_id,
            "wavelength_min_um": bmin,
            "wavelength_max_um": bmax,
            "wavelength_center_um": centro,
            "bin_width_um": round(bmax - bmin, 5),
            "usar_bin": True,
            "observacao": "",
        })

        bin_id += 1


df = pd.DataFrame(linhas)

saida = OUT / "05_bins_espectrais.csv"
df.to_csv(saida, index=False, encoding="utf-8-sig")

print("Tabela de bins criada em:")
print(saida)

print("\nResumo:")
print(df.groupby(["instrumento", "parte"]).size())
