from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns
import streamlit as st
from sqlalchemy import Column, Float, ForeignKey, Integer, String, create_engine, text
from sqlalchemy.orm import declarative_base

AUTOR = "Thalles Órion Volcov Pitz"
PASTA = Path(__file__).parent
CSV = PASTA / "dados" / "simulacao_desmatamento_brasil.csv"
BANCO = PASTA / "database" / "desmatamento.db"

VERDE = "#2f6b4f"
ORDEM_RISCO = ["Baixo", "Médio", "Alto", "Crítico"]

COORDENADAS = {
    "AM": (-3.12, -60.02),
    "BA": (-12.97, -38.51),
    "CE": (-3.73, -38.52),
    "DF": (-15.79, -47.88),
    "ES": (-20.32, -40.34),
    "GO": (-16.68, -49.25),
    "MA": (-2.53, -44.30),
    "MG": (-19.92, -43.94),
    "MS": (-20.47, -54.62),
    "MT": (-15.60, -56.10),
    "PA": (-1.46, -48.50),
    "PB": (-7.12, -34.86),
    "PE": (-8.05, -34.88),
    "PR": (-25.43, -49.27),
    "RJ": (-22.91, -43.17),
    "RO": (-8.76, -63.90),
    "RS": (-30.03, -51.23),
    "SC": (-27.59, -48.55),
    "SP": (-23.55, -46.63),
    "TO": (-10.18, -48.33),
}

NOMES_CURTOS = {
    "area_desmatada_km2": "Desmatamento",
    "area_preservada_km2": "Área preservada",
    "focos_queimada": "Focos de queimada",
    "chuva_mm": "Chuva",
    "temperatura_media": "Temperatura",
    "emissoes_co2": "Emissões CO₂",
    "unidades_conservacao": "Unid. conservação",
}

Base = declarative_base()


class Estado(Base):
    __tablename__ = "estados"

    uf = Column(String(2), primary_key=True)
    regiao = Column(String(20), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)


class Registro(Base):
    __tablename__ = "registros"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    data = Column(String(10), nullable=False)
    uf = Column(String(2), ForeignKey("estados.uf"), nullable=False)
    bioma = Column(String(30))
    area_desmatada_km2 = Column(Float)
    area_preservada_km2 = Column(Float)
    focos_queimada = Column(Integer)
    chuva_mm = Column(Float)
    temperatura_media = Column(Float)
    emissoes_co2 = Column(Float)
    unidades_conservacao = Column(Integer)
    nivel_risco = Column(String(10))


@st.cache_resource
def obter_motor():
    BANCO.parent.mkdir(exist_ok=True)
    motor = create_engine(f"sqlite:///{BANCO.as_posix()}")
    Base.metadata.create_all(motor)

    with motor.connect() as conexao:
        total = conexao.execute(text("SELECT COUNT(*) FROM registros")).scalar()

    if total == 0:
        bruto = pd.read_csv(CSV, encoding="utf-8-sig")

        estados = bruto[["uf", "regiao"]].drop_duplicates().copy()
        estados["latitude"] = estados["uf"].map(lambda uf: COORDENADAS[uf][0])
        estados["longitude"] = estados["uf"].map(lambda uf: COORDENADAS[uf][1])
        estados.to_sql("estados", motor, if_exists="append", index=False)

        registros = bruto.drop(columns=["regiao"])
        registros.to_sql("registros", motor, if_exists="append", index=False)

    return motor


@st.cache_data
def carregar_dados():
    motor = obter_motor()
    consulta = """
        SELECT r.*, e.regiao, e.latitude, e.longitude
        FROM registros r
        JOIN estados e ON e.uf = r.uf
    """
    df = pd.read_sql(consulta, motor, parse_dates=["data"])
    df["taxa_desmatamento_pct"] = (
        df["area_desmatada_km2"]
        / (df["area_desmatada_km2"] + df["area_preservada_km2"])
        * 100
    )
    df["nivel_risco"] = pd.Categorical(df["nivel_risco"], categories=ORDEM_RISCO, ordered=True)
    return df


def numero(valor, casas=0):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def nova_figura(largura=7, altura=4):
    return plt.subplots(figsize=(largura, altura))


def mostrar(fig):
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


st.set_page_config(page_title="Desmatamento no Brasil", page_icon="🌳", layout="wide")
sns.set_theme(style="whitegrid")

df = carregar_dados()

st.title("🌳 Desmatamento e Preservação Ambiental no Brasil")
st.caption(f"Projeto G1 · Análise e Visualização de Dados com Python · Autor: {AUTOR}")

st.markdown(
    """
    ### O problema
    O desmatamento reduz a cobertura vegetal, aumenta as emissões de carbono e pressiona
    a biodiversidade. Este painel acompanha 20 estados brasileiros entre 2015 e 2024 e
    mostra como a área desmatada se relaciona com a área preservada, os focos de queimada,
    o clima, as emissões de CO₂ e o nível de risco ambiental.

    A base usada é uma **simulação** criada para fins didáticos. Os padrões exibidos aqui
    servem para praticar análise de dados e não representam medições oficiais.
    """
)

st.sidebar.header("Filtros")
ano_min, ano_max = int(df["ano"].min()), int(df["ano"].max())
periodo = st.sidebar.slider("Período", ano_min, ano_max, (ano_min, ano_max))

todas_regioes = sorted(df["regiao"].unique())
regioes = st.sidebar.multiselect("Região", todas_regioes, default=todas_regioes)

todos_biomas = sorted(df["bioma"].unique())
biomas = st.sidebar.multiselect("Bioma", todos_biomas, default=todos_biomas)

riscos = st.sidebar.multiselect("Nível de risco", ORDEM_RISCO, default=ORDEM_RISCO)

filtrado = df[
    df["ano"].between(periodo[0], periodo[1])
    & df["regiao"].isin(regioes)
    & df["bioma"].isin(biomas)
    & df["nivel_risco"].isin(riscos)
]

st.sidebar.markdown("---")
st.sidebar.write(f"**{numero(len(filtrado))}** registros selecionados de {numero(len(df))}")
st.sidebar.caption(f"Desenvolvido por {AUTOR}")

if len(filtrado) < 20:
    st.warning("Há poucos registros com esses filtros. Amplie a seleção na barra lateral.")
    st.stop()

st.header("Indicadores principais")

anual = filtrado.groupby("ano", as_index=False)["area_desmatada_km2"].sum()
variacao = None
if len(anual) >= 2:
    ultimo, anterior = anual["area_desmatada_km2"].iloc[-1], anual["area_desmatada_km2"].iloc[-2]
    variacao = (ultimo / anterior - 1) * 100

pct_risco_alto = filtrado["nivel_risco"].isin(["Alto", "Crítico"]).mean() * 100

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric(
    "Área desmatada (km²)",
    numero(filtrado["area_desmatada_km2"].sum()),
    delta=f"{variacao:+.1f}% vs ano anterior".replace(".", ",") if variacao is not None else None,
    delta_color="inverse",
)
k2.metric("Preservada por registro (km²)", numero(filtrado["area_preservada_km2"].mean()))
k3.metric("Focos de queimada", numero(filtrado["focos_queimada"].sum()))
k4.metric("Emissões de CO₂", numero(filtrado["emissoes_co2"].sum() / 1_000_000, 1) + " mi")
k5.metric("Risco Alto ou Crítico", numero(pct_risco_alto, 1) + "%")

aba_geral, aba_comparar, aba_clima, aba_mapa, aba_dados = st.tabs(
    ["Visão geral", "Comparativos", "Clima e correlação", "Mapa", "Dados"]
)

with aba_geral:
    st.subheader("Evolução ao longo do tempo")
    col_a, col_b = st.columns(2)

    with col_a:
        fig, eixo = nova_figura()
        sns.lineplot(data=anual, x="ano", y="area_desmatada_km2", marker="o", color=VERDE, ax=eixo)
        eixo.set_title("Área desmatada por ano")
        eixo.set_xlabel("Ano")
        eixo.set_ylabel("km²")
        eixo.set_xticks(anual["ano"])
        mostrar(fig)

    with col_b:
        mensal = filtrado.groupby("mes", as_index=False)["area_desmatada_km2"].mean()
        fig, eixo = nova_figura()
        sns.barplot(data=mensal, x="mes", y="area_desmatada_km2", color=VERDE, ax=eixo)
        eixo.set_title("Média de desmatamento por mês do ano")
        eixo.set_xlabel("Mês")
        eixo.set_ylabel("km² por registro")
        mostrar(fig)

    linha_pico = anual.loc[anual["area_desmatada_km2"].idxmax()]
    linha_vale = anual.loc[anual["area_desmatada_km2"].idxmin()]
    mes_forte = mensal.loc[mensal["area_desmatada_km2"].idxmax()]
    st.info(
        f"**Interpretação:** o maior total anual foi em {int(linha_pico['ano'])} "
        f"({numero(linha_pico['area_desmatada_km2'])} km²) e o menor em {int(linha_vale['ano'])} "
        f"({numero(linha_vale['area_desmatada_km2'])} km²). O mês com a maior média é o "
        f"{int(mes_forte['mes'])}, mas a diferença entre os meses é pequena, o que indica "
        f"pouca sazonalidade nesta base."
    )

with aba_comparar:
    st.subheader("Comparando regiões, estados, biomas e riscos")

    por_regiao = (
        filtrado.groupby("regiao", as_index=False)["area_desmatada_km2"]
        .mean()
        .sort_values("area_desmatada_km2", ascending=False)
    )
    por_uf = (
        filtrado.groupby("uf", as_index=False)["area_desmatada_km2"]
        .mean()
        .sort_values("area_desmatada_km2", ascending=False)
        .head(10)
    )
    por_bioma = (
        filtrado.groupby("bioma", as_index=False)["area_desmatada_km2"]
        .mean()
        .sort_values("area_desmatada_km2", ascending=False)
    )

    col_a, col_b = st.columns(2)
    with col_a:
        fig, eixo = nova_figura()
        sns.barplot(
            data=por_regiao, x="regiao", y="area_desmatada_km2",
            hue="regiao", palette="YlGn_r", legend=False, ax=eixo,
        )
        eixo.set_title("Média de desmatamento por região")
        eixo.set_xlabel("")
        eixo.set_ylabel("km² por registro")
        mostrar(fig)

    with col_b:
        fig, eixo = nova_figura()
        sns.barplot(
            data=por_uf, y="uf", x="area_desmatada_km2",
            hue="uf", palette="Reds_r", legend=False, ax=eixo,
        )
        eixo.set_title("10 estados com maior média de desmatamento")
        eixo.set_xlabel("km² por registro")
        eixo.set_ylabel("")
        mostrar(fig)

    col_c, col_d = st.columns(2)
    with col_c:
        fig, eixo = nova_figura()
        sns.barplot(
            data=por_bioma, y="bioma", x="area_desmatada_km2",
            hue="bioma", palette="Greens_r", legend=False, ax=eixo,
        )
        eixo.set_title("Média de desmatamento por bioma")
        eixo.set_xlabel("km² por registro")
        eixo.set_ylabel("")
        mostrar(fig)

    with col_d:
        fig, eixo = nova_figura()
        sns.countplot(
            data=filtrado, x="nivel_risco", order=ORDEM_RISCO,
            hue="nivel_risco", hue_order=ORDEM_RISCO, palette="YlOrRd", legend=False, ax=eixo,
        )
        eixo.set_title("Registros por nível de risco")
        eixo.set_xlabel("")
        eixo.set_ylabel("Quantidade")
        mostrar(fig)

    st.info(
        f"**Interpretação:** a região com maior média por registro é {por_regiao.iloc[0]['regiao']} "
        f"({numero(por_regiao.iloc[0]['area_desmatada_km2'], 1)} km²) e o estado líder é "
        f"{por_uf.iloc[0]['uf']} ({numero(por_uf.iloc[0]['area_desmatada_km2'], 1)} km²). "
        f"Entre os biomas, {por_bioma.iloc[0]['bioma']} aparece no topo. Comparei médias, e não "
        f"somas, porque alguns estados têm mais registros que outros e a soma favoreceria quem "
        f"tem mais linhas na base."
    )

with aba_clima:
    st.subheader("Clima, queimadas e correlação")

    colunas_numericas = list(NOMES_CURTOS.keys())
    correlacao = filtrado[colunas_numericas].corr().rename(index=NOMES_CURTOS, columns=NOMES_CURTOS)

    col_a, col_b = st.columns(2)
    with col_a:
        fig, eixo = nova_figura()
        sns.heatmap(correlacao, annot=True, fmt=".2f", cmap="RdYlGn_r", center=0, ax=eixo)
        eixo.set_title("Correlação entre as variáveis")
        mostrar(fig)

    with col_b:
        fig, eixo = nova_figura()
        sns.regplot(
            data=filtrado, x="chuva_mm", y="area_desmatada_km2",
            scatter_kws={"alpha": 0.25, "s": 12, "color": VERDE},
            line_kws={"color": "#c0392b"}, ax=eixo,
        )
        eixo.set_title("Chuva e desmatamento")
        eixo.set_xlabel("Chuva (mm)")
        eixo.set_ylabel("Área desmatada (km²)")
        mostrar(fig)

    focos = filtrado.pivot_table(index="mes", columns="ano", values="focos_queimada", aggfunc="mean")
    fig, eixo = nova_figura(11, 4)
    sns.heatmap(focos, cmap="YlOrRd", annot=True, fmt=".1f", linewidths=0.4, ax=eixo)
    eixo.set_title("Média de focos de queimada por mês e ano")
    eixo.set_xlabel("Ano")
    eixo.set_ylabel("Mês")
    mostrar(fig)

    com_desmatamento = correlacao["Desmatamento"].drop("Desmatamento")
    variavel_forte = com_desmatamento.abs().idxmax()
    valor_forte = com_desmatamento[variavel_forte]
    if abs(valor_forte) < 0.1:
        classe = "praticamente nula"
    elif abs(valor_forte) < 0.3:
        classe = "fraca"
    elif abs(valor_forte) < 0.6:
        classe = "moderada"
    else:
        classe = "forte"

    st.info(
        f"**Interpretação:** a variável mais ligada ao desmatamento é "
        f"{variavel_forte.lower()}, com correlação de {numero(valor_forte, 2)}, considerada {classe}. "
        f"Correlação baixa significa que, nesta base, nenhuma variável isolada explica bem a "
        f"variação do desmatamento. Isso é esperado em dados simulados e mostra a importância "
        f"de não concluir causalidade só a partir de gráficos."
    )

with aba_mapa:
    st.subheader("Desmatamento por estado")

    por_estado = (
        filtrado.groupby(["uf", "regiao", "latitude", "longitude"], as_index=False)
        .agg(
            media_desmatamento=("area_desmatada_km2", "mean"),
            total_desmatamento=("area_desmatada_km2", "sum"),
            focos=("focos_queimada", "sum"),
        )
    )

    mapa = px.scatter_geo(
        por_estado,
        lat="latitude",
        lon="longitude",
        size="media_desmatamento",
        color="media_desmatamento",
        hover_name="uf",
        hover_data={
            "regiao": True,
            "media_desmatamento": ":.1f",
            "total_desmatamento": ":,.0f",
            "focos": True,
            "latitude": False,
            "longitude": False,
        },
        color_continuous_scale="YlOrRd",
        size_max=35,
        labels={"media_desmatamento": "Média km²"},
    )
    mapa.update_geos(
        scope="south america",
        showcountries=True,
        showland=True,
        landcolor="#eef3ea",
        lataxis_range=[-35, 6],
        lonaxis_range=[-75, -32],
    )
    mapa.update_layout(height=600, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(mapa)

    estado_topo = por_estado.loc[por_estado["media_desmatamento"].idxmax()]
    st.info(
        f"**Interpretação:** cada círculo representa um estado, posicionado pela sua capital. "
        f"Quanto maior e mais escuro, maior a média de área desmatada por registro. No filtro "
        f"atual, o destaque é {estado_topo['uf']} ({numero(estado_topo['media_desmatamento'], 1)} km²)."
    )

with aba_dados:
    st.subheader("Tabela resumo por região")
    resumo = (
        filtrado.groupby("regiao")
        .agg(
            registros=("uf", "size"),
            desmatamento_total_km2=("area_desmatada_km2", "sum"),
            desmatamento_medio_km2=("area_desmatada_km2", "mean"),
            focos_queimada=("focos_queimada", "sum"),
            emissoes_co2=("emissoes_co2", "sum"),
        )
        .round(1)
        .reset_index()
    )
    st.dataframe(resumo, hide_index=True)

    st.subheader("Registros filtrados")
    colunas_tabela = [
        "data", "regiao", "uf", "bioma", "area_desmatada_km2", "area_preservada_km2",
        "focos_queimada", "chuva_mm", "temperatura_media", "emissoes_co2",
        "unidades_conservacao", "nivel_risco",
    ]
    st.dataframe(filtrado[colunas_tabela], hide_index=True)

    st.download_button(
        "Baixar dados filtrados (CSV)",
        filtrado[colunas_tabela].to_csv(index=False).encode("utf-8"),
        file_name="desmatamento_filtrado.csv",
        mime="text/csv",
    )

    with st.expander("Como os dados estão guardados"):
        st.write(
            "Os dados do CSV são carregados em um banco SQLite com duas tabelas ligadas pela "
            "coluna uf: `estados` (região e coordenadas) e `registros` (as medições). "
            "O painel lê tudo com um JOIN entre elas."
        )
        st.code(
            "SELECT r.*, e.regiao, e.latitude, e.longitude\n"
            "FROM registros r\n"
            "JOIN estados e ON e.uf = r.uf",
            language="sql",
        )

st.header("Conclusão executiva")

regiao_lider = por_regiao.iloc[0]["regiao"]
uf_lider = por_uf.iloc[0]["uf"]
st.success(
    f"""
    - No recorte selecionado ({periodo[0]} a {periodo[1]}), foram desmatados **{numero(filtrado['area_desmatada_km2'].sum())} km²**,
      com pico em **{int(linha_pico['ano'])}**.
    - **{regiao_lider}** tem a maior média por registro entre as regiões, e **{uf_lider}** lidera entre os estados.
    - **{numero(pct_risco_alto, 1)}%** dos registros estão em risco Alto ou Crítico, o que pede monitoramento contínuo.
    - As correlações com o desmatamento são {classe}s, então nenhum fator climático ou de queimadas
      explica sozinho o problema.
    - Como a base é simulada, o próximo passo natural é repetir a análise com dados oficiais
      (por exemplo, do INPE/PRODES) para validar essas conclusões.
    """
)

st.caption(f"© {AUTOR} · Projeto G1 · Linguagem de Programação")
