"""
Sistema de Análise de Churn PCLs v2.0
Dashboard moderno e profissional para análise de retenção de laboratórios
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from typing import Optional, List, Dict, Any, Tuple
from io import BytesIO
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# Importar configurações
from config_churn import *

# Configuração da página
st.set_page_config(
    page_title="📊 Churn PCLs v2.0",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Dashboard de Análise de Churn v2.0 - Sistema profissional para monitoramento de retenção de PCLs"
    }
)

# CSS moderno e profissional
CSS_STYLES = """
<style>
    /* Tema profissional */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ca02c;
        --warning-color: #ff7f0e;
        --danger-color: #d62728;
        --info-color: #17a2b8;
        --light-bg: #f8f9fa;
        --dark-bg: #343a40;
        --border-radius: 8px;
        --shadow: 0 2px 4px rgba(0,0,0,0.1);
        --transition: all 0.3s ease;
    }

    /* Reset e base */
    * { box-sizing: border-box; }

    /* Header profissional */
    .main-header {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        padding: 2rem 1rem;
        border-radius: var(--border-radius);
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: var(--shadow);
    }

    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 300;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }

    /* Cards de métricas modernas */
    .metric-card {
        background: white;
        border-radius: var(--border-radius);
        padding: 1.5rem;
        box-shadow: var(--shadow);
        border: 1px solid #e9ecef;
        transition: var(--transition);
        text-align: center;
        margin-bottom: 1rem;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 0.5rem 0;
        color: var(--primary-color);
    }

    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 0;
    }

    .metric-delta {
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }

    .metric-delta.positive { color: var(--success-color); }
    .metric-delta.negative { color: var(--danger-color); }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    .status-alto { background-color: #fee; color: var(--danger-color); border: 1px solid #fcc; }
    .status-medio { background-color: #ffeaa7; color: var(--warning-color); border: 1px solid #ffeaa7; }
    .status-baixo { background-color: #d4edda; color: var(--success-color); border: 1px solid #c3e6cb; }
    .status-inativo { background-color: #f8f9fa; color: #6c757d; border: 1px solid #dee2e6; }

    /* Botões modernos */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        border: none;
        border-radius: var(--border-radius);
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: var(--transition);
        box-shadow: var(--shadow);
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }

    /* Sidebar moderna */
    .sidebar-header {
        background: var(--light-bg);
        padding: 1rem;
        border-radius: var(--border-radius);
        margin-bottom: 1rem;
        border-left: 4px solid var(--primary-color);
    }

    .sidebar-header h3 {
        margin: 0;
        color: var(--primary-color);
        font-size: 1.1rem;
        font-weight: 600;
    }

    /* Tabelas modernas */
    .dataframe-container {
        background: white;
        border-radius: var(--border-radius);
        padding: 1rem;
        box-shadow: var(--shadow);
        overflow: hidden;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: var(--light-bg);
        border-radius: var(--border-radius);
        font-weight: 600;
        color: var(--primary-color);
    }

    /* Loading states */
    .loading-container {
        text-align: center;
        padding: 3rem;
        color: #6c757d;
    }

    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid var(--primary-color);
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 0 auto 1rem;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* Responsividade */
    @media (max-width: 768px) {
        .metric-card {
            margin-bottom: 1rem;
        }
        .main-header h1 {
            font-size: 2rem;
        }
        .metric-value {
            font-size: 1.5rem;
        }
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--secondary-color);
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #6c757d;
        border-top: 1px solid #e9ecef;
        margin-top: 3rem;
    }

    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        :root {
            --light-bg: #2d3748;
            --dark-bg: #1a202c;
        }

        .metric-card {
            background: var(--dark-bg);
            border-color: #4a5568;
            color: white;
        }

        .metric-label {
            color: #a0aec0;
        }
    }
</style>
"""

# Injetar CSS
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# ========================================
# CLASSES DO SISTEMA v2.0
# ========================================

@dataclass
class KPIMetrics:
    """Classe para armazenar métricas calculadas."""
    total_labs: int = 0
    churn_rate: float = 0.0
    nrr: float = 0.0
    labs_em_risco: int = 0
    ativos_7d: float = 0.0
    ativos_30d: float = 0.0
    labs_alto_risco: int = 0
    labs_medio_risco: int = 0
    labs_baixo_risco: int = 0
    labs_inativos: int = 0

class DataManager:
    """Gerenciador de dados com cache inteligente."""

    @staticmethod
    @st.cache_data(ttl=CACHE_TTL)
    def carregar_dados_churn() -> Optional[pd.DataFrame]:
        """Carrega dados de análise de churn com cache inteligente."""
        try:
            arquivo_path = os.path.join(OUTPUT_DIR, CHURN_ANALYSIS_FILE)
            if os.path.exists(arquivo_path):
                df = pd.read_parquet(arquivo_path, engine='pyarrow')
                return df
            else:
                # Fallback para CSV
                arquivo_csv = os.path.join(OUTPUT_DIR, "churn_analysis_latest.csv")
                if os.path.exists(arquivo_csv):
                    df = pd.read_csv(arquivo_csv, encoding=ENCODING, low_memory=False)
                    return df
                else:
                    return None
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados: {e}")
            return None

    @staticmethod
    def preparar_dados(df: pd.DataFrame) -> pd.DataFrame:
        """Prepara e limpa os dados carregados."""
        if df is None or df.empty:
            return pd.DataFrame()

        # Garantir tipos de dados corretos
        if 'Data_Analise' in df.columns:
            df['Data_Analise'] = pd.to_datetime(df['Data_Analise'], errors='coerce')

        # Calcular volume total se não existir
        meses_2025 = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out']
        colunas_meses = [f'N_Coletas_{mes}_25' for mes in meses_2025]

        if 'Volume_Total_2025' not in df.columns:
            df['Volume_Total_2025'] = df[colunas_meses].sum(axis=1, skipna=True)

        return df

class FilterManager:
    """Gerenciador de filtros da interface."""

    def __init__(self):
        self.filtros = {}

    def renderizar_sidebar_filtros(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Renderiza todos os filtros na sidebar."""
        st.sidebar.markdown('<div class="sidebar-header"><h3>🔧 Filtros</h3></div>', unsafe_allow_html=True)

        filtros = {}

        # Filtro por Estado
        if 'Estado' in df.columns:
            filtros['estados'] = st.sidebar.multiselect(
                "🏛️ Estado",
                options=sorted(df['Estado'].dropna().unique()),
                default=sorted(df['Estado'].dropna().unique()),
                help="Selecione os estados para filtrar"
            )

        # Filtro por Representante
        if 'Representante_Nome' in df.columns:
            filtros['representantes'] = st.sidebar.multiselect(
                "👤 Representante",
                options=sorted(df['Representante_Nome'].dropna().unique()),
                default=sorted(df['Representante_Nome'].dropna().unique()),
                help="Selecione os representantes para filtrar"
            )

        # Filtro por Status de Risco
        if 'Status_Risco' in df.columns:
            filtros['status_risco'] = st.sidebar.multiselect(
                "⚠️ Status de Risco",
                options=sorted(df['Status_Risco'].dropna().unique()),
                default=sorted(df['Status_Risco'].dropna().unique()),
                help="Selecione os status de risco para filtrar"
            )

        # Filtro por período
        col1, col2 = st.sidebar.columns(2)
        with col1:
            filtros['data_inicio'] = st.sidebar.date_input(
                "📅 Data Início",
                value=datetime.now() - timedelta(days=30)
            )
        with col2:
            filtros['data_fim'] = st.sidebar.date_input(
                "📅 Data Fim",
                value=datetime.now()
            )

        # Busca textual
        filtros['busca_texto'] = st.sidebar.text_input(
            "🔍 Buscar por CNPJ/Nome/Cidade",
            help="Digite parte do CNPJ, nome do laboratório ou cidade"
        )

        self.filtros = filtros
        return filtros

    def aplicar_filtros(self, df: pd.DataFrame, filtros: Dict[str, Any]) -> pd.DataFrame:
        """Aplica todos os filtros ao DataFrame."""
        if df.empty:
            return df

        df_filtrado = df.copy()

        # Filtro por estados
        if filtros.get('estados'):
            df_filtrado = df_filtrado[df_filtrado['Estado'].isin(filtros['estados'])]

        # Filtro por representantes
        if filtros.get('representantes'):
            df_filtrado = df_filtrado[df_filtrado['Representante_Nome'].isin(filtros['representantes'])]

        # Filtro por status de risco
        if filtros.get('status_risco'):
            df_filtrado = df_filtrado[df_filtrado['Status_Risco'].isin(filtros['status_risco'])]

        # Filtro por período
        if 'Data_Analise' in df_filtrado.columns and filtros.get('data_inicio') and filtros.get('data_fim'):
            df_filtrado = df_filtrado[
                (df_filtrado['Data_Analise'].dt.date >= filtros['data_inicio']) &
                (df_filtrado['Data_Analise'].dt.date <= filtros['data_fim'])
            ]

        # Busca textual
        if filtros.get('busca_texto'):
            busca = filtros['busca_texto'].lower()
            mask = (
                df_filtrado['CNPJ_PCL'].astype(str).str.lower().str.contains(busca, na=False) |
                df_filtrado['Razao_Social_PCL'].astype(str).str.lower().str.contains(busca, na=False) |
                df_filtrado['Nome_Fantasia_PCL'].astype(str).str.lower().str.contains(busca, na=False) |
                df_filtrado['Cidade'].astype(str).str.lower().str.contains(busca, na=False)
            )
            df_filtrado = df_filtrado[mask]

        return df_filtrado

class KPIManager:
    """Gerenciador de cálculos de KPIs."""

    @staticmethod
    def calcular_kpis(df: pd.DataFrame) -> KPIMetrics:
        """Calcula todas as métricas principais."""
        if df.empty:
            return KPIMetrics()

        metrics = KPIMetrics()
        metrics.total_labs = len(df)

        # Distribuição por status de risco
        status_counts = df['Status_Risco'].value_counts()
        metrics.labs_alto_risco = status_counts.get('Alto', 0)
        metrics.labs_medio_risco = status_counts.get('Médio', 0)
        metrics.labs_baixo_risco = status_counts.get('Baixo', 0)
        metrics.labs_inativos = status_counts.get('Inativo', 0)

        # Churn Rate (Alto + Médio risco)
        labs_churn = metrics.labs_alto_risco + metrics.labs_medio_risco
        metrics.churn_rate = (labs_churn / metrics.total_labs * 100) if metrics.total_labs > 0 else 0

        # Labs em risco (todos exceto Baixo)
        metrics.labs_em_risco = metrics.total_labs - metrics.labs_baixo_risco

        # NRR (Net Revenue Retention)
        if 'Media_Coletas_Mensal_2024' in df.columns and 'Media_Coletas_Mensal_2025' in df.columns:
            media_2024 = df['Media_Coletas_Mensal_2024'].sum()
            media_2025 = df['Media_Coletas_Mensal_2025'].sum()
            metrics.nrr = (media_2025 / media_2024 * 100) if media_2024 > 0 else 100
        else:
            metrics.nrr = 100.0

        # Ativos recentes
        if 'Dias_Sem_Coleta' in df.columns:
            metrics.ativos_7d = (len(df[df['Dias_Sem_Coleta'] <= DIAS_ATIVO_REcente_7]) / metrics.total_labs * 100) if metrics.total_labs > 0 else 0
            metrics.ativos_30d = (len(df[df['Dias_Sem_Coleta'] <= DIAS_ATIVO_REcente_30]) / metrics.total_labs * 100) if metrics.total_labs > 0 else 0

        return metrics

class ChartManager:
    """Gerenciador de criação de gráficos."""

    @staticmethod
    def criar_grafico_distribuicao_risco(df: pd.DataFrame):
        """Cria gráfico de distribuição de risco."""
        if df.empty:
            st.info("📊 Nenhum dado disponível para o gráfico")
            return

        status_counts = df['Status_Risco'].value_counts()

        cores_map = {
            'Alto': '#d62728',
            'Médio': '#ff7f0e',
            'Baixo': '#2ca02c',
            'Inativo': '#9467bd'
        }

        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="📊 Distribuição de Risco dos Laboratórios",
            color=status_counts.index,
            color_discrete_map=cores_map
        )

        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>%{value} laboratórios<br>%{percent}'
        )

        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def criar_grafico_top_labs(df: pd.DataFrame, top_n: int = 10):
        """Cria gráfico dos top laboratórios por volume."""
        if df.empty:
            st.info("📊 Nenhum dado disponível para o gráfico")
            return

        # Garantir que Volume_Total_2025 existe
        if 'Volume_Total_2025' not in df.columns:
            meses_2025 = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out']
            colunas_meses = [f'N_Coletas_{mes}_25' for mes in meses_2025]
            df['Volume_Total_2025'] = df[colunas_meses].sum(axis=1, skipna=True)

        top_labs = df.nlargest(top_n, 'Volume_Total_2025')

        cores_map = {
            'Alto': '#d62728',
            'Médio': '#ff7f0e',
            'Baixo': '#2ca02c',
            'Inativo': '#9467bd'
        }

        fig = px.bar(
            top_labs,
            x='Volume_Total_2025',
            y='Nome_Fantasia_PCL',
            orientation='h',
            title=f"🏆 Top {top_n} Laboratórios por Volume (2025)",
            color='Status_Risco',
            color_discrete_map=cores_map,
            text='Volume_Total_2025'
        )

        fig.update_traces(
            texttemplate='%{text:.0f}',
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Volume: %{x:.0f} coletas<br>Status: %{marker.color}'
        )

        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            xaxis_title="Volume de Coletas",
            yaxis_title="Laboratório",
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def criar_grafico_evolucao_mensal(df: pd.DataFrame, lab_selecionado: str = None):
        """Cria gráfico de evolução mensal."""
        if df.empty:
            st.info("📊 Nenhum dado disponível para o gráfico")
            return

        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out']
        colunas_meses = [f'N_Coletas_{mes}_25' for mes in meses]

        if lab_selecionado:
            # Gráfico para laboratório específico
            lab_data = df[df['Nome_Fantasia_PCL'] == lab_selecionado]
            if not lab_data.empty:
                valores = [lab_data.iloc[0][col] for col in colunas_meses]

                fig = px.line(
                    x=meses,
                    y=valores,
                    title=f"📈 Evolução Mensal - {lab_selecionado}",
                    markers=True,
                    line_shape='spline'
                )

                fig.update_traces(
                    mode='lines+markers+text',
                    text=valores,
                    textposition="top center",
                    hovertemplate='<b>Mês:</b> %{x}<br><b>Coletas:</b> %{y}<extra></extra>'
                )

                fig.update_layout(
                    xaxis_title="Mês",
                    yaxis_title="Número de Coletas",
                    hovermode='x unified'
                )

                st.plotly_chart(fig, use_container_width=True)
        else:
            # Gráfico agregado
            valores_agregados = [df[col].sum() for col in colunas_meses]

            fig = px.line(
                x=meses,
                y=valores_agregados,
                title="📈 Evolução Mensal Agregada (2025)",
                markers=True,
                line_shape='spline'
            )

            fig.update_traces(
                mode='lines+markers+text',
                text=valores_agregados,
                textposition="top center",
                hovertemplate='<b>Mês:</b> %{x}<br><b>Total Coletas:</b> %{y}<extra></extra>'
            )

            fig.update_layout(
                xaxis_title="Mês",
                yaxis_title="Total de Coletas",
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def criar_heatmap_coletas(df: pd.DataFrame, top_n: int = 20):
        """Cria heatmap de coletas por mês para top laboratórios."""
        if df.empty:
            st.info("📊 Nenhum dado disponível para o heatmap")
            return

        # Garantir volume total
        if 'Volume_Total_2025' not in df.columns:
            meses_2025 = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out']
            colunas_meses = [f'N_Coletas_{mes}_25' for mes in meses_2025]
            df['Volume_Total_2025'] = df[colunas_meses].sum(axis=1, skipna=True)

        top_labs = df.nlargest(top_n, 'Volume_Total_2025')
        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out']
        colunas_meses = [f'N_Coletas_{mes}_25' for mes in meses]

        dados_heatmap = []
        for _, row in top_labs.iterrows():
            dados_heatmap.append([row[col] for col in colunas_meses])

        fig = px.imshow(
            dados_heatmap,
            labels=dict(x="Mês", y="Laboratório", color="Coletas"),
            x=meses,
            y=top_labs['Nome_Fantasia_PCL'].tolist(),
            title=f"🔥 Heatmap de Coletas - Top {top_n} Laboratórios",
            color_continuous_scale="Blues",
            aspect="auto"
        )

        fig.update_layout(
            xaxis=dict(side="top"),
            yaxis=dict(autorange="reversed")
        )

        st.plotly_chart(fig, use_container_width=True)

class UIManager:
    """Gerenciador da interface do usuário."""

    @staticmethod
    def renderizar_header():
        """Renderiza o cabeçalho principal."""
        st.markdown("""
        <div class="main-header">
            <h1>📊 Churn PCLs v2.0</h1>
            <p>Dashboard profissional para análise de retenção de laboratórios</p>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def renderizar_kpi_cards(metrics: KPIMetrics):
        """Renderiza cards de KPIs modernos."""
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{metrics.total_labs:,}</div>
                <div class="metric-label">Total Labs</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            delta_class = "positive" if metrics.churn_rate < 10 else "negative"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{metrics.churn_rate:.1f}%</div>
                <div class="metric-label">Churn Rate</div>
                <div class="metric-delta {delta_class}">{"↗️" if metrics.churn_rate > 10 else "↘️"}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            delta_class = "positive" if metrics.nrr > 95 else "negative"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{metrics.nrr:.1f}%</div>
                <div class="metric-label">NRR</div>
                <div class="metric-delta {delta_class}">{"↗️" if metrics.nrr > 95 else "↘️"}</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{metrics.labs_em_risco:,}</div>
                <div class="metric-label">Labs em Risco</div>
            </div>
            """, unsafe_allow_html=True)

        with col5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{metrics.ativos_7d:.1f}%</div>
                <div class="metric-label">Ativos 7d</div>
            </div>
            """, unsafe_allow_html=True)

    @staticmethod
    def renderizar_status_badge(status: str) -> str:
        """Renderiza um badge de status."""
        status_classes = {
            'Alto': 'status-alto',
            'Médio': 'status-medio',
            'Baixo': 'status-baixo',
            'Inativo': 'status-inativo'
        }
        return f'<span class="status-badge {status_classes.get(status, "status-inativo")}">{status}</span>'

    @staticmethod
    def criar_tabela_detalhada(df: pd.DataFrame, titulo: str = "📋 Dados Detalhados"):
        """Cria tabela detalhada com formatação moderna."""
        if df.empty:
            st.warning("⚠️ Nenhum dado disponível para exibição")
            return

        st.subheader(titulo)

        # Selecionar colunas principais
        colunas_principais = [
            'Nome_Fantasia_PCL', 'Estado', 'Cidade', 'Representante_Nome',
            'Status_Risco', 'Dias_Sem_Coleta', 'Variacao_Percentual',
            'Volume_Total_2025', 'Motivo_Risco'
        ]

        colunas_existentes = [col for col in colunas_principais if col in df.columns]
        df_exibicao = df[colunas_existentes].copy()

        # Formatação de colunas
        if 'Variacao_Percentual' in df_exibicao.columns:
            df_exibicao['Variacao_Percentual'] = df_exibicao['Variacao_Percentual'].round(2)

        if 'Volume_Total_2025' in df_exibicao.columns:
            df_exibicao['Volume_Total_2025'] = df_exibicao['Volume_Total_2025'].astype(int)

        # Renderizar tabela com container estilizado
        st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
        st.dataframe(
            df_exibicao,
            use_container_width=True,
            height=400,
            column_config={
                "Status_Risco": st.column_config.TextColumn(
                    "Status de Risco",
                    help="Classificação de risco do laboratório"
                ),
                "Variacao_Percentual": st.column_config.NumberColumn(
                    "Variação %",
                    format="%.2f%%",
                    help="Variação percentual em relação ao ano anterior"
                ),
                "Volume_Total_2025": st.column_config.NumberColumn(
                    "Volume 2025",
                    help="Total de coletas em 2025"
                )
            }
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Botões de download
        UIManager.renderizar_botoes_download(df_exibicao)

    @staticmethod
    def renderizar_botoes_download(df: pd.DataFrame):
        """Renderiza botões de download para os dados."""
        col1, col2 = st.columns(2)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        with col1:
            csv_data = df.to_csv(index=False, encoding=ENCODING)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"churn_analysis_{timestamp}.csv",
                mime="text/csv",
                key=f"download_csv_{timestamp}"
            )

        with col2:
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_data = excel_buffer.getvalue()
            st.download_button(
                label="📥 Download Excel",
                data=excel_data,
                file_name=f"churn_analysis_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"download_excel_{timestamp}"
            )

class ReportManager:
    """Gerenciador de geração de relatórios."""

    @staticmethod
    def gerar_relatorio_automatico(df: pd.DataFrame, metrics: KPIMetrics, tipo: str):
        """Gera relatório automático baseado no tipo."""
        if tipo == "semanal":
            ReportManager._gerar_relatorio_semanal(df, metrics)
        elif tipo == "mensal":
            ReportManager._gerar_relatorio_mensal(df, metrics)

    @staticmethod
    def _gerar_relatorio_semanal(df: pd.DataFrame, metrics: KPIMetrics):
        """Gera relatório semanal."""
        sumario = f"""
        📊 **Relatório Semanal de Churn - {datetime.now().strftime('%d/%m/%Y')}**

        **KPIs Principais:**
        • Churn Rate: {metrics.churn_rate:.1f}%
        • NRR: {metrics.nrr:.1f}%
        • Labs em Risco: {metrics.labs_em_risco:,}
        • Ativos (7d): {metrics.ativos_7d:.1f}%

        **Alertas:**
        • {metrics.labs_alto_risco:,} laboratórios em alto risco
        • {metrics.labs_medio_risco:,} laboratórios em médio risco

        **Recomendações:**
        • Focar nos {metrics.labs_alto_risco} labs de alto risco
        • Monitorar closely os {metrics.labs_medio_risco} labs de médio risco
        """

        st.success("✅ Relatório Semanal Gerado!")
        st.code(sumario, language="markdown")

        # Download do relatório
        st.download_button(
            "📥 Download Relatório Semanal",
            sumario,
            file_name=f"relatorio_semanal_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            key="download_relatorio_semanal"
        )

    @staticmethod
    def _gerar_relatorio_mensal(df: pd.DataFrame, metrics: KPIMetrics):
        """Gera relatório mensal detalhado."""
        # Calcular top variações
        if 'Variacao_Percentual' in df.columns:
            top_quedas = df.nsmallest(10, 'Variacao_Percentual')[['Nome_Fantasia_PCL', 'Variacao_Percentual', 'Estado']]
            top_recuperacoes = df.nlargest(10, 'Variacao_Percentual')[['Nome_Fantasia_PCL', 'Variacao_Percentual', 'Estado']]

        sumario = f"""
        📊 **Relatório Mensal de Churn - {datetime.now().strftime('%B/%Y').title()}**

        **KPIs Executivos:**
        • Total de Laboratórios: {metrics.total_labs:,}
        • Taxa de Churn: {metrics.churn_rate:.1f}%
        • Net Revenue Retention: {metrics.nrr:.1f}%
        • Laboratórios em Risco: {metrics.labs_em_risco:,}
        • Ativos (7 dias): {metrics.ativos_7d:.1f}%
        • Ativos (30 dias): {metrics.ativos_30d:.1f}%

        **Distribuição por Risco:**
        • Alto Risco: {metrics.labs_alto_risco:,} ({metrics.labs_alto_risco/metrics.total_labs*100:.1f}%)
        • Médio Risco: {metrics.labs_medio_risco:,} ({metrics.labs_medio_risco/metrics.total_labs*100:.1f}%)
        • Baixo Risco: {metrics.labs_baixo_risco:,} ({metrics.labs_baixo_risco/metrics.total_labs*100:.1f}%)
        • Inativos: {metrics.labs_inativos:,} ({metrics.labs_inativos/metrics.total_labs*100:.1f}%)

        **Análise de Tendências:**
        """

        if 'Variacao_Percentual' in df.columns:
            media_variacao = df['Variacao_Percentual'].mean()
            sumario += f"""
        • Variação Média: {media_variacao:.1f}%
        • Top Recuperações: {len(top_recuperacoes)} laboratórios
        • Top Quedas: {len(top_quedas)} laboratórios
            """

        st.success("✅ Relatório Mensal Gerado!")
        with st.expander("📋 Ver Relatório Completo", expanded=True):
            st.code(sumario, language="markdown")

        # Tabelas detalhadas
        if 'Variacao_Percentual' in df.columns:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📉 Top 10 Quedas")
                st.dataframe(top_quedas)
            with col2:
                st.subheader("📈 Top 10 Recuperações")
                st.dataframe(top_recuperacoes)

        # Download do relatório
        st.download_button(
            "📥 Download Relatório Mensal",
            sumario,
            file_name=f"relatorio_mensal_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            key="download_relatorio_mensal"
        )

def main():
    """Função principal do dashboard v2.0."""
    # Renderizar header
    UIManager.renderizar_header()

    # Carregar e preparar dados
    with st.spinner("🔄 Carregando dados..."):
        df_raw = DataManager.carregar_dados_churn()
        if df_raw is None:
            st.error("❌ Não foi possível carregar os dados. Execute o gerador de dados primeiro.")
            return

        df = DataManager.preparar_dados(df_raw)
        st.success(f"✅ Dados carregados: {len(df):,} laboratórios")

    # Indicador de última atualização
    if not df.empty and 'Data_Analise' in df.columns:
        ultima_atualizacao = df['Data_Analise'].max()
        st.markdown(f"**Última Atualização:** {ultima_atualizacao.strftime('%d/%m/%Y %H:%M:%S')}")

    # Inicializar gerenciadores
    filter_manager = FilterManager()

    # Sidebar com filtros
    filtros = filter_manager.renderizar_sidebar_filtros(df)

    # Aplicar filtros
    df_filtrado = filter_manager.aplicar_filtros(df, filtros)

    # Calcular KPIs
    metrics = KPIManager.calcular_kpis(df_filtrado)

    # Botão de refresh
    if st.sidebar.button("🔄 Atualizar Dados", help="Limpar cache e recarregar dados"):
        st.cache_data.clear()
        st.rerun()

    # Seção de relatórios na sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown('<div class="sidebar-header"><h3>📅 Relatórios</h3></div>', unsafe_allow_html=True)

    tipo_relatorio = st.sidebar.selectbox(
        "Tipo de Relatório",
        ["Semanal", "Mensal"],
        help="Selecione o tipo de relatório a gerar"
    )

    if st.sidebar.button("📊 Gerar Relatório", help="Gerar relatório automático"):
        ReportManager.gerar_relatorio_automatico(df_filtrado, metrics, tipo_relatorio.lower())

    # ========================================
    # ABAS PRINCIPAIS COM NOVA ORGANIZAÇÃO
    # ========================================
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏠 Visão Geral",
        "📋 Análise Detalhada",
        "👤 Por Representante",
        "📈 Tendências",
        "🔄 Visão 360°",
        "🏆 Rankings"
    ])

    # ========================================
    # ABA 1: VISÃO GERAL
    # ========================================
    with tab1:
        st.header("🏠 Visão Geral")

        # KPIs principais com cards modernos
        UIManager.renderizar_kpi_cards(metrics)

        # Expander com métricas detalhadas
        with st.expander("📊 Métricas Detalhadas", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📈 Distribuição por Status")
                ChartManager.criar_grafico_distribuicao_risco(df_filtrado)

            with col2:
                st.subheader("🏆 Top Laboratórios")
                ChartManager.criar_grafico_top_labs(df_filtrado, top_n=10)

        # Expander com variações
        with st.expander("📉 Top Quedas e Recuperações", expanded=False):
            if 'Variacao_Percentual' in df_filtrado.columns:
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📉 Maiores Quedas")
                    top_quedas = df_filtrado.nsmallest(10, 'Variacao_Percentual')[
                        ['Nome_Fantasia_PCL', 'Variacao_Percentual', 'Estado']
                    ]
                    st.dataframe(top_quedas, use_container_width=True)

                with col2:
                    st.subheader("📈 Maiores Recuperações")
                    top_recuperacoes = df_filtrado.nlargest(10, 'Variacao_Percentual')[
                        ['Nome_Fantasia_PCL', 'Variacao_Percentual', 'Estado']
                    ]
                    st.dataframe(top_recuperacoes, use_container_width=True)

        # Expander com laboratórios em risco
        with st.expander("🔴 Laboratórios em Alto Risco", expanded=False):
            labs_alto_risco = df_filtrado[df_filtrado['Status_Risco'] == 'Alto']
            if not labs_alto_risco.empty:
                colunas_resumo = ['Nome_Fantasia_PCL', 'Estado', 'Representante_Nome',
                                 'Dias_Sem_Coleta', 'Motivo_Risco']
                st.dataframe(
                    labs_alto_risco[colunas_resumo],
                    use_container_width=True,
                    height=300
                )
            else:
                st.success("✅ Nenhum laboratório em alto risco encontrado!")

    # ========================================
    # ABA 2: ANÁLISE DETALHADA
    # ========================================
    with tab2:
        st.header("📋 Análise Detalhada")

        # Filtros avançados
        with st.expander("🔍 Filtros Avançados", expanded=False):
            # Seleção de laboratório específico
            if not df_filtrado.empty:
                lab_selecionado = st.selectbox(
                    "📊 Análise Individual de Laboratório:",
                    options=[""] + sorted(df_filtrado['Nome_Fantasia_PCL'].unique()),
                    help="Selecione um laboratório para ver sua evolução mensal detalhada"
                )

                if lab_selecionado:
                    st.subheader(f"📈 Evolução Mensal - {lab_selecionado}")
                    ChartManager.criar_grafico_evolucao_mensal(df_filtrado, lab_selecionado)

        # Tabela completa de dados
        UIManager.criar_tabela_detalhada(df_filtrado, "📋 Dados Completos dos Laboratórios")

    # ========================================
    # ABA 3: ANÁLISE POR REPRESENTANTE
    # ========================================
    with tab3:
        st.header("👤 Análise por Representante")

        if not df_filtrado.empty and 'Representante_Nome' in df_filtrado.columns:
            # Seletor de representante
            representante_selecionado = st.selectbox(
                "👤 Selecione um Representante:",
                options=sorted(df_filtrado['Representante_Nome'].dropna().unique()),
                help="Filtrar análise por representante específico"
            )

            if representante_selecionado:
                # Filtrar dados do representante
                df_rep = df_filtrado[df_filtrado['Representante_Nome'] == representante_selecionado]

                # Calcular métricas do representante
                metrics_rep = KPIManager.calcular_kpis(df_rep)

                # KPIs do representante
                st.subheader(f"📊 Performance - {representante_selecionado}")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🏥 Total Labs", metrics_rep.total_labs)
                with col2:
                    st.metric("⚠️ Taxa Churn", f"{metrics_rep.churn_rate:.1f}%")
                with col3:
                    volume_total = df_rep['Volume_Total_2025'].sum() if 'Volume_Total_2025' in df_rep.columns else 0
                    st.metric("📦 Volume Total", f"{volume_total:,}")
                with col4:
                    variacao_media = df_rep['Variacao_Percentual'].mean() if 'Variacao_Percentual' in df_rep.columns else 0
                    st.metric("📈 Variação Média", f"{variacao_media:.1f}%")

                # Gráficos do representante
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📊 Distribuição de Risco")
                    ChartManager.criar_grafico_distribuicao_risco(df_rep)

                with col2:
                    st.subheader("🏆 Top Labs do Representante")
                    ChartManager.criar_grafico_top_labs(df_rep, top_n=5)

                # Tabela detalhada do representante
                UIManager.criar_tabela_detalhada(df_rep, f"🏥 Laboratórios - {representante_selecionado}")

    # ========================================
    # ABA 4: TENDÊNCIAS HISTÓRICAS
    # ========================================
    with tab4:
        st.header("📈 Tendências Históricas")

        # Evolução mensal agregada
        with st.expander("📈 Evolução Mensal Agregada", expanded=True):
            ChartManager.criar_grafico_evolucao_mensal(df_filtrado)

        # Comparativo ano a ano
        if ('Media_Coletas_Mensal_2024' in df_filtrado.columns and
            'Media_Coletas_Mensal_2025' in df_filtrado.columns):

            with st.expander("📊 Comparativo 2024 vs 2025", expanded=False):
                media_2024 = df_filtrado['Media_Coletas_Mensal_2024'].mean()
                media_2025 = df_filtrado['Media_Coletas_Mensal_2025'].mean()

                fig = go.Figure(data=[
                    go.Bar(
                        name='2024',
                        x=['Média Mensal'],
                        y=[media_2024],
                        marker_color='#1f77b4',
                        text=f'{media_2024:.1f}',
                        textposition='auto'
                    ),
                    go.Bar(
                        name='2025',
                        x=['Média Mensal'],
                        y=[media_2025],
                        marker_color='#ff7f0e',
                        text=f'{media_2025:.1f}',
                        textposition='auto'
                    )
                ])

                fig.update_layout(
                    title="📊 Comparativo de Médias Mensais",
                    xaxis_title="Período",
                    yaxis_title="Média de Coletas",
                    showlegend=True,
                    barmode='group'
                )

                st.plotly_chart(fig, use_container_width=True)

                # Indicador de variação
                variacao_yoy = ((media_2025 - media_2024) / media_2024 * 100) if media_2024 > 0 else 0
                delta_color = "normal" if variacao_yoy >= 0 else "inverse"
                st.metric(
                    "📈 Variação YoY",
                    f"{variacao_yoy:+.1f}%",
                    delta=f"{variacao_yoy:+.1f}%",
                    delta_color=delta_color
                )

        # Heatmap de coletas
        with st.expander("🔥 Heatmap de Coletas (Top 20)", expanded=False):
            ChartManager.criar_heatmap_coletas(df_filtrado, top_n=20)

    # ========================================
    # ABA 5: VISÃO 360°
    # ========================================
    with tab5:
        st.header("🔄 Visão 360° da Saúde dos PCLs")

        # Criar status composto para visão 360
        if not df_filtrado.empty:
            df_360 = df_filtrado.copy()
            if 'Tendencia' in df_360.columns and 'Status_Risco' in df_360.columns:
                df_360['Status_360'] = df_360.apply(
                    lambda row: f"{row['Tendencia']} - {row['Status_Risco']}",
                    axis=1
                )

                # Definir cores para diferentes combinações
                cores_360 = {
                    'Crescimento - Baixo': 'darkgreen',
                    'Crescimento - Médio': 'limegreen',
                    'Crescimento - Alto': 'lightgreen',
                    'Crescimento - Inativo': 'gray',
                    'Estável - Baixo': 'blue',
                    'Estável - Médio': 'lightblue',
                    'Estável - Alto': 'darkblue',
                    'Estável - Inativo': 'gray',
                    'Declínio - Baixo': 'orange',
                    'Declínio - Médio': 'darkorange',
                    'Declínio - Alto': 'red',
                    'Declínio - Inativo': 'darkred'
                }

                fig_360 = px.sunburst(
                    df_360,
                    path=['Estado', 'Representante_Nome', 'Nome_Fantasia_PCL'],
                    values='Volume_Total_2025',
                    color='Status_360',
                    color_discrete_map=cores_360,
                    title="🔄 Distribuição Hierárquica: Estado → Representante → Laboratório",
                    hover_data=['Variacao_Percentual', 'Dias_Sem_Coleta', 'Status_Risco']
                )

                fig_360.update_layout(margin=dict(t=50, l=0, r=0, b=0))
                st.plotly_chart(fig_360, use_container_width=True)

                # Legenda explicativa
                with st.expander("📖 Como Interpretar", expanded=False):
                    st.markdown("""
                    **🟢 Verde:** Laboratórios crescendo (tendência positiva)
                    **🔵 Azul:** Laboratórios estáveis
                    **🟠 Laranja:** Laboratórios em declínio mas ainda ativos
                    **🔴 Vermelho:** Laboratórios em declínio e alto risco
                    **⚫ Cinza:** Laboratórios inativos

                    **Hierarquia:**
                    - **Nível 1:** Estados brasileiros
                    - **Nível 2:** Representantes
                    - **Nível 3:** Laboratórios individuais

                    **Tamanho dos segmentos:** Representa o volume total de coletas
                    """)

    # ========================================
    # ABA 6: RANKINGS
    # ========================================
    with tab6:
        st.header("🏆 Rankings de Performance")

        if 'Variacao_Percentual' in df_filtrado.columns:
            # Rankings de variações
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📉 Maiores Quedas")
                top_quedas = df_filtrado.nsmallest(15, 'Variacao_Percentual')[
                    ['Nome_Fantasia_PCL', 'Variacao_Percentual', 'Estado', 'Representante_Nome']
                ].reset_index(drop=True)
                st.dataframe(top_quedas, use_container_width=True, height=400)

            with col2:
                st.subheader("📈 Maiores Recuperações")
                top_recuperacoes = df_filtrado.nlargest(15, 'Variacao_Percentual')[
                    ['Nome_Fantasia_PCL', 'Variacao_Percentual', 'Estado', 'Representante_Nome']
                ].reset_index(drop=True)
                st.dataframe(top_recuperacoes, use_container_width=True, height=400)

            # Gráfico comparativo
            st.subheader("📊 Distribuição de Variações")
            fig_variacao = px.histogram(
                df_filtrado,
                x='Variacao_Percentual',
                nbins=50,
                title="Distribuição das Variações Percentuais",
                labels={'Variacao_Percentual': 'Variação %', 'count': 'Número de Labs'},
                color_discrete_sequence=['#1f77b4']
            )
            fig_variacao.add_vline(
                x=0,
                line_dash="dash",
                line_color="red",
                annotation_text="Ponto de Equilíbrio"
            )
            st.plotly_chart(fig_variacao, use_container_width=True)

    # ========================================
    # RODAPÉ
    # ========================================
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <p>📊 <strong>Churn PCLs v2.0</strong> - Dashboard profissional de análise de retenção de laboratórios</p>
        <p>Desenvolvido com ❤️ para otimizar a gestão de relacionamento com PCLs</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
