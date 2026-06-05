"""
07_integrar_bins_separados.py

Etapa 07 — Integração espectral por bins para todos os planetas,
salvando cada componente espectral em um CSV separado.

O script processa:
- TOI-2076 b, c e d;
- NIRISS/SOSS: HDU3 e HDU4;
- NIRSpec/G395H: NRS1 e NRS2.

Entradas:
- produtos x1dints.fits;
- tabela 05_bins_espectrais.csv ou 06_bins_espectrais.csv;
- máscaras *_limpa.csv das curvas brancas, quando localizadas.

Saídas:
- 12 CSVs detalhados, um por planeta/componente espectral;
- 12 CSVs-resumo;
- 1 tabela-resumo geral;
- 1 gráfico didático do TOI-2076 b / NIRISS-SOSS / HDU3 / bin 1.

Esta etapa ainda NÃO calcula a profundidade do trânsito.
"""

from pathlib import Path
import re
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.io import fits


# ============================================================
# 1. CAMINHOS DO PROJETO
# ============================================================

BASE = Path(r"C:\Users\Pedro\Desktop\TOI_2076")
RAW = BASE / "raw" / "TOI-2076_JWST_MAST"
OUTPUTS = BASE / "outputs"
PASTA_SAIDA_GERAL = OUTPUTS / "fluxo_espectral_por_bin"

PASTA_SAIDA_GERAL.mkdir(parents=True, exist_ok=True)

CANDIDATOS_BINS = [
    OUTPUTS / "tabelas" / "06_bins_espectrais.csv",
    OUTPUTS / "tabelas" / "05_bins_espectrais.csv",
]

ARQUIVO_BINS = next(
    (arquivo for arquivo in CANDIDATOS_BINS if arquivo.exists()),
    None,
)

if ARQUIVO_BINS is None:
    caminhos = "\n".join(str(arquivo) for arquivo in CANDIDATOS_BINS)
    raise FileNotFoundError(
        "Tabela de bins não encontrada. O script procurou em:\n"
        f"{caminhos}"
    )


# ============================================================
# 2. CONFIGURAÇÃO DAS 12 EXTRAÇÕES
# ============================================================

CONFIGURACOES = [
    # TOI-2076 b
    {
        "planeta": "TOI-2076_b",
        "instrumento": "NIRISS_SOSS",
        "obs": "obs10",
        "parte": "HDU3",
        "hdu": 3,
        "prefixo": "jw05959010001_04102_00001",
        "padrao": "*nis*x1dints.fits",
    },
    {
        "planeta": "TOI-2076_b",
        "instrumento": "NIRISS_SOSS",
        "obs": "obs10",
        "parte": "HDU4",
        "hdu": 4,
        "prefixo": "jw05959010001_04102_00001",
        "padrao": "*nis*x1dints.fits",
    },
    {
        "planeta": "TOI-2076_b",
        "instrumento": "NIRSpec_G395H",
        "obs": "obs09",
        "parte": "NRS1",
        "hdu": 2,
        "prefixo": "jw05959009001_04102_00001",
        "padrao": "*nrs1*x1dints.fits",
    },
    {
        "planeta": "TOI-2076_b",
        "instrumento": "NIRSpec_G395H",
        "obs": "obs09",
        "parte": "NRS2",
        "hdu": 2,
        "prefixo": "jw05959009001_04102_00001",
        "padrao": "*nrs2*x1dints.fits",
    },

    # TOI-2076 c
    {
        "planeta": "TOI-2076_c",
        "instrumento": "NIRISS_SOSS",
        "obs": "obs12",
        "parte": "HDU3",
        "hdu": 3,
        "prefixo": "jw05959012001_04102_00001",
        "padrao": "*nis*x1dints.fits",
    },
    {
        "planeta": "TOI-2076_c",
        "instrumento": "NIRISS_SOSS",
        "obs": "obs12",
        "parte": "HDU4",
        "hdu": 4,
        "prefixo": "jw05959012001_04102_00001",
        "padrao": "*nis*x1dints.fits",
    },
    {
        "planeta": "TOI-2076_c",
        "instrumento": "NIRSpec_G395H",
        "obs": "obs11",
        "parte": "NRS1",
        "hdu": 2,
        "prefixo": "jw05959011001_04102_00001",
        "padrao": "*nrs1*x1dints.fits",
    },
    {
        "planeta": "TOI-2076_c",
        "instrumento": "NIRSpec_G395H",
        "obs": "obs11",
        "parte": "NRS2",
        "hdu": 2,
        "prefixo": "jw05959011001_04102_00001",
        "padrao": "*nrs2*x1dints.fits",
    },

    # TOI-2076 d
    {
        "planeta": "TOI-2076_d",
        "instrumento": "NIRISS_SOSS",
        "obs": "obs14",
        "parte": "HDU3",
        "hdu": 3,
        "prefixo": "jw05959014001_04102_00001",
        "padrao": "*nis*x1dints.fits",
    },
    {
        "planeta": "TOI-2076_d",
        "instrumento": "NIRISS_SOSS",
        "obs": "obs14",
        "parte": "HDU4",
        "hdu": 4,
        "prefixo": "jw05959014001_04102_00001",
        "padrao": "*nis*x1dints.fits",
    },
    {
        "planeta": "TOI-2076_d",
        "instrumento": "NIRSpec_G395H",
        "obs": "obs13",
        "parte": "NRS1",
        "hdu": 2,
        "prefixo": "jw05959013001_04102_00001",
        "padrao": "*nrs1*x1dints.fits",
    },
    {
        "planeta": "TOI-2076_d",
        "instrumento": "NIRSpec_G395H",
        "obs": "obs13",
        "parte": "NRS2",
        "hdu": 2,
        "prefixo": "jw05959013001_04102_00001",
        "padrao": "*nrs2*x1dints.fits",
    },
]


# ============================================================
# 3. FUNÇÕES AUXILIARES
# ============================================================

def converter_booleano(serie: pd.Series) -> pd.Series:
    """Converte True/False, sim/não e 1/0 para booleano."""
    return (
        serie.astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "sim", "yes"])
    )


def extrair_segmento(nome_arquivo: str) -> str:
    """Obtém seg001, seg002 etc. a partir do nome do arquivo."""
    resultado = re.search(r"(seg\d+)", nome_arquivo.lower())
    return resultado.group(1) if resultado else "sem_segmento"


def obter_tempo(data, colunas, indice: int) -> tuple[float, str]:
    """Obtém o tempo médio da integração."""
    if "TDB-MID" in colunas:
        return float(data["TDB-MID"][indice]), "TDB-MID"

    if "MJD-AVG" in colunas:
        return float(data["MJD-AVG"][indice]), "MJD-AVG"

    return float(indice), "integration_index"


def normalizar_texto(texto: str) -> str:
    """Normaliza nomes e caminhos para facilitar buscas."""
    texto = texto.lower().replace("-", "_")
    return re.sub(r"[^a-z0-9_]+", "_", texto)


def integrar_trapezio(
    wave: np.ndarray,
    flux: np.ndarray,
    erro: np.ndarray,
) -> tuple[float, float, int]:
    """
    Integra a densidade de fluxo com regra dos trapézios.

    Para erros independentes:
        sigma_integrado = sqrt(sum((peso_i * sigma_i)^2))
    """
    wave = np.asarray(wave, dtype=float)
    flux = np.asarray(flux, dtype=float)
    erro = np.asarray(erro, dtype=float)

    if len(wave) < 2:
        return np.nan, np.nan, int(len(wave))

    ordem = np.argsort(wave)
    wave = wave[ordem]
    flux = flux[ordem]
    erro = erro[ordem]

    wave, indices_unicos = np.unique(wave, return_index=True)
    flux = flux[indices_unicos]
    erro = erro[indices_unicos]

    if len(wave) < 2:
        return np.nan, np.nan, int(len(wave))

    delta_wave = np.diff(wave)
    pesos = np.zeros(len(wave), dtype=float)

    pesos[0] = delta_wave[0] / 2
    pesos[-1] = delta_wave[-1] / 2

    if len(wave) > 2:
        pesos[1:-1] = (delta_wave[:-1] + delta_wave[1:]) / 2

    fluxo_integrado = np.sum(pesos * flux)
    erro_integrado = np.sqrt(np.sum((pesos * erro) ** 2))

    return (
        float(fluxo_integrado),
        float(erro_integrado),
        int(len(wave)),
    )


def localizar_mascara_limpa(config: dict) -> Path | None:
    """
    Procura o CSV limpo correspondente à observação e componente espectral.
    Exclui arquivos gerais com 'todos' no nome.
    """
    planeta = normalizar_texto(config["planeta"])
    instrumento = normalizar_texto(config["instrumento"])
    obs = normalizar_texto(config["obs"])
    parte = normalizar_texto(config["parte"])

    candidatos = []

    for arquivo in OUTPUTS.rglob("*_limpa.csv"):
        caminho_norm = normalizar_texto(str(arquivo))

        if "todos" in caminho_norm:
            continue

        if (
            planeta in caminho_norm
            and instrumento in caminho_norm
            and obs in caminho_norm
            and parte in caminho_norm
        ):
            candidatos.append(arquivo)

    if not candidatos:
        return None

    candidatos.sort(key=lambda caminho: len(str(caminho)))

    if len(candidatos) > 1:
        print("  AVISO: mais de uma máscara limpa encontrada.")
        for candidato in candidatos:
            print("   -", candidato)
        print("  Será usada:", candidatos[0])

    return candidatos[0]


def aplicar_mascara_branca(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Adiciona a flag usar_na_etapa_seguinte a partir da curva branca limpa."""
    arquivo_mascara = localizar_mascara_limpa(config)

    if arquivo_mascara is None:
        print("  Máscara branca limpa não localizada; todos os pontos começam como válidos.")
        df["usar_na_etapa_seguinte"] = True
        df["arquivo_mascara_branca"] = ""
        return df

    print("  Máscara branca usada:", arquivo_mascara)

    mascara = pd.read_csv(arquivo_mascara)
    chaves = ["segmento", "integration_index_segmento"]

    colunas_necessarias = chaves + ["usar_na_etapa_seguinte"]

    if not all(coluna in mascara.columns for coluna in colunas_necessarias):
        print("  AVISO: a máscara não contém todas as colunas necessárias.")
        df["usar_na_etapa_seguinte"] = True
        df["arquivo_mascara_branca"] = str(arquivo_mascara)
        return df

    mascara = mascara[colunas_necessarias].drop_duplicates(chaves)
    mascara["usar_na_etapa_seguinte"] = converter_booleano(
        mascara["usar_na_etapa_seguinte"]
    )

    df = df.merge(mascara, on=chaves, how="left")
    df["usar_na_etapa_seguinte"] = (
        df["usar_na_etapa_seguinte"]
        .fillna(True)
        .astype(bool)
    )
    df["arquivo_mascara_branca"] = str(arquivo_mascara)

    return df


def selecionar_bins(
    tabela_bins: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    """Seleciona apenas os bins da parte espectral atual."""
    selecionados = tabela_bins[
        (tabela_bins["instrumento"] == config["instrumento"])
        & (tabela_bins["parte"] == config["parte"])
        & tabela_bins["usar_bin"]
    ].copy()

    if "observacao" in selecionados.columns:
        obs_col = (
            selecionados["observacao"]
            .fillna("")
            .astype(str)
            .str.strip()
        )
        selecionados = selecionados[
            (obs_col == "") | (obs_col == config["obs"])
        ]

    return selecionados.sort_values("bin_id").reset_index(drop=True)


def processar_configuracao(
    config: dict,
    tabela_bins: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Processa uma das 12 combinações e retorna tabela detalhada e resumo."""
    planeta = config["planeta"]
    instrumento = config["instrumento"]
    obs = config["obs"]
    parte = config["parte"]
    hdu_index = config["hdu"]

    pasta_fits = RAW / planeta / instrumento / obs
    arquivos = sorted(
        pasta_fits.glob(f'{config["prefixo"]}{config["padrao"]}')
    )

    bins = selecionar_bins(tabela_bins, config)

    print("\n" + "=" * 90)
    print(f"{planeta} | {instrumento} | {obs} | {parte}")
    print(f"Arquivos x1dints encontrados: {len(arquivos)}")
    print(f"Bins ativos encontrados: {len(bins)}")

    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum x1dints encontrado em: {pasta_fits}"
        )

    if bins.empty:
        raise ValueError(
            f"Nenhum bin ativo encontrado para {instrumento} / {parte}."
        )

    linhas = []

    for arquivo in arquivos:
        segmento = extrair_segmento(arquivo.name)
        print(f"  Lendo {segmento}: {arquivo.name}")

        with fits.open(arquivo, memmap=True) as hdul:
            if hdu_index >= len(hdul):
                warnings.warn(
                    f"HDU {hdu_index} não existe em {arquivo.name}."
                )
                continue

            hdu = hdul[hdu_index]

            if hdu.data is None or not hasattr(hdu, "columns"):
                warnings.warn(
                    f"HDU {hdu_index} sem tabela válida em {arquivo.name}."
                )
                continue

            data = hdu.data
            colunas = list(hdu.columns.names)

            obrigatorias = ["WAVELENGTH", "FLUX", "FLUX_ERROR"]
            faltando = [col for col in obrigatorias if col not in colunas]

            if faltando:
                warnings.warn(
                    f"Colunas ausentes em {arquivo.name}: {faltando}"
                )
                continue

            for indice_integracao in range(len(data)):
                wave = np.asarray(
                    data["WAVELENGTH"][indice_integracao],
                    dtype=float,
                )
                flux = np.asarray(
                    data["FLUX"][indice_integracao],
                    dtype=float,
                )
                erro = np.asarray(
                    data["FLUX_ERROR"][indice_integracao],
                    dtype=float,
                )

                if "DQ" in colunas:
                    dq = np.asarray(data["DQ"][indice_integracao])
                else:
                    dq = np.zeros_like(flux, dtype=int)

                tempo, coluna_tempo = obter_tempo(
                    data,
                    colunas,
                    indice_integracao,
                )

                mascara_base = (
                    np.isfinite(wave)
                    & np.isfinite(flux)
                    & np.isfinite(erro)
                    & (dq == 0)
                )

                for _, bin_atual in bins.iterrows():
                    bin_id = int(bin_atual["bin_id"])
                    wmin = float(bin_atual["wavelength_min_um"])
                    wmax = float(bin_atual["wavelength_max_um"])
                    wcenter = float(bin_atual["wavelength_center_um"])
                    largura = float(bin_atual["bin_width_um"])

                    mascara_bin = (
                        mascara_base
                        & (wave >= wmin)
                        & (wave < wmax)
                    )

                    fluxo_integrado, erro_integrado, n_validos = (
                        integrar_trapezio(
                            wave[mascara_bin],
                            flux[mascara_bin],
                            erro[mascara_bin],
                        )
                    )

                    linhas.append({
                        "planeta": planeta,
                        "instrumento": instrumento,
                        "obs": obs,
                        "parte": parte,
                        "arquivo": arquivo.name,
                        "segmento": segmento,
                        "hdu": hdu_index,
                        "integration_index_segmento": indice_integracao,
                        "time_value": tempo,
                        "time_column": coluna_tempo,
                        "bin_id": bin_id,
                        "wavelength_min_um": wmin,
                        "wavelength_max_um": wmax,
                        "wavelength_center_um": wcenter,
                        "bin_width_um": largura,
                        "flux_bin_integrado": fluxo_integrado,
                        "flux_bin_error": erro_integrado,
                        "n_pixels_validos": n_validos,
                    })

    df = pd.DataFrame(linhas)

    if df.empty:
        raise RuntimeError(
            f"Nenhum dado integrado para {planeta}/{instrumento}/{parte}."
        )

    df = df.sort_values(
        [
            "bin_id",
            "time_value",
            "segmento",
            "integration_index_segmento",
        ]
    ).reset_index(drop=True)

    df["integration_index_global"] = df.groupby("bin_id").cumcount()

    # Normalização global por bin.
    df["flux_bin_normalizado"] = np.nan
    df["flux_bin_error_normalizado"] = np.nan

    for bin_id, grupo in df.groupby("bin_id"):
        mediana = np.nanmedian(grupo["flux_bin_integrado"])

        if np.isfinite(mediana) and mediana != 0:
            df.loc[grupo.index, "flux_bin_normalizado"] = (
                df.loc[grupo.index, "flux_bin_integrado"] / mediana
            )
            df.loc[grupo.index, "flux_bin_error_normalizado"] = (
                df.loc[grupo.index, "flux_bin_error"] / abs(mediana)
            )

    # Normalização por segmento mantida apenas como coluna diagnóstica.
    df["flux_bin_normalizado_segmento"] = np.nan
    df["flux_bin_error_normalizado_segmento"] = np.nan

    for (bin_id, segmento), grupo in df.groupby(["bin_id", "segmento"]):
        mediana_segmento = np.nanmedian(grupo["flux_bin_integrado"])

        if np.isfinite(mediana_segmento) and mediana_segmento != 0:
            df.loc[grupo.index, "flux_bin_normalizado_segmento"] = (
                df.loc[grupo.index, "flux_bin_integrado"]
                / mediana_segmento
            )
            df.loc[grupo.index, "flux_bin_error_normalizado_segmento"] = (
                df.loc[grupo.index, "flux_bin_error"]
                / abs(mediana_segmento)
            )

    df = aplicar_mascara_branca(df, config)

    df.loc[
        ~np.isfinite(df["flux_bin_integrado"]),
        "usar_na_etapa_seguinte",
    ] = False

    resumo = (
        df.groupby(
            [
                "planeta",
                "instrumento",
                "obs",
                "parte",
                "bin_id",
                "wavelength_min_um",
                "wavelength_max_um",
                "wavelength_center_um",
                "bin_width_um",
            ],
            as_index=False,
        )
        .agg(
            n_integracoes=("integration_index_global", "size"),
            n_integracoes_usadas=("usar_na_etapa_seguinte", "sum"),
            n_pixels_validos_mediana=("n_pixels_validos", "median"),
            fluxo_integrado_mediano=("flux_bin_integrado", "median"),
            erro_integrado_mediano=("flux_bin_error", "median"),
        )
    )

    return df, resumo


def salvar_resultados(
    config: dict,
    df: pd.DataFrame,
    resumo: pd.DataFrame,
) -> tuple[Path, Path]:
    """Salva o CSV detalhado e o resumo em uma pasta própria."""
    pasta_saida = (
        PASTA_SAIDA_GERAL
        / config["planeta"]
        / config["instrumento"]
        / config["parte"]
        / config["obs"]
    )
    pasta_saida.mkdir(parents=True, exist_ok=True)

    base_nome = (
        f'07_curvas_por_bin_{config["planeta"]}_'
        f'{config["instrumento"]}_{config["obs"]}_{config["parte"]}'
    )

    arquivo_detalhado = pasta_saida / f"{base_nome}.csv"
    arquivo_resumo = pasta_saida / f"{base_nome}_resumo.csv"

    df.to_csv(
        arquivo_detalhado,
        index=False,
        encoding="utf-8-sig",
    )
    resumo.to_csv(
        arquivo_resumo,
        index=False,
        encoding="utf-8-sig",
    )

    print("  CSV detalhado salvo em:", arquivo_detalhado)
    print("  Resumo salvo em:", arquivo_resumo)

    return arquivo_detalhado, arquivo_resumo


def gerar_grafico_didatico(df_exemplo: pd.DataFrame) -> Path:
    """Gera apenas um gráfico didático: b / SOSS / HDU3 / bin 1."""
    dados = df_exemplo[df_exemplo["bin_id"] == 1].copy()
    dados = dados.sort_values("integration_index_global")

    usados = dados[
        dados["usar_na_etapa_seguinte"]
        & np.isfinite(dados["flux_bin_normalizado"])
        & np.isfinite(dados["flux_bin_error_normalizado"])
    ]

    sinalizados = dados[~dados["usar_na_etapa_seguinte"]]

    wmin = float(dados["wavelength_min_um"].iloc[0])
    wmax = float(dados["wavelength_max_um"].iloc[0])
    centro = float(dados["wavelength_center_um"].iloc[0])

    plt.figure(figsize=(11, 5))

    plt.errorbar(
        usados["integration_index_global"],
        usados["flux_bin_normalizado"],
        yerr=usados["flux_bin_error_normalizado"],
        fmt=".",
        markersize=3,
        linewidth=0.6,
        elinewidth=0.4,
        capsize=0,
        label="Pontos mantidos",
    )

    if not sinalizados.empty:
        plt.plot(
            sinalizados["integration_index_global"],
            sinalizados["flux_bin_normalizado"],
            marker="x",
            linestyle="None",
            markersize=5,
            label="Integrações sinalizadas",
        )

    plt.xlabel("Índice global da integração")
    plt.ylabel("Fluxo do bin normalizado")
    plt.title(
        "Exemplo didático — TOI-2076 b | NIRISS/SOSS | obs10 | HDU3\n"
        f"Bin 1: {wmin:.2f}–{wmax:.2f} µm "
        f"(centro = {centro:.2f} µm)"
    )
    plt.legend()

    if len(usados) > 5:
        y = usados["flux_bin_normalizado"].to_numpy(dtype=float)
        inferior = np.nanpercentile(y, 0.5)
        superior = np.nanpercentile(y, 99.5)
        amplitude = superior - inferior

        if np.isfinite(amplitude) and amplitude > 0:
            margem = 0.15 * amplitude
            plt.ylim(inferior - margem, superior + margem)

    plt.tight_layout()

    arquivo = (
        PASTA_SAIDA_GERAL
        / "07_exemplo_didatico_TOI_2076_b_NIRISS_SOSS_obs10_HDU3_bin01.png"
    )

    plt.savefig(arquivo, dpi=150)
    plt.close()

    return arquivo


# ============================================================
# 4. EXECUÇÃO PRINCIPAL
# ============================================================

def main() -> None:
    print("=" * 90)
    print("ETAPA 07 — INTEGRAÇÃO DOS BINS EM ARQUIVOS SEPARADOS")
    print("=" * 90)
    print("Tabela de bins usada:", ARQUIVO_BINS)

    tabela_bins = pd.read_csv(ARQUIVO_BINS)

    colunas_bins = [
        "instrumento",
        "parte",
        "bin_id",
        "wavelength_min_um",
        "wavelength_max_um",
        "wavelength_center_um",
        "bin_width_um",
        "usar_bin",
    ]

    faltando = [
        coluna for coluna in colunas_bins
        if coluna not in tabela_bins.columns
    ]

    if faltando:
        raise ValueError(
            f"A tabela de bins não possui estas colunas: {faltando}"
        )

    tabela_bins["usar_bin"] = converter_booleano(
        tabela_bins["usar_bin"]
    )

    resumos_gerais = []
    exemplo_didatico = None

    for config in CONFIGURACOES:
        try:
            df, resumo = processar_configuracao(config, tabela_bins)
            salvar_resultados(config, df, resumo)
            resumos_gerais.append(resumo)

            if (
                config["planeta"] == "TOI-2076_b"
                and config["instrumento"] == "NIRISS_SOSS"
                and config["obs"] == "obs10"
                and config["parte"] == "HDU3"
            ):
                exemplo_didatico = df.copy()

        except Exception as erro:
            print("\nERRO nesta configuração:")
            print(config)
            print(erro)

    if not resumos_gerais:
        raise RuntimeError(
            "Nenhuma das 12 configurações foi processada com sucesso."
        )

    resumo_geral = pd.concat(
        resumos_gerais,
        ignore_index=True,
    )

    arquivo_resumo_geral = (
        PASTA_SAIDA_GERAL
        / "07_resumo_geral_bins.csv"
    )

    resumo_geral.to_csv(
        arquivo_resumo_geral,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n" + "=" * 90)
    print("RESUMO GERAL")
    print("=" * 90)
    print("Tabela-resumo geral salva em:")
    print(arquivo_resumo_geral)

    if exemplo_didatico is not None:
        arquivo_grafico = gerar_grafico_didatico(
            exemplo_didatico
        )
        print("\nGráfico didático salvo em:")
        print(arquivo_grafico)
    else:
        print(
            "\nAVISO: o caso didático não foi processado; "
            "nenhum gráfico foi gerado."
        )

    print("\nETAPA 07 FINALIZADA.")
    print(
        "Foram criados arquivos separados por planeta, "
        "instrumento, componente espectral e observação."
    )
    print(
        "Ainda não foi calculada a profundidade do trânsito."
    )


if __name__ == "__main__":
    main()
