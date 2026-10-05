# Desmatamento e Preservação Ambiental no Brasil

Projeto G1 da disciplina **Linguagem de Programação — Análise e Visualização de Dados com Python**.

**Autor:** Thalles Órion Volcov Pitz

## Sobre o projeto

Análise de 10 anos (2015 a 2024) de registros mensais de desmatamento em 20 estados brasileiros. O projeto mostra quanto se desmata, onde, e como a área desmatada se relaciona com queimadas, clima, emissões de CO₂ e nível de risco ambiental.

A base `simulacao_desmatamento_brasil.csv` é uma simulação criada para fins didáticos. Os resultados demonstram o processo de análise e não representam medições oficiais.

## Links

- Repositório: https://github.com/SEU-USUARIO/projeto-desmatamento-brasil
- Página do projeto: https://SEU-USUARIO.github.io/projeto-desmatamento-brasil/
- Dashboard: https://SEU-APP.streamlit.app

## O que o projeto tem

- Notebook com limpeza, engenharia de atributos, análise exploratória, KPIs, gráficos e conclusão
- Dashboard em Streamlit com filtros por período, região, bioma e nível de risco
- KPIs dinâmicos, análise temporal, comparativos e tabelas
- Gráficos com Matplotlib e Seaborn
- Mapa interativo com Plotly
- Banco SQLite com duas tabelas relacionadas (`estados` e `registros`), criado com SQLAlchemy
- Correlação estatística entre as variáveis
- Página de apresentação em HTML (GitHub Pages)

## Tecnologias

Python, Pandas, Matplotlib, Seaborn, Streamlit, Plotly, SQLAlchemy, SQLite e GitHub.

## Estrutura

```
projeto-desmatamento-brasil/
├── app.py
├── requirements.txt
├── README.md
├── index.html
├── dados/
│   └── simulacao_desmatamento_brasil.csv
├── database/
│   └── desmatamento.db
├── notebooks/
│   └── analise_desmatamento.ipynb
└── imagens/
```

## Como executar

```
pip install -r requirements.txt
streamlit run app.py
```

O banco `database/desmatamento.db` é criado automaticamente a partir do CSV caso ainda não exista.

## Principais resultados

- O total anual de desmatamento oscila entre 30,3 mil e 34,0 mil km², sem tendência clara.
- Na média por registro, as regiões ficam muito próximas. A Bahia (81,3 km²) e o Amazonas (75,9 km²) têm as maiores médias entre os estados.
- Cerca de 49,8% dos registros estão em risco Alto ou Crítico.
- As correlações entre o desmatamento e as demais variáveis são praticamente nulas nesta base.
