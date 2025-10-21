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

        # Debug: mostrar colunas disponíveis
        if st.sidebar.checkbox("🔍 Mostrar Debug", help="Exibir informações de debug"):
            st.sidebar.write(f"Total de colunas: {len(df.columns)}")
            
            # Verificar se campos de cidade e estado existem
            if 'Estado' in df.columns:
                st.sidebar.write(f"✅ Estado: {df['Estado'].nunique()} valores únicos")
            else:
                st.sidebar.write("❌ Campo 'Estado' não encontrado")
                
            if 'Cidade' in df.columns:
                st.sidebar.write(f"✅ Cidade: {df['Cidade'].nunique()} valores únicos")
            else:
                st.sidebar.write("❌ Campo 'Cidade' não encontrado")

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

        # NRR removido conforme solicitação

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
        """Cria gráfico dos laboratórios em risco prioritários."""
        if df.empty:
            st.info("📊 Nenhum dado disponível para o gráfico")
            return

        # Filtrar apenas labs em risco (Alto, Médio, Inativo)
        labs_risco = df[df['Status_Risco'].isin(['Alto', 'Médio', 'Inativo'])].copy()
        
        if labs_risco.empty:
            st.info("✅ Nenhum laboratório em risco encontrado!")
            return

        # Ordenar por prioridade: Score de risco (se disponível) ou dias sem coleta
        if 'Score_Risco' in labs_risco.columns:
            labs_risco = labs_risco.sort_values(['Score_Risco', 'Dias_Sem_Coleta'], ascending=[False, False])
        else:
            labs_risco = labs_risco.sort_values('Dias_Sem_Coleta', ascending=False)
        
        top_labs_risco = labs_risco.head(top_n)

        cores_map = {
            'Alto': '#d62728',
            'Médio': '#ff7f0e',
            'Baixo': '#2ca02c',
            'Inativo': '#9467bd'
        }

        # Usar dias sem coleta como métrica principal
        fig = px.bar(
            top_labs_risco,
            x='Dias_Sem_Coleta',
            y='Nome_Fantasia_PCL',
            orientation='h',
            title=f"🚨 Top {top_n} Laboratórios em Risco",
            color='Status_Risco',
            color_discrete_map=cores_map,
            text='Dias_Sem_Coleta'
        )

        fig.update_traces(
            texttemplate='%{text:.0f}',
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Dias sem coleta: %{x:.0f}<br>Status: %{marker.color}'
        )

        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            xaxis_title="Dias sem Coleta",
            yaxis_title="Laboratório",
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def criar_grafico_media_diaria(df: pd.DataFrame, lab_selecionado: str = None):
        """Cria gráfico de média diária por mês."""
        if df.empty:
            st.info("📊 Nenhum dado disponível para o gráfico")
            return

        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out']
        colunas_meses = [f'N_Coletas_{mes}_25' for mes in meses]
        
        if lab_selecionado:
            lab_data = df[df['Nome_Fantasia_PCL'] == lab_selecionado]
            if not lab_data.empty:
                lab = lab_data.iloc[0]
                valores_mensais = [lab[col] for col in colunas_meses]
                
                # Calcular média diária (assumindo 30 dias por mês)
                dias_por_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31]  # Jan-Out
                medias_diarias = [val / dias for val, dias in zip(valores_mensais, dias_por_mes)]
                
                fig = px.bar(
                    x=meses,
                    y=medias_diarias,
                    title=f"📊 Média Diária por Mês - {lab_selecionado}",
                    color=medias_diarias,
                    color_continuous_scale='Blues'
                )
                
                fig.update_traces(
                    hovertemplate='<b>Mês:</b> %{x}<br><b>Média Diária:</b> %{y:.1f} coletas<extra></extra>'
                )
                
                fig.update_layout(
                    xaxis_title="Mês",
                    yaxis_title="Média Diária (Coletas)",
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def criar_grafico_coletas_por_dia(df: pd.DataFrame, lab_selecionado: str = None):
        """Cria gráfico de coletas por dia do mês (0-31)."""
        if df.empty:
            st.info("📊 Nenhum dado disponível para o gráfico")
            return

        if lab_selecionado:
            lab_data = df[df['Nome_Fantasia_PCL'] == lab_selecionado]
            if not lab_data.empty:
                lab = lab_data.iloc[0]
                
                # Simular distribuição de coletas por dia (baseado no volume mensal)
                meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out']
                colunas_meses = [f'N_Coletas_{mes}_25' for mes in meses]
                valores_mensais = [lab[col] for col in colunas_meses]
                
                # Criar dados simulados para cada dia do mês
                dias = list(range(1, 32))
                dados_grafico = []
                
                for i, (mes, volume) in enumerate(zip(meses, valores_mensais)):
                    # Simular distribuição uniforme por dia (pode ser melhorado com dados reais)
                    coletas_por_dia = volume / 30 if volume > 0 else 0
                    for dia in dias:
                        # Adicionar alguma variação aleatória
                        import random
                        variacao = random.uniform(0.5, 1.5)
                        coletas_dia = max(0, coletas_por_dia * variacao)
                        dados_grafico.append({
                            'Dia': dia,
                            'Mês': mes,
                            'Coletas': coletas_dia
                        })
                
                df_grafico = pd.DataFrame(dados_grafico)
                
                # Criar gráfico de linha múltipla
                fig = px.line(
                    df_grafico,
                    x='Dia',
                    y='Coletas',
                    color='Mês',
                    title=f"📅 Coletas por Dia do Mês - {lab_selecionado}",
                    markers=True
                )
                
                fig.update_traces(
                    hovertemplate='<b>Dia:</b> %{x}<br><b>Mês:</b> %{legendgroup}<br><b>Coletas:</b> %{y:.1f}<extra></extra>'
                )
                
                fig.update_layout(
                    xaxis_title="Dia do Mês (1-31)",
                    yaxis_title="Número de Coletas",
                    xaxis=dict(tickmode='linear', tick0=1, dtick=5),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.3,
                        xanchor="center",
                        x=0.5
                    )
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
                lab = lab_data.iloc[0]
                valores_2025 = [lab[col] for col in colunas_meses]
                
                # Dados 2024 se disponíveis
                colunas_2024 = [f'N_Coletas_{mes}_24' for mes in meses]
                valores_2024 = [lab[col] if col in lab.index else 0 for col in colunas_2024]
                
                # Calcular médias
                media_2025 = sum(valores_2025) / len(valores_2025) if valores_2025 else 0
                media_2024 = sum(valores_2024) / len(valores_2024) if valores_2024 else 0
                
                # Criar DataFrame para o gráfico
                df_grafico = pd.DataFrame({
                    'Mês': meses,
                    '2025': valores_2025,
                    '2024': valores_2024,
                    'Média 2025': [media_2025] * len(meses),
                    'Média 2024': [media_2024] * len(meses)
                })
                
                # Criar gráfico com múltiplas linhas
                fig = px.line(
                    df_grafico,
                    x='Mês',
                    y=['2025', '2024', 'Média 2025', 'Média 2024'],
                    title=f"📈 Evolução Mensal - {lab_selecionado}",
                    markers=True,
                    line_shape='spline'
                )
                
                # Personalizar cores e estilos
                fig.update_traces(
                    mode='lines+markers',
                    hovertemplate='<b>Mês:</b> %{x}<br><b>Coletas:</b> %{y}<extra></extra>'
                )
                
                # Cores personalizadas
                fig.data[0].line.color = '#1f77b4'  # Azul para 2025
                fig.data[1].line.color = '#ff7f0e'  # Laranja para 2024
                fig.data[2].line.color = '#1f77b4'   # Azul claro para média 2025
                fig.data[2].line.dash = 'dash'
                fig.data[3].line.color = '#ff7f0e'   # Laranja claro para média 2024
                fig.data[3].line.dash = 'dash'

                fig.update_layout(
                    xaxis_title="Mês",
                    yaxis_title="Número de Coletas",
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.2,
                        xanchor="center",
                        x=0.5
                    )
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
        col1, col2, col3, col4 = st.columns(4)

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
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{metrics.labs_em_risco:,}</div>
                <div class="metric-label">Labs em Risco</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            delta_class = "positive" if metrics.ativos_7d > 80 else "negative"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{metrics.ativos_7d:.1f}%</div>
                <div class="metric-label">Ativos 7D</div>
                <div class="metric-delta {delta_class}">{"↗️" if metrics.ativos_7d > 80 else "↘️"}</div>
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

        # Selecionar colunas principais com análises inteligentes
        colunas_principais = [
            'Nome_Fantasia_PCL', 'Estado', 'Cidade', 'Representante_Nome',
            'Status_Risco', 'Dias_Sem_Coleta', 'Variacao_Percentual',
            'Volume_Atual_2025', 'Volume_Maximo_2024', 'Tendencia_Volume',
            'Score_Risco', 'Motivo_Risco', 'Insights_Automaticos'
        ]

        colunas_existentes = [col for col in colunas_principais if col in df.columns]
        df_exibicao = df[colunas_existentes].copy()

        # Formatação de colunas
        if 'Variacao_Percentual' in df_exibicao.columns:
            df_exibicao['Variacao_Percentual'] = df_exibicao['Variacao_Percentual'].round(2)

        if 'Volume_Atual_2025' in df_exibicao.columns:
            df_exibicao['Volume_Atual_2025'] = df_exibicao['Volume_Atual_2025'].astype(int)
            
        if 'Volume_Maximo_2024' in df_exibicao.columns:
            df_exibicao['Volume_Maximo_2024'] = df_exibicao['Volume_Maximo_2024'].astype(int)
            
        if 'Score_Risco' in df_exibicao.columns:
            df_exibicao['Score_Risco'] = df_exibicao['Score_Risco'].astype(int)

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
                "Volume_Atual_2025": st.column_config.NumberColumn(
                    "Volume Atual 2025",
                    help="Volume atual de coletas em 2025"
                ),
                "Volume_Maximo_2024": st.column_config.NumberColumn(
                    "Volume Máximo 2024",
                    help="Volume máximo de coletas em 2024"
                ),
                "Tendencia_Volume": st.column_config.TextColumn(
                    "Tendência",
                    help="Tendência de volume (Crescimento/Declínio/Estável)"
                ),
                "Score_Risco": st.column_config.NumberColumn(
                    "Score Risco",
                    help="Score de risco de 0-100"
                ),
                "Insights_Automaticos": st.column_config.TextColumn(
                    "Insights",
                    help="Insights automáticos gerados pelo sistema"
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

class MetricasAvancadas:
    """Classe para métricas avançadas de laboratórios."""
    
    @staticmethod
    def calcular_metricas_lab(df: pd.DataFrame, lab_nome: str) -> dict:
        """Calcula métricas avançadas para um laboratório específico."""
        lab_data = df[df['Nome_Fantasia_PCL'] == lab_nome]
        
        if lab_data.empty:
            return {}
        
        lab = lab_data.iloc[0]
        
        # Total de coletas 2025
        meses_2025 = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out']
        colunas_2025 = [f'N_Coletas_{mes}_25' for mes in meses_2025]
        total_coletas_2025 = lab[colunas_2025].sum() if all(col in lab.index for col in colunas_2025) else 0
        
        # Média dos últimos 3 meses
        ultimos_3_meses = ['Ago', 'Set', 'Out']
        colunas_3_meses = [f'N_Coletas_{mes}_25' for mes in ultimos_3_meses]
        media_3_meses = lab[colunas_3_meses].mean() if all(col in lab.index for col in colunas_3_meses) else 0
        
        # Média diária (últimos 3 meses)
        dias_3_meses = 90  # Aproximadamente 3 meses
        media_diaria = media_3_meses / 30 if media_3_meses > 0 else 0
        
        # Agudo (7 dias) - coletas nos últimos 7 dias
        dias_sem_coleta = lab.get('Dias_Sem_Coleta', 0)
        agudo = "Ativo" if dias_sem_coleta <= 7 else "Inativo"
        
        # Crônico (fechamentos mensais) - baseado na variação
        variacao = lab.get('Variacao_Percentual', 0)
        if variacao > 20:
            cronico = "Crescimento"
        elif variacao < -20:
            cronico = "Declínio"
        else:
            cronico = "Estável"
        
        return {
            'total_coletas': int(total_coletas_2025),
            'media_3_meses': round(media_3_meses, 1),
            'media_diaria': round(media_diaria, 1),
            'agudo': agudo,
            'cronico': cronico,
            'dias_sem_coleta': int(dias_sem_coleta),
            'variacao_percentual': round(variacao, 1)
        }

class AnaliseInteligente:
    """Classe para análises inteligentes e insights automáticos."""
    
    @staticmethod
    def calcular_insights_automaticos(df: pd.DataFrame) -> pd.DataFrame:
        """Calcula insights automáticos para cada laboratório."""
        df_insights = df.copy()
        
        # Volume atual (último mês disponível)
        df_insights['Volume_Atual_2025'] = df_insights.get('N_Coletas_Out_25', 0)
        
        # Volume máximo do ano passado
        colunas_2024 = [col for col in df_insights.columns if 'N_Coletas_' in col and '24' in col]
        if colunas_2024:
            df_insights['Volume_Maximo_2024'] = df_insights[colunas_2024].max(axis=1)
        else:
            df_insights['Volume_Maximo_2024'] = 0
        
        # Tendência de volume (comparação atual vs máximo histórico)
        df_insights['Tendencia_Volume'] = df_insights.apply(
            lambda row: 'Crescimento' if row['Volume_Atual_2025'] > row['Volume_Maximo_2024'] 
            else 'Declínio' if row['Volume_Atual_2025'] < row['Volume_Maximo_2024'] * 0.5
            else 'Estável', axis=1
        )
        
        # Score de risco (0-100)
        df_insights['Score_Risco'] = df_insights.apply(
            lambda row: AnaliseInteligente._calcular_score_risco(row), axis=1
        )
        
        # Insights automáticos
        df_insights['Insights_Automaticos'] = df_insights.apply(
            lambda row: AnaliseInteligente._gerar_insights(row), axis=1
        )
        
        return df_insights
    
    @staticmethod
    def _calcular_score_risco(row) -> int:
        """Calcula score de risco de 0-100."""
        score = 0
        
        # Dias sem coleta (peso 40%)
        dias_sem = row.get('Dias_Sem_Coleta', 0)
        if dias_sem > 90:
            score += 40
        elif dias_sem > 60:
            score += 30
        elif dias_sem > 30:
            score += 20
        elif dias_sem > 15:
            score += 10
        
        # Variação percentual (peso 30%)
        variacao = row.get('Variacao_Percentual', 0)
        if variacao < -80:
            score += 30
        elif variacao < -50:
            score += 25
        elif variacao < -20:
            score += 15
        elif variacao < 0:
            score += 10
        
        # Volume atual vs histórico (peso 30%)
        volume_atual = row.get('Volume_Atual_2025', 0)
        volume_max = row.get('Volume_Maximo_2024', 1)
        if volume_max > 0:
            ratio = volume_atual / volume_max
            if ratio < 0.2:
                score += 30
            elif ratio < 0.5:
                score += 20
            elif ratio < 0.8:
                score += 10
        
        return min(score, 100)
    
    @staticmethod
    def _gerar_insights(row) -> str:
        """Gera insights automáticos baseados nos dados."""
        insights = []
        
        # Análise de dias sem coleta
        dias_sem = row.get('Dias_Sem_Coleta', 0)
        if dias_sem > 90:
            insights.append("🚨 CRÍTICO: Sem coletas há mais de 3 meses")
        elif dias_sem > 60:
            insights.append("⚠️ ALERTA: Sem coletas há mais de 2 meses")
        elif dias_sem > 30:
            insights.append("📉 ATENÇÃO: Sem coletas há mais de 1 mês")
        
        # Análise de volume
        volume_atual = row.get('Volume_Atual_2025', 0)
        volume_max = row.get('Volume_Maximo_2024', 0)
        if volume_max > 0:
            ratio = volume_atual / volume_max
            if ratio > 1.5:
                insights.append("📈 EXCELENTE: Volume 50% acima do histórico")
            elif ratio > 1.2:
                insights.append("📊 POSITIVO: Volume 20% acima do histórico")
            elif ratio < 0.3:
                insights.append("📉 CRÍTICO: Volume 70% abaixo do histórico")
            elif ratio < 0.6:
                insights.append("⚠️ ALERTA: Volume 40% abaixo do histórico")
        
        # Análise de tendência
        variacao = row.get('Variacao_Percentual', 0)
        if variacao > 100:
            insights.append("🚀 CRESCIMENTO: Variação superior a 100%")
        elif variacao > 50:
            insights.append("📈 POSITIVO: Variação superior a 50%")
        elif variacao < -80:
            insights.append("📉 CRÍTICO: Queda superior a 80%")
        elif variacao < -50:
            insights.append("⚠️ ALERTA: Queda superior a 50%")
        
        return " | ".join(insights) if insights else "✅ Estável"
    
    @staticmethod
    def criar_dashboard_inteligente(df: pd.DataFrame):
        """Cria dashboard com análises inteligentes."""
        st.subheader("🧠 Análises Inteligentes")
        
        # Métricas de alto nível
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            labs_criticos = len(df[df['Score_Risco'] > 80])
            st.metric("🚨 Labs Críticos", labs_criticos, 
                     delta=f"{labs_criticos/len(df)*100:.1f}%" if len(df) > 0 else "0%")
        
        with col2:
            labs_crescimento = len(df[df['Tendencia_Volume'] == 'Crescimento'])
            st.metric("📈 Labs em Crescimento", labs_crescimento,
                     delta=f"{labs_crescimento/len(df)*100:.1f}%" if len(df) > 0 else "0%")
        
        with col3:
            score_medio = df['Score_Risco'].mean() if 'Score_Risco' in df.columns else 0
            st.metric("📊 Score Médio", f"{score_medio:.1f}/100")
        
        with col4:
            labs_estaveis = len(df[df['Tendencia_Volume'] == 'Estável'])
            st.metric("⚖️ Labs Estáveis", labs_estaveis,
                     delta=f"{labs_estaveis/len(df)*100:.1f}%" if len(df) > 0 else "0%")
        
        # Gráfico de distribuição de risco
        if 'Score_Risco' in df.columns:
            st.subheader("📊 Distribuição de Risco")
            fig = px.histogram(df, x='Score_Risco', nbins=20, 
                              title="Distribuição do Score de Risco",
                              labels={'Score_Risco': 'Score de Risco', 'count': 'Número de Labs'})
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # Top insights automáticos
        st.subheader("💡 Insights Automáticos")
        if 'Insights_Automaticos' in df.columns:
            insights_df = df[['Nome_Fantasia_PCL', 'Score_Risco', 'Insights_Automaticos']].copy()
            insights_df = insights_df[insights_df['Score_Risco'] > 50].sort_values('Score_Risco', ascending=False)
            
            if not insights_df.empty:
                st.dataframe(insights_df, use_container_width=True)
            else:
                st.success("✅ Nenhum laboratório com insights críticos!")

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

    # Calcular análises inteligentes
    df_filtrado = AnaliseInteligente.calcular_insights_automaticos(df_filtrado)

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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🏠 Visão Geral",
        "📋 Análise Detalhada",
        "👤 Por Representante",
        "📈 Tendências",
        "🔄 Visão 360°",
        "🏆 Rankings",
        "🧠 Análises Inteligentes"
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
                st.subheader("🚨 Labs em Risco")
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
        with st.expander("🔍 Filtros Avançados", expanded=True):
            # Seleção de laboratório específico
            if not df_filtrado.empty:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Campo de busca por CNPJ ou nome
                    busca_lab = st.text_input(
                        "🔍 Buscar por CNPJ ou Nome:",
                        placeholder="Digite CNPJ ou nome do laboratório...",
                        help="Digite CNPJ (apenas números) ou nome do laboratório"
                    )
                
                with col2:
                    # Seleção por dropdown como alternativa
                    lab_selecionado = st.selectbox(
                        "📊 Ou selecione:",
                        options=[""] + sorted(df_filtrado['Nome_Fantasia_PCL'].unique()),
                        help="Selecione um laboratório da lista"
                    )
                
                # Lógica de busca
                lab_final = None
                if busca_lab:
                    # Buscar por CNPJ (apenas números)
                    if busca_lab.isdigit():
                        lab_encontrado = df_filtrado[df_filtrado['CNPJ_PCL'].str.contains(busca_lab, na=False)]
                    else:
                        # Buscar por nome
                        lab_encontrado = df_filtrado[df_filtrado['Nome_Fantasia_PCL'].str.contains(busca_lab, case=False, na=False)]
                    
                    if not lab_encontrado.empty:
                        lab_final = lab_encontrado.iloc[0]['Nome_Fantasia_PCL']
                        st.success(f"✅ Laboratório encontrado: {lab_final}")
                    else:
                        st.warning("⚠️ Laboratório não encontrado")
                elif lab_selecionado:
                    lab_final = lab_selecionado

                if lab_final:
                    # Cards de métricas avançadas
                    metricas = MetricasAvancadas.calcular_metricas_lab(df_filtrado, lab_final)
                    
                    if metricas:
                        st.subheader(f"📊 Métricas Avançadas - {lab_final}")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric(
                                "📈 Total de Coletas 2025",
                                f"{metricas['total_coletas']:,}",
                                help="Total de coletas realizadas em 2025"
                            )
                        
                        with col2:
                            st.metric(
                                "📅 Média 3 Meses",
                                f"{metricas['media_3_meses']:.1f}",
                                help="Média dos últimos 3 meses (Ago-Set-Out)"
                            )
                        
                        with col3:
                            st.metric(
                                "📊 Média Diária",
                                f"{metricas['media_diaria']:.1f}",
                                help="Média diária baseada nos últimos 3 meses"
                            )
                        
                        with col4:
                            status_agudo = "🟢" if metricas['agudo'] == "Ativo" else "🔴"
                            st.metric(
                                f"{status_agudo} Status Agudo",
                                metricas['agudo'],
                                help="Atividade nos últimos 7 dias"
                            )
                        
                        # Segunda linha de cards
                        col5, col6, col7, col8 = st.columns(4)
                        
                        with col5:
                            status_cronico = "📈" if metricas['cronico'] == "Crescimento" else "📉" if metricas['cronico'] == "Declínio" else "📊"
                            st.metric(
                                f"{status_cronico} Status Crônico",
                                metricas['cronico'],
                                help="Tendência baseada na variação percentual"
                            )
                        
                        with col6:
                            st.metric(
                                "⏰ Dias sem Coleta",
                                f"{metricas['dias_sem_coleta']}",
                                help="Dias desde a última coleta"
                            )
                        
                        with col7:
                            delta_variacao = f"{metricas['variacao_percentual']:+.1f}%"
                            st.metric(
                                "📊 Variação %",
                                delta_variacao,
                                help="Variação percentual vs ano anterior"
                            )
                        
                        with col8:
                            # Status de risco
                            if metricas['dias_sem_coleta'] > 60:
                                risco = "🔴 Alto"
                            elif metricas['dias_sem_coleta'] > 30:
                                risco = "🟡 Médio"
                            else:
                                risco = "🟢 Baixo"
                            
                            st.metric(
                                "⚠️ Risco",
                                risco,
                                help="Classificação de risco baseada em dias sem coleta"
                            )
                    
                    st.subheader(f"📈 Evolução Mensal - {lab_final}")
                    ChartManager.criar_grafico_evolucao_mensal(df_filtrado, lab_final)
                    
                    # Novos gráficos
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📊 Média Diária por Mês")
                        ChartManager.criar_grafico_media_diaria(df_filtrado, lab_final)
                    
                    with col2:
                        st.subheader("📅 Coletas por Dia do Mês")
                        ChartManager.criar_grafico_coletas_por_dia(df_filtrado, lab_final)

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
            
            # Limpar dados nulos e vazios para o gráfico sunburst
            df_360 = df_360.dropna(subset=['Estado', 'Representante_Nome', 'Nome_Fantasia_PCL'])
            df_360 = df_360[df_360['Estado'] != '']
            df_360 = df_360[df_360['Representante_Nome'] != '']
            df_360 = df_360[df_360['Nome_Fantasia_PCL'] != '']
            
            if not df_360.empty and 'Tendencia' in df_360.columns and 'Status_Risco' in df_360.columns:
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
            else:
                st.warning("⚠️ Dados insuficientes para visualização 360°. Verifique se os campos Estado, Representante_Nome e Nome_Fantasia_PCL estão preenchidos.")
        else:
            st.warning("⚠️ Nenhum dado disponível para visualização 360°")

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
    # ABA 7: ANÁLISES INTELIGENTES
    # ========================================
    with tab7:
        st.header("🧠 Análises Inteligentes")
        st.markdown("**Dashboard com insights automáticos e análises preditivas**")
        
        # Dashboard inteligente
        AnaliseInteligente.criar_dashboard_inteligente(df_filtrado)
        
        # Análise geográfica inteligente
        if 'Estado' in df_filtrado.columns and 'Cidade' in df_filtrado.columns:
            st.subheader("🗺️ Análise Geográfica Inteligente")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Top estados por risco
                st.subheader("📊 Estados por Score de Risco")
                if 'Score_Risco' in df_filtrado.columns:
                    estado_risco = df_filtrado.groupby('Estado')['Score_Risco'].agg(['mean', 'count']).reset_index()
                    estado_risco = estado_risco[estado_risco['count'] >= 5]  # Mínimo 5 labs
                    estado_risco = estado_risco.sort_values('mean', ascending=False)
                    
                    fig_estado = px.bar(estado_risco, x='Estado', y='mean',
                                      title="Score Médio de Risco por Estado",
                                      labels={'mean': 'Score Médio de Risco'})
                    st.plotly_chart(fig_estado, use_container_width=True)
            
            with col2:
                # Distribuição de tendências por estado
                st.subheader("📈 Tendências por Estado")
                if 'Tendencia_Volume' in df_filtrado.columns:
                    tendencia_estado = df_filtrado.groupby(['Estado', 'Tendencia_Volume']).size().reset_index(name='count')
                    tendencia_estado = tendencia_estado[tendencia_estado['Estado'] != '']
                    
                    fig_tendencia = px.bar(tendencia_estado, x='Estado', y='count', color='Tendencia_Volume',
                                         title="Distribuição de Tendências por Estado")
                    st.plotly_chart(fig_tendencia, use_container_width=True)
        
        # Análise de padrões temporais
        st.subheader("⏰ Análise de Padrões Temporais")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Volume atual vs histórico
            if 'Volume_Atual_2025' in df_filtrado.columns and 'Volume_Maximo_2024' in df_filtrado.columns:
                st.subheader("📊 Volume Atual vs Histórico")
                
                # Criar scatter plot
                fig_scatter = px.scatter(
                    df_filtrado, 
                    x='Volume_Maximo_2024', 
                    y='Volume_Atual_2025',
                    color='Score_Risco',
                    size='Score_Risco',
                    hover_data=['Nome_Fantasia_PCL', 'Estado', 'Tendencia_Volume'],
                    title="Volume Atual vs Volume Máximo Histórico",
                    labels={'Volume_Maximo_2024': 'Volume Máximo 2024', 'Volume_Atual_2025': 'Volume Atual 2025'}
                )
                
                # Linha de referência (y = x)
                fig_scatter.add_shape(
                    type="line",
                    x0=0, y0=0, x1=df_filtrado['Volume_Maximo_2024'].max(), y1=df_filtrado['Volume_Maximo_2024'].max(),
                    line=dict(dash="dash", color="red"),
                    name="Linha de Referência"
                )
                
                st.plotly_chart(fig_scatter, use_container_width=True)
        
        with col2:
            # Distribuição de scores
            if 'Score_Risco' in df_filtrado.columns:
                st.subheader("📊 Distribuição de Scores de Risco")
                
                # Criar box plot por tendência
                if 'Tendencia_Volume' in df_filtrado.columns:
                    fig_box = px.box(
                        df_filtrado, 
                        x='Tendencia_Volume', 
                        y='Score_Risco',
                        title="Distribuição de Scores por Tendência",
                        labels={'Tendencia_Volume': 'Tendência de Volume', 'Score_Risco': 'Score de Risco'}
                    )
                    st.plotly_chart(fig_box, use_container_width=True)
        
        # Recomendações automáticas
        st.subheader("💡 Recomendações Automáticas")
        
        # Labs que precisam de atenção imediata
        labs_criticos = df_filtrado[df_filtrado['Score_Risco'] > 80].sort_values('Score_Risco', ascending=False)
        
        if not labs_criticos.empty:
            st.warning(f"🚨 **{len(labs_criticos)} laboratórios** precisam de atenção imediata!")
            
            # Mostrar top 10 mais críticos
            top_criticos = labs_criticos.head(10)[
                ['Nome_Fantasia_PCL', 'Estado', 'Cidade', 'Score_Risco', 'Insights_Automaticos']
            ]
            
            st.dataframe(top_criticos, use_container_width=True)
            
            # Ações recomendadas
            st.subheader("🎯 Ações Recomendadas")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📞 Contatos Urgentes", len(labs_criticos[labs_criticos['Dias_Sem_Coleta'] > 60]))
            
            with col2:
                st.metric("📈 Oportunidades", len(df_filtrado[df_filtrado['Tendencia_Volume'] == 'Crescimento']))
            
            with col3:
                st.metric("⚖️ Estáveis", len(df_filtrado[df_filtrado['Tendencia_Volume'] == 'Estável']))
        else:
            st.success("✅ Nenhum laboratório crítico identificado!")

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
