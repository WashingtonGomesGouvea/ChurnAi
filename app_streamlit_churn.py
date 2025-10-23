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
    def normalizar_cnpj(cnpj: str) -> str:
        """Remove formatação do CNPJ (pontos, traços, barras)"""
        if pd.isna(cnpj) or cnpj == '':
            return ''
        # Remove tudo exceto dígitos
        return ''.join(filter(str.isdigit, str(cnpj)))

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

        # Calcular volume total se não existir (até o mês atual)
        try:
            # Função inline para evitar dependência circular
            meses_ordem = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            ano_atual = pd.Timestamp.today().year
            limite_mes = pd.Timestamp.today().month if 2025 == ano_atual else 12
            meses_limite = meses_ordem[:limite_mes]
            sufixo = str(2025)[-2:]
            meses_2025_dyn = [m for m in meses_limite if f'N_Coletas_{m}_{sufixo}' in df.columns]
        except Exception:
            meses_2025_dyn = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out']
        colunas_meses = [f'N_Coletas_{mes}_25' for mes in meses_2025_dyn]

        if 'Volume_Total_2025' not in df.columns:
            df['Volume_Total_2025'] = df[colunas_meses].sum(axis=1, skipna=True) if colunas_meses else 0

        # Adicionar coluna CNPJ normalizado para match com dados VIP
        if 'CNPJ_PCL' in df.columns:
            df['CNPJ_Normalizado'] = df['CNPJ_PCL'].apply(DataManager.normalizar_cnpj)

        return df

    @staticmethod
    @st.cache_data(ttl=VIP_CACHE_TTL)
    def carregar_dados_vip() -> Optional[pd.DataFrame]:
        """Carrega dados VIP do CSV normalizado com cache."""
        try:
            # Tentar múltiplos caminhos possíveis para o CSV normalizado
            caminhos_possiveis = [
                VIP_CSV_FILE,  # Diretório atual
                os.path.join(OUTPUT_DIR, VIP_CSV_FILE),  # Dentro do OUTPUT_DIR
                os.path.join(os.path.dirname(OUTPUT_DIR), VIP_CSV_FILE),  # Pai do OUTPUT_DIR
            ]
            
            arquivo_csv = None
            for caminho in caminhos_possiveis:
                if os.path.exists(caminho):
                    arquivo_csv = caminho
                    break
            
            if arquivo_csv:
                df_vip = pd.read_csv(arquivo_csv, encoding='utf-8-sig')
                # Normalizar CNPJ para match
                df_vip['CNPJ_Normalizado'] = df_vip['CNPJ'].apply(DataManager.normalizar_cnpj)
                st.success(f"✅ Dados VIP carregados: {len(df_vip)} registros")
                return df_vip
            else:
                st.warning(f"Arquivo VIP normalizado não encontrado em nenhum dos caminhos: {caminhos_possiveis}")
                return None
        except Exception as e:
            st.warning(f"Erro ao carregar arquivo VIP: {e}")
            return None

class VIPManager:
    """Gerenciador de dados VIP."""

    @staticmethod
    def buscar_info_vip(cnpj: str, df_vip: pd.DataFrame) -> Optional[dict]:
        """Busca informações VIP para um CNPJ."""
        if df_vip is None or df_vip.empty or not cnpj:
            return None
        
        cnpj_normalizado = DataManager.normalizar_cnpj(cnpj)
        if not cnpj_normalizado:
            return None
        
        # Buscar match no DataFrame VIP
        match = df_vip[df_vip['CNPJ_Normalizado'] == cnpj_normalizado]
        if not match.empty:
            row = match.iloc[0]
            return {
                'ranking': row.get('Ranking', ''),
                'ranking_rede': row.get('Ranking Rede', ''),
                'rede': row.get('Rede', ''),
                'contato': row.get('Contato PCL', ''),
                'telefone': row.get('Whatsapp/telefone', ''),
                'email': row.get('Email', '')
            }
        return None

    @staticmethod
    def renderizar_card_vip(info_vip: dict, lab_nome: str):
        """Renderiza card visual com informações VIP."""
        st.subheader(f"🌟 Informações VIP - {lab_nome}")
        
        # Badge VIP
        st.markdown("""
        <div style="background: linear-gradient(135deg, #FFD700, #FFA500); 
                    color: white; padding: 1rem; border-radius: 10px; 
                    text-align: center; margin-bottom: 1rem; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
            <h3 style="margin: 0; font-size: 1.5rem;">⭐ CLIENTE VIP ⭐</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Informações VIP em colunas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; 
                        border-left: 4px solid #FFD700; text-align: center;">
                <h4 style="margin: 0 0 0.5rem 0; color: #333;">🏆 Ranking</h4>
                <p style="margin: 0; font-size: 1.2rem; font-weight: bold; color: #FFD700;">
                    {info_vip.get('ranking', 'N/A')}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; 
                        border-left: 4px solid #FFA500; text-align: center;">
                <h4 style="margin: 0 0 0.5rem 0; color: #333;">🏅 Ranking Rede</h4>
                <p style="margin: 0; font-size: 1.2rem; font-weight: bold; color: #FFA500;">
                    {info_vip.get('ranking_rede', 'N/A')}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; 
                        border-left: 4px solid #007bff; text-align: center;">
                <h4 style="margin: 0 0 0.5rem 0; color: #333;">🏥 Rede</h4>
                <p style="margin: 0; font-size: 1.2rem; font-weight: bold; color: #007bff;">
                    {info_vip.get('rede', 'N/A')}
                </p>
            </div>
            """, unsafe_allow_html=True)

class FilterManager:
    """Gerenciador de filtros da interface."""

    def __init__(self):
        self.filtros = {}

    def renderizar_sidebar_filtros(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Renderiza filtros otimizados na sidebar."""
        st.sidebar.markdown('<div class="sidebar-header"><h3>🔧 Filtros</h3></div>', unsafe_allow_html=True)

        filtros = {}

        # Filtro VIP com opção de alternar
        filtros['apenas_vip'] = st.sidebar.toggle(
            "🌟 Apenas Clientes VIP",
            value=True,
            help="Ative para mostrar apenas clientes VIP, desative para mostrar todos"
        )
        
        # Separador visual
        st.sidebar.markdown("---")

        # Filtro por período simplificado
        st.sidebar.markdown("**📅 Período de Análise**")
        
        # Opções de período pré-definidas
        opcoes_periodo = {
            "Últimos 7 dias": 7,
            "Últimos 15 dias": 15,
            "Últimos 30 dias": 30,
            "Últimos 60 dias": 60,
            "Últimos 90 dias": 90,
            "Personalizado": "custom"
        }
        
        periodo_selecionado = st.sidebar.selectbox(
            "Selecione o período:",
            options=list(opcoes_periodo.keys()),
            index=2,  # Padrão: 30 dias
            help="Escolha o período para análise"
        )
        
        if opcoes_periodo[periodo_selecionado] == "custom":
            # Período personalizado
            col1, col2 = st.sidebar.columns(2)
            with col1:
                filtros['data_inicio'] = st.sidebar.date_input(
                    "Data Início",
                    value=datetime.now() - timedelta(days=30),
                    key="data_inicio_custom"
                )
            with col2:
                filtros['data_fim'] = st.sidebar.date_input(
                    "Data Fim",
                    value=datetime.now(),
                    key="data_fim_custom"
                )
        else:
            # Período pré-definido
            dias = opcoes_periodo[periodo_selecionado]
            filtros['data_inicio'] = datetime.now() - timedelta(days=dias)
            filtros['data_fim'] = datetime.now()
        
        # Mostrar período atual (texto discreto)
        data_inicio_str = filtros['data_inicio'].strftime('%d/%m/%Y')
        data_fim_str = filtros['data_fim'].strftime('%d/%m/%Y')
        st.sidebar.markdown(f"<small>📊 {data_inicio_str} a {data_fim_str}</small>", unsafe_allow_html=True)

        self.filtros = filtros
        return filtros

    def aplicar_filtros(self, df: pd.DataFrame, filtros: Dict[str, Any]) -> pd.DataFrame:
        """Aplica filtros otimizados ao DataFrame."""
        if df.empty:
            return df

        df_filtrado = df.copy()

        # Filtro VIP (sempre ativo)
        if filtros.get('apenas_vip', False):
            try:
                # Carregar dados VIP
                df_vip = DataManager.carregar_dados_vip()
                if df_vip is not None and not df_vip.empty:
                    # Normalizar CNPJs para match com tratamento de erro
                    df_filtrado['CNPJ_Normalizado'] = df_filtrado['CNPJ_PCL'].apply(
                        lambda x: ''.join(filter(str.isdigit, str(x))) if pd.notna(x) and str(x).strip() != '' else ''
                    )
                    df_vip['CNPJ_Normalizado'] = df_vip['CNPJ'].apply(
                        lambda x: ''.join(filter(str.isdigit, str(x))) if pd.notna(x) and str(x).strip() != '' else ''
                    )
                    
                    # Filtrar apenas registros que estão na lista VIP (com validação)
                    if 'CNPJ_Normalizado' in df_filtrado.columns and 'CNPJ_Normalizado' in df_vip.columns:
                        # Remover CNPJs vazios antes do match
                        df_filtrado = df_filtrado[df_filtrado['CNPJ_Normalizado'] != '']
                        df_vip_clean = df_vip[df_vip['CNPJ_Normalizado'] != '']
                        
                        if not df_vip_clean.empty:
                            df_filtrado = df_filtrado[df_filtrado['CNPJ_Normalizado'].isin(df_vip_clean['CNPJ_Normalizado'])]
                        else:
                            # Se não há CNPJs válidos na lista VIP, retornar DataFrame vazio
                            return pd.DataFrame()
                    else:
                        # Se as colunas não existem, retornar DataFrame vazio
                        return pd.DataFrame()
                else:
                    # Se não há dados VIP, retornar DataFrame vazio
                    return pd.DataFrame()
            except Exception as e:
                # Em caso de erro, retornar DataFrame vazio e log do erro
                st.error(f"Erro ao aplicar filtro VIP: {str(e)}")
                return pd.DataFrame()

        # Filtro por período
        if 'Data_Analise' in df_filtrado.columns and filtros.get('data_inicio') and filtros.get('data_fim'):
            try:
                # Garantir que as datas sejam do tipo date
                data_inicio = filtros['data_inicio']
                data_fim = filtros['data_fim']
                
                # Se for datetime, converter para date
                if hasattr(data_inicio, 'date'):
                    data_inicio = data_inicio.date()
                if hasattr(data_fim, 'date'):
                    data_fim = data_fim.date()
                
                # Verificar se a coluna Data_Analise é do tipo datetime
                if df_filtrado['Data_Analise'].dtype == 'object':
                    # Tentar converter para datetime
                    df_filtrado['Data_Analise'] = pd.to_datetime(df_filtrado['Data_Analise'], errors='coerce')
                
                # Aplicar filtro apenas se a conversão foi bem-sucedida
                if df_filtrado['Data_Analise'].dtype.name.startswith('datetime'):
                    df_filtrado = df_filtrado[
                        (df_filtrado['Data_Analise'].dt.date >= data_inicio) &
                        (df_filtrado['Data_Analise'].dt.date <= data_fim)
                    ]
            except Exception as e:
                # Em caso de erro no filtro de data, continuar sem filtrar
                st.warning(f"Aviso: Erro ao aplicar filtro de período: {str(e)}")
                pass

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
    def _meses_ate_hoje(df: pd.DataFrame, ano: int) -> list:
        """Retorna lista de códigos de meses disponíveis até o mês corrente para o ano informado.

        - Garante ordem cronológica correta
        - Considera apenas colunas que existem no DataFrame
        - Para anos anteriores ao corrente, considera até Dezembro
        """
        meses_ordem = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        ano_atual = pd.Timestamp.today().year
        limite_mes = pd.Timestamp.today().month if ano == ano_atual else 12
        meses_limite = meses_ordem[:limite_mes]
        sufixo = str(ano)[-2:]
        return [m for m in meses_limite if f'N_Coletas_{m}_{sufixo}' in df.columns]

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

        meses = ChartManager._meses_ate_hoje(df, 2025)
        if not meses:
            return
        colunas_meses = [f'N_Coletas_{mes}_25' for mes in meses]
        
        if lab_selecionado:
            lab_data = df[df['Nome_Fantasia_PCL'] == lab_selecionado]
            if not lab_data.empty:
                lab = lab_data.iloc[0]
                valores_mensais = [lab[col] for col in colunas_meses]
                
                # Calcular média diária (dias reais aproximados por mês)
                dias_map = {
                    'Jan': 31, 'Fev': 28, 'Mar': 31, 'Abr': 30, 'Mai': 31, 'Jun': 30,
                    'Jul': 31, 'Ago': 31, 'Set': 30, 'Out': 31, 'Nov': 30, 'Dez': 31
                }
                medias_diarias = [val / max(1, dias_map.get(mes, 30)) for val, mes in zip(valores_mensais, meses)]
                
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
                meses = ChartManager._meses_ate_hoje(df, 2025)
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

        meses = ChartManager._meses_ate_hoje(df, 2025)
        if not meses:
            st.info("📊 Nenhum mês disponível até a data atual")
            return
        colunas_meses = [f'N_Coletas_{mes}_25' for mes in meses]

        if lab_selecionado:
            # Gráfico para laboratório específico
            lab_data = df[df['Nome_Fantasia_PCL'] == lab_selecionado]
            if not lab_data.empty:
                lab = lab_data.iloc[0]
                valores_2025 = [lab[col] for col in colunas_meses]
                
                # Dados 2024 (mesmos meses para comparação direta)
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
            meses_2025 = ChartManager._meses_ate_hoje(df, 2025)
            colunas_meses = [f'N_Coletas_{mes}_25' for mes in meses_2025]
            if colunas_meses:
                df['Volume_Total_2025'] = df[colunas_meses].sum(axis=1, skipna=True)
            else:
                df['Volume_Total_2025'] = 0

        top_labs = df.nlargest(top_n, 'Volume_Total_2025')
        meses = ChartManager._meses_ate_hoje(df, 2025)
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
        
        # Total de coletas 2025 (até o mês atual)
        meses_2025 = ChartManager._meses_ate_hoje(df, 2025)
        colunas_2025 = [f'N_Coletas_{mes}_25' for mes in meses_2025]
        total_coletas_2025 = lab[colunas_2025].sum() if colunas_2025 and all(col in lab.index for col in colunas_2025) else 0
        
        # Média dos últimos 3 meses (dinâmico)
        if len(meses_2025) >= 3:
            ultimos_3_meses = meses_2025[-3:]
        else:
            ultimos_3_meses = meses_2025
        colunas_3_meses = [f'N_Coletas_{mes}_25' for mes in ultimos_3_meses]
        media_3_meses = lab[colunas_3_meses].mean() if colunas_3_meses and all(col in lab.index for col in colunas_3_meses) else 0
        
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
        
        # Volume atual (último mês disponível dinâmico)
        meses_validos_2025 = ChartManager._meses_ate_hoje(df_insights, 2025)
        ultima_coluna_2025 = f"N_Coletas_{meses_validos_2025[-1]}_25" if meses_validos_2025 else None
        if ultima_coluna_2025 and ultima_coluna_2025 in df_insights.columns:
            df_insights['Volume_Atual_2025'] = df_insights[ultima_coluna_2025]
        else:
            df_insights['Volume_Atual_2025'] = 0
        
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
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏠 Visão Geral",
        "📋 Análise Detalhada",
        "👤 Por Representante",
        "🧠 Análises Inteligentes",
        "🏢 Ranking Rede",
        "🔧 Manutenção VIPs"
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

        # Filtros avançados com design moderno
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 1.5rem; border-radius: 10px;
                    margin-bottom: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h3 style="margin: 0; font-size: 1.3rem;">🔍 Busca Inteligente de Laboratórios</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                Busque por CNPJ (com ou sem formatação) ou nome do laboratório
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="dataframe-container" style="padding: 1.5rem;">', unsafe_allow_html=True)

            # Seleção de laboratório específico
            if not df_filtrado.empty:
                # Layout melhorado com 3 colunas - ajustado para melhor alinhamento
                col1, col2, col3 = st.columns([4, 1.5, 2.5])

                with col1:
                    # Campo de busca aprimorado
                    busca_lab = st.text_input(
                        "🔍 Buscar por CNPJ ou Nome:",
                        placeholder="Ex: 51.865.434/0012-48 ou BIOLOGICO...",
                        help="Digite CNPJ (com ou sem pontos/tracos) ou nome do laboratório/razão social",
                        key="busca_avancada"
                    )

                with col2:
                    # Espaçamento para alinhamento
                    st.write("")  # Espaço vazio para alinhar com o campo de texto
                    # Botão de busca rápida
                    buscar_btn = st.button("🔎 Buscar", type="primary", use_container_width=True)

                with col3:
                    # Seleção por dropdown como alternativa
                    lab_selecionado = st.selectbox(
                        "📋 Lista Rápida:",
                        options=[""] + sorted(df_filtrado['Nome_Fantasia_PCL'].unique()),
                        help="Ou selecione um laboratório da lista completa",
                        key="lista_rapida"
                    )

                # Informações de ajuda
                with st.expander("💡 Dicas de Busca", expanded=False):
                    st.markdown("""
                    **🔢 Para CNPJ:**
                    - Apenas números: `51865434001248`
                    - Com formatação: `51.865.434/0012-48`

                    **🏥 Para Nome:**
                    - Nome fantasia ou razão social
                    - Busca parcial e sem distinção de maiúsculas/minúsculas

                    **📊 Resultados:**
                    - 1 resultado: Selecionado automaticamente
                    - Múltiplos: Lista para escolher o correto
                    """)

                # Estado da busca
                lab_final = None

                # Verificar se há busca ativa ou laboratório selecionado
                busca_ativa = buscar_btn or (busca_lab and len(busca_lab.strip()) > 2)
                tem_selecao = lab_selecionado and lab_selecionado != ""

                if busca_ativa or tem_selecao:
                    # Lógica de busca aprimorada
                    if busca_ativa and busca_lab:
                        busca_normalizada = busca_lab.strip()

                        # Verificar se é CNPJ (com ou sem formatação)
                        cnpj_limpo = ''.join(filter(str.isdigit, busca_normalizada))

                        if len(cnpj_limpo) >= 8:  # CNPJ válido tem pelo menos 8 dígitos
                            # Buscar por CNPJ normalizado
                            df_filtrado['CNPJ_Normalizado_Busca'] = df_filtrado['CNPJ_PCL'].apply(
                                lambda x: ''.join(filter(str.isdigit, str(x))) if pd.notna(x) else ''
                            )
                            lab_encontrado = df_filtrado[df_filtrado['CNPJ_Normalizado_Busca'].str.startswith(cnpj_limpo)]
                        else:
                            # Buscar por nome (case insensitive e parcial) - apenas nome fantasia e razão social
                            lab_encontrado = df_filtrado[
                                df_filtrado['Nome_Fantasia_PCL'].str.contains(busca_normalizada, case=False, na=False) |
                                df_filtrado['Razao_Social_PCL'].str.contains(busca_normalizada, case=False, na=False)
                            ]

                        if not lab_encontrado.empty:
                            if len(lab_encontrado) == 1:
                                lab_final = lab_encontrado.iloc[0]['Nome_Fantasia_PCL']
                                st.success(f"✅ Laboratório encontrado: {lab_final}")
                            else:
                                # Múltiplos resultados - mostrar opções
                                st.info(f"🔍 Encontrados {len(lab_encontrado)} laboratórios. Selecione um:")

                                # Criar lista de opções com mais detalhes
                                opcoes = []
                                for _, row in lab_encontrado.head(10).iterrows():
                                    nome = row['Nome_Fantasia_PCL']
                                    cidade = row.get('Cidade', 'N/A')
                                    estado = row.get('Estado', 'N/A')
                                    cnpj = row.get('CNPJ_PCL', 'N/A')
                                    opcao = f"{nome} - {cidade}/{estado} (CNPJ: {cnpj})"
                                    opcoes.append(opcao)

                                lab_selecionado_multiplo = st.selectbox(
                                    "Selecione o laboratório correto:",
                                    options=[""] + opcoes,
                                    key="multiplo_resultados"
                                )

                                if lab_selecionado_multiplo and lab_selecionado_multiplo != "":
                                    # Extrair nome do laboratório da opção selecionada
                                    nome_selecionado = lab_selecionado_multiplo.split(" - ")[0]
                                    lab_final = nome_selecionado
                        else:
                            st.warning("⚠️ Nenhum laboratório encontrado com os critérios informados")

                    elif tem_selecao:
                        # Laboratório selecionado diretamente da lista
                        lab_final = lab_selecionado

                    # Renderizar dados do laboratório encontrado/selecionado
                    if lab_final:
                        st.markdown("---")  # Separador antes dos dados

                        # Verificar se é VIP
                        df_vip = DataManager.carregar_dados_vip()
                        lab_data = df_filtrado[df_filtrado['Nome_Fantasia_PCL'] == lab_final]
                        info_vip = None

                        if not lab_data.empty and df_vip is not None:
                            cnpj_lab = lab_data.iloc[0].get('CNPJ_PCL', '')
                            info_vip = VIPManager.buscar_info_vip(cnpj_lab, df_vip)

                        # Container principal para informações do laboratório
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    color: white; padding: 2rem; border-radius: 15px;
                                    margin-bottom: 2rem; box-shadow: 0 8px 25px rgba(0,0,0,0.15);">
                            <div style="display: flex; align-items: center;">
                                <div style="font-size: 2rem; margin-right: 1rem;">🏥</div>
                                <div>
                                    <h2 style="margin: 0; font-size: 1.8rem; font-weight: 600;">{lab_final}</h2>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Armazenar informações da rede para filtro automático na tabela
                        if info_vip and 'rede' in info_vip:
                            st.session_state['rede_lab_pesquisado'] = info_vip['rede']
                        else:
                            st.session_state['rede_lab_pesquisado'] = None

                        # Ficha Técnica Comercial
                        st.markdown("""
                        <div style="background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; 
                                    border: 1px solid #e9ecef; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h3 style="margin: 0 0 1rem 0; color: #2c3e50; font-weight: 600; border-bottom: 2px solid #007bff; padding-bottom: 0.5rem;">
                                📋 Ficha Técnica Comercial
                            </h3>
                        """, unsafe_allow_html=True)

                        # Informações de contato e localização
                        lab_data = df_filtrado[df_filtrado['Nome_Fantasia_PCL'] == lab_final]
                        if not lab_data.empty:
                            lab_info = lab_data.iloc[0]
                            
                            # CNPJ formatado
                            cnpj_raw = str(lab_info.get('CNPJ_PCL', ''))
                            cnpj_formatado = f"{cnpj_raw[:2]}.{cnpj_raw[2:5]}.{cnpj_raw[5:8]}/{cnpj_raw[8:12]}-{cnpj_raw[12:14]}" if len(cnpj_raw) == 14 else cnpj_raw
                            
                            # Usar dados do Excel VIP se disponível, senão usar dados do laboratório
                            telefone = info_vip.get('telefone', '') if info_vip else lab_info.get('Telefone', 'N/A')
                            email = info_vip.get('email', '') if info_vip else lab_info.get('Email', 'N/A')
                            contato = info_vip.get('contato', '') if info_vip else 'N/A'
                            
                            # Limpar dados vazios
                            telefone = telefone if telefone and telefone != 'N/A' else 'N/A'
                            email = email if email and email != 'N/A' else 'N/A'
                            contato = contato if contato else 'N/A'
                            
                            st.markdown(f"""
                            <div style="background: #f8f9fa; border-radius: 6px; padding: 1rem; margin-bottom: 1rem; border-left: 4px solid #6c757d;">
                                <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem; font-weight: 600;">INFORMAÇÕES DE CONTATO</div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666; margin-bottom: 0.3rem;">CNPJ</div>
                                        <div style="font-size: 1rem; font-weight: bold; color: #495057;">{cnpj_formatado}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666; margin-bottom: 0.3rem;">Localização</div>
                                        <div style="font-size: 1rem; font-weight: bold; color: #495057;">{lab_info.get('Cidade', 'N/A')} - {lab_info.get('Estado', 'N/A')}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666; margin-bottom: 0.3rem;">Contato</div>
                                        <div style="font-size: 1rem; font-weight: bold; color: #495057;">{contato}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666; margin-bottom: 0.3rem;">Telefone</div>
                                        <div style="font-size: 1rem; font-weight: bold; color: #495057;">{telefone}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666; margin-bottom: 0.3rem;">Email</div>
                                        <div style="font-size: 1rem; font-weight: bold; color: #495057;">{email}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        # Informações VIP se disponível
                        if info_vip:
                            st.markdown(f"""
                            <div style="background: #f8f9fa; border-radius: 6px; padding: 1rem; margin-bottom: 1rem; border-left: 4px solid #007bff;">
                                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; text-align: center;">
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666; margin-bottom: 0.3rem;">RANKING GERAL</div>
                                        <div style="font-size: 1.2rem; font-weight: bold; color: #FFD700;">{info_vip.get('ranking', 'N/A')}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666; margin-bottom: 0.3rem;">RANKING REDE</div>
                                        <div style="font-size: 1.2rem; font-weight: bold; color: #FFA500;">{info_vip.get('ranking_rede', 'N/A')}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666; margin-bottom: 0.3rem;">REDE</div>
                                        <div style="font-size: 1.1rem; font-weight: bold; color: #007bff;">{info_vip.get('rede', 'N/A')}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        # Métricas comerciais essenciais
                        metricas = MetricasAvancadas.calcular_metricas_lab(df_filtrado, lab_final)

                        if metricas:
                            # Dados de Performance
                            st.markdown(f"""
                            <div style="background: #f8f9fa; border-radius: 6px; padding: 1rem; margin-bottom: 1rem; border-left: 4px solid #28a745;">
                                <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem; font-weight: 600;">PERFORMANCE 2025</div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; text-align: center;">
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666;">Total Coletas</div>
                                        <div style="font-size: 1.3rem; font-weight: bold; color: #28a745;">{metricas['total_coletas']:,}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666;">Média 3 Meses</div>
                                        <div style="font-size: 1.3rem; font-weight: bold; color: #28a745;">{metricas['media_3_meses']:.1f}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666;">Média Diária</div>
                                        <div style="font-size: 1.3rem; font-weight: bold; color: #28a745;">{metricas['media_diaria']:.1f}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # Status e Risco
                            status_color = "#28a745" if metricas['agudo'] == "Ativo" else "#dc3545"
                            risco_color = "#28a745" if metricas['dias_sem_coleta'] <= 7 else "#ffc107" if metricas['dias_sem_coleta'] <= 30 else "#dc3545"
                            
                            st.markdown(f"""
                            <div style="background: #f8f9fa; border-radius: 6px; padding: 1rem; margin-bottom: 1rem; border-left: 4px solid {risco_color};">
                                <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem; font-weight: 600;">STATUS & RISCO</div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; text-align: center;">
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666;">Status Atual</div>
                                        <div style="font-size: 1.1rem; font-weight: bold; color: {status_color};">{metricas['agudo']}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666;">Dias sem Coleta</div>
                                        <div style="font-size: 1.1rem; font-weight: bold; color: {risco_color};">{metricas['dias_sem_coleta']}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666;">Variação %</div>
                                        <div style="font-size: 1.1rem; font-weight: bold; color: {'#28a745' if metricas['variacao_percentual'] > 0 else '#dc3545'};">{metricas['variacao_percentual']:+.1f}%</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # Histórico de Performance
                            # Calcular máxima de coletas histórica (respeitando meses disponíveis)
                            meses_validos_2024 = ChartManager._meses_ate_hoje(df_filtrado, 2024)
                            meses_validos_2025 = ChartManager._meses_ate_hoje(df_filtrado, 2025)
                            colunas_meses_2024 = [f'N_Coletas_{mes}_24' for mes in meses_validos_2024]
                            colunas_meses_2025 = [f'N_Coletas_{mes}_25' for mes in meses_validos_2025]

                            max_2024 = 0
                            max_2025 = 0
                            mes_max_2024 = ""
                            mes_max_2025 = ""
                            
                            # Mapeamento de códigos de mês para nomes
                            meses_map = {
                                'Jan': 'Janeiro', 'Fev': 'Fevereiro', 'Mar': 'Março', 'Abr': 'Abril',
                                'Mai': 'Maio', 'Jun': 'Junho', 'Jul': 'Julho', 'Ago': 'Agosto',
                                'Set': 'Setembro', 'Out': 'Outubro', 'Nov': 'Novembro', 'Dez': 'Dezembro'
                            }
                            
                            if colunas_meses_2024:
                                for col in colunas_meses_2024:
                                    valor = pd.to_numeric(lab_info.get(col, 0), errors='coerce')
                                    valor = 0 if pd.isna(valor) else valor
                                    if valor and valor > max_2024:
                                        max_2024 = valor
                                        # Extrair código do mês corretamente
                                        partes = col.split('_')
                                        if len(partes) >= 3:
                                            mes_codigo = partes[2]  # Ex: 'Out' de N_Coletas_Out_24
                                            # Verificar se é um mês válido
                                            if mes_codigo in meses_map:
                                                mes_max_2024 = meses_map[mes_codigo]
                                            else:
                                                # Se não for um mês válido, usar o código original
                                                mes_max_2024 = mes_codigo
                            
                            if colunas_meses_2025:
                                for col in colunas_meses_2025:
                                    valor = pd.to_numeric(lab_info.get(col, 0), errors='coerce')
                                    valor = 0 if pd.isna(valor) else valor
                                    if valor and valor > max_2025:
                                        max_2025 = valor
                                        # Extrair código do mês corretamente
                                        partes = col.split('_')
                                        if len(partes) >= 3:
                                            mes_codigo = partes[2]  # Ex: 'Out' de N_Coletas_Out_25
                                            # Verificar se é um mês válido
                                            if mes_codigo in meses_map:
                                                mes_max_2025 = meses_map[mes_codigo]
                                            else:
                                                # Se não for um mês válido, usar o código original
                                                mes_max_2025 = mes_codigo
                            
                            max_historica = max(max_2024, max_2025)
                            if max_2024 > max_2025:
                                mes_max = mes_max_2024
                                ano_max = "2024"
                            else:
                                mes_max = mes_max_2025
                                ano_max = "2025"
                            
                            # Fallback se não conseguir determinar o mês
                            if not mes_max or mes_max == "":
                                mes_max = "N/A"
                            
                            st.markdown(f"""
                            <div style="background: #f8f9fa; border-radius: 6px; padding: 1rem; margin-bottom: 1rem; border-left: 4px solid #17a2b8;">
                                <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem; font-weight: 600;">HISTÓRICO DE PERFORMANCE</div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; text-align: center;">
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666;">Máxima Histórica</div>
                                        <div style="font-size: 1.3rem; font-weight: bold; color: #17a2b8;">{max_historica:,} coletas</div>
                                        <div style="font-size: 0.7rem; color: #666;">{mes_max}/{ano_max}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666;">Performance Atual vs Máxima</div>
                                        <div style="font-size: 1.1rem; font-weight: bold; color: {'#28a745' if metricas['total_coletas'] >= max_historica * 0.8 else '#ffc107' if metricas['total_coletas'] >= max_historica * 0.5 else '#dc3545'};">
                                            {(metricas['total_coletas'] / max_historica * 100):.0f}% da máxima
                                        </div>
                                        <div style="font-size: 0.7rem; color: #666;">{metricas['total_coletas']:,} vs {max_historica:,}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            st.markdown("</div>", unsafe_allow_html=True)

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

                # Fechar container
                st.markdown('</div>', unsafe_allow_html=True)

        # Tabela completa de dados com funcionalidade de rede
        st.markdown("""
        <div style="background: white; border-radius: 12px; padding: 1.5rem;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.08); margin-bottom: 2rem;
                    border: 1px solid #f0f0f0;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.5rem; margin-right: 0.5rem;">📋</span>
                    <h3 style="margin: 0; color: #2c3e50; font-weight: 600;">Dados Completos dos Laboratórios</h3>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Carregar dados VIP para análise de rede
        df_vip_tabela = DataManager.carregar_dados_vip()

        # Adicionar informações de rede se disponível
        df_tabela = df_filtrado.copy()
        mostrar_rede = False

        if df_vip_tabela is not None and not df_vip_tabela.empty:
            # Merge dos dados com informações VIP
            df_tabela['CNPJ_Normalizado'] = df_tabela['CNPJ_PCL'].apply(
                lambda x: ''.join(filter(str.isdigit, str(x))) if pd.notna(x) else ''
            )
            df_vip_tabela['CNPJ_Normalizado'] = df_vip_tabela['CNPJ'].apply(
                lambda x: ''.join(filter(str.isdigit, str(x))) if pd.notna(x) else ''
            )

            df_tabela = df_tabela.merge(
                df_vip_tabela[['CNPJ_Normalizado', 'Rede', 'Ranking', 'Ranking Rede']],
                on='CNPJ_Normalizado',
                how='left'
            )
            mostrar_rede = True

        # Filtro por rede (simplificado)
        if mostrar_rede and 'Rede' in df_tabela.columns:
            redes_disponiveis = ["Todas"] + sorted(df_tabela['Rede'].dropna().unique().tolist())

            # Usar rede do laboratório pesquisado como padrão, se disponível
            rede_padrao = st.session_state.get('rede_lab_pesquisado', "Todas")
            if rede_padrao not in redes_disponiveis:
                rede_padrao = "Todas"

            # Aplicar filtro automático se há rede selecionada
            if rede_padrao != "Todas":
                rede_filtro = rede_padrao
                # Mostrar indicador de filtro automático
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #e8f5e8, #f1f8e9); border-radius: 6px; padding: 0.8rem; margin-bottom: 1rem;">
                    <span style="color: #2e7d32; font-size: 0.9rem;">🎯 <strong>Filtro automático ativo:</strong> mostrando apenas laboratórios da rede <strong>"{rede_padrao}"</strong></span>
                </div>
                """, unsafe_allow_html=True)
                
                # Botão para limpar filtro automático
                if st.button("🔄 Mostrar Todas as Redes", key="limpar_filtro_auto", help="Mostrar laboratórios de todas as redes"):
                    st.session_state['rede_lab_pesquisado'] = None
                    st.rerun()
            else:
                # Seleção manual de rede
                rede_filtro = st.selectbox(
                    "🏢 Filtrar por Rede:",
                    options=redes_disponiveis,
                    index=0,  # Sempre "Todas" por padrão
                    help="Selecione uma rede para filtrar",
                    key="filtro_rede_tabela"
                )
        else:
            rede_filtro = "Todas"

        # Aplicar filtros
        df_tabela_filtrada = df_tabela.copy()

        # Filtro por rede
        if rede_filtro != "Todas" and mostrar_rede:
            df_tabela_filtrada = df_tabela_filtrada[df_tabela_filtrada['Rede'] == rede_filtro]

        # Mostrar informações da rede se filtrada
        if rede_filtro != "Todas" and mostrar_rede and not df_tabela_filtrada.empty:
            # Estatísticas da rede
            stats_rede = {
                'total_labs': len(df_tabela_filtrada),
                'volume_total': df_tabela_filtrada['Volume_Total_2025'].sum() if 'Volume_Total_2025' in df_tabela_filtrada.columns else 0,
                'media_volume': df_tabela_filtrada['Volume_Total_2025'].mean() if 'Volume_Total_2025' in df_tabela_filtrada.columns else 0,
                'labs_risco_alto': len(df_tabela_filtrada[df_tabela_filtrada['Status_Risco'] == 'Alto']) if 'Status_Risco' in df_tabela_filtrada.columns else 0,
                'labs_ativos': len(df_tabela_filtrada[df_tabela_filtrada['Dias_Sem_Coleta'] <= 30]) if 'Dias_Sem_Coleta' in df_tabela_filtrada.columns else 0
            }

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #e3f2fd, #f3e5f5); border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                <h4 style="margin: 0 0 0.5rem 0; color: #1976d2;">📊 Estatísticas da Rede: {rede_filtro}</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
                    <div style="text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #1976d2;">{stats_rede['total_labs']}</div>
                        <div style="font-size: 0.8rem; color: #666;">Laboratórios</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #1976d2;">{stats_rede['volume_total']:,.0f}</div>
                        <div style="font-size: 0.8rem; color: #666;">Volume Total</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #1976d2;">{stats_rede['media_volume']:.0f}</div>
                        <div style="font-size: 0.8rem; color: #666;">Média por Lab</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #f44336;">{stats_rede['labs_risco_alto']}</div>
                        <div style="font-size: 0.8rem; color: #666;">Alto Risco</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #4caf50;">{stats_rede['labs_ativos']}</div>
                        <div style="font-size: 0.8rem; color: #666;">Ativos (30d)</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Configurar colunas da tabela
        colunas_principais = [
            'Nome_Fantasia_PCL', 'Estado', 'Cidade', 'Representante_Nome',
            'Status_Risco', 'Dias_Sem_Coleta', 'Variacao_Percentual',
            'Volume_Atual_2025', 'Volume_Maximo_2024', 'Tendencia_Volume'
        ]

        # Adicionar colunas de rede se disponível
        if mostrar_rede:
            colunas_principais.extend(['Rede', 'Ranking', 'Ranking Rede'])

        colunas_existentes = [col for col in colunas_principais if col in df_tabela_filtrada.columns]

        if not df_tabela_filtrada.empty and colunas_existentes:
            df_exibicao = df_tabela_filtrada[colunas_existentes].copy()

            # Formatação de colunas
            if 'Variacao_Percentual' in df_exibicao.columns:
                df_exibicao['Variacao_Percentual'] = df_exibicao['Variacao_Percentual'].round(2)

            if 'Volume_Atual_2025' in df_exibicao.columns:
                df_exibicao['Volume_Atual_2025'] = df_exibicao['Volume_Atual_2025'].astype(int)

            if 'Volume_Maximo_2024' in df_exibicao.columns:
                df_exibicao['Volume_Maximo_2024'] = df_exibicao['Volume_Maximo_2024'].astype(int)

            # Mostrar tabela com contador
            st.markdown(f"**Mostrando {len(df_exibicao)} laboratórios**")

            st.dataframe(
                df_exibicao,
                use_container_width=True,
                height=500,
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
                    "Rede": st.column_config.TextColumn(
                        "🏢 Rede",
                        help="Rede à qual o laboratório pertence"
                    ),
                    "Ranking": st.column_config.TextColumn(
                        "🏆 Ranking",
                        help="Ranking individual do laboratório"
                    ),
                    "Ranking Rede": st.column_config.TextColumn(
                        "🏅 Ranking Rede",
                        help="Ranking da rede do laboratório"
                    )
                }
            )

            # Botões de download
            col_download1, col_download2 = st.columns(2)

            with col_download1:
                csv_data = df_exibicao.to_csv(index=False, encoding='utf-8')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"dados_laboratorios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_csv_tabela"
                )

            with col_download2:
                excel_buffer = BytesIO()
                df_exibicao.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_data = excel_buffer.getvalue()
                st.download_button(
                    label="📥 Download Excel",
                    data=excel_data,
                    file_name=f"dados_laboratorios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel_tabela"
                )
        else:
            st.info("📋 Nenhum laboratório encontrado com os filtros aplicados.")

        st.markdown("</div>", unsafe_allow_html=True)

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
    # ABA 4: ANÁLISES INTELIGENTES
    # ========================================
    with tab4:
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
    # ABA 5: RANKING REDE
    # ========================================
    with tab5:
        st.header("🏢 Ranking por Rede")

        # Carregar dados VIP para análise de rede
        df_vip = DataManager.carregar_dados_vip()

        if df_vip is not None and not df_vip.empty:
            # Merge dos dados principais com dados VIP
            df_com_rede = df_filtrado.copy()

            # Adicionar coluna CNPJ normalizado para match
            df_com_rede['CNPJ_Normalizado'] = df_com_rede['CNPJ_PCL'].apply(
                lambda x: ''.join(filter(str.isdigit, str(x))) if pd.notna(x) else ''
            )
            df_vip['CNPJ_Normalizado'] = df_vip['CNPJ'].apply(
                lambda x: ''.join(filter(str.isdigit, str(x))) if pd.notna(x) else ''
            )

            # Merge dos dados
            df_com_rede = df_com_rede.merge(
                df_vip[['CNPJ_Normalizado', 'Rede', 'Ranking', 'Ranking Rede']],
                on='CNPJ_Normalizado',
                how='left'
            )

            # Filtros específicos para ranking de rede
            st.markdown("""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                        color: white; padding: 1rem; border-radius: 8px;
                        margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="margin: 0;">🔍 Filtros para Análise de Redes</h4>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)

            with col1:
                redes_disponiveis = sorted(df_com_rede['Rede'].dropna().unique())
                rede_selecionada = st.multiselect(
                    "🏢 Redes:",
                    options=redes_disponiveis,
                    default=redes_disponiveis if len(redes_disponiveis) <= 5 else [],
                    help="Selecione as redes para análise"
                )

            with col2:
                rankings_rede = sorted(df_com_rede['Ranking Rede'].dropna().unique())
                ranking_rede_selecionado = st.multiselect(
                    "🏅 Ranking Rede:",
                    options=rankings_rede,
                    default=rankings_rede if len(rankings_rede) <= 5 else [],
                    help="Selecione os rankings de rede"
                )

            with col3:
                tipo_analise = st.selectbox(
                    "📊 Tipo de Análise:",
                    options=["Visão Geral", "Por Volume", "Por Performance", "Por Risco"],
                    help="Escolha o tipo de análise a ser realizada"
                )

            # Aplicar filtros
            df_rede_filtrado = df_com_rede.copy()

            if rede_selecionada:
                df_rede_filtrado = df_rede_filtrado[df_rede_filtrado['Rede'].isin(rede_selecionada)]

            if ranking_rede_selecionado:
                df_rede_filtrado = df_rede_filtrado[df_rede_filtrado['Ranking Rede'].isin(ranking_rede_selecionado)]

            if not df_rede_filtrado.empty:
                # Análise baseada no tipo selecionado
                if tipo_analise == "Visão Geral":
                    # Cards de métricas gerais
                    col1, col2, col3, col4 = st.columns(4)

                    total_redes = df_rede_filtrado['Rede'].nunique()
                    total_labs_rede = len(df_rede_filtrado)
                    volume_total_rede = df_rede_filtrado['Volume_Total_2025'].sum() if 'Volume_Total_2025' in df_rede_filtrado.columns else 0

                    with col1:
                        st.metric("🏢 Total de Redes", total_redes)

                    with col2:
                        st.metric("🏥 Labs nas Redes", f"{total_labs_rede:,}")

                    with col3:
                        st.metric("📦 Volume Total", f"{volume_total_rede:,}")

                    with col4:
                        media_por_rede = volume_total_rede / total_redes if total_redes > 0 else 0
                        st.metric("📊 Média por Rede", f"{media_por_rede:,.0f}")

                    # Distribuição por rede
                    st.subheader("📊 Distribuição por Rede")
                    if 'Rede' in df_rede_filtrado.columns:
                        # Remover duplicatas baseado no CNPJ antes da contagem
                        df_sem_duplicatas_rede = df_rede_filtrado.drop_duplicates(subset=['CNPJ_PCL'], keep='first')
                        
                        rede_stats = df_sem_duplicatas_rede.groupby('Rede').agg({
                            'Nome_Fantasia_PCL': 'count',
                            'Volume_Total_2025': 'sum',
                            'Score_Risco': 'mean'
                        }).reset_index()

                        rede_stats.columns = ['Rede', 'Qtd_Labs', 'Volume_Total', 'Score_Medio_Risco']

                        col1, col2 = st.columns(2)

                        with col1:
                            # Gráfico de quantidade de labs por rede
                            fig_labs = px.bar(
                                rede_stats.sort_values('Qtd_Labs', ascending=False),
                                x='Rede',
                                y='Qtd_Labs',
                                title="🏥 Quantidade de Laboratórios por Rede",
                                color='Qtd_Labs',
                                color_continuous_scale='Blues'
                            )
                            fig_labs.update_layout(xaxis_tickangle=-45)
                            st.plotly_chart(fig_labs, use_container_width=True)

                        with col2:
                            # Gráfico de volume por rede
                            fig_volume = px.bar(
                                rede_stats.sort_values('Volume_Total', ascending=False),
                                x='Rede',
                                y='Volume_Total',
                                title="📦 Volume Total por Rede",
                                color='Volume_Total',
                                color_continuous_scale='Greens'
                            )
                            fig_volume.update_layout(xaxis_tickangle=-45)
                            st.plotly_chart(fig_volume, use_container_width=True)

                        # Tabela detalhada
                        st.subheader("📋 Detalhamento por Rede")
                        st.dataframe(
                            rede_stats.round(2),
                            use_container_width=True,
                            column_config={
                                "Rede": st.column_config.TextColumn("🏢 Rede"),
                                "Qtd_Labs": st.column_config.NumberColumn("🏥 Qtd Labs"),
                                "Volume_Total": st.column_config.NumberColumn("📦 Volume Total", format="%.0f"),
                                "Score_Medio_Risco": st.column_config.NumberColumn("⚠️ Score Médio Risco", format="%.1f")
                            }
                        )

                elif tipo_analise == "Por Volume":
                    st.subheader("📦 Análise por Volume de Coletas")

                    # Ranking de redes por volume - remover duplicatas antes da contagem
                    df_sem_duplicatas_volume = df_rede_filtrado.drop_duplicates(subset=['CNPJ_PCL'], keep='first')
                    volume_por_rede = df_sem_duplicatas_volume.groupby('Rede')['Volume_Total_2025'].agg(['sum', 'mean', 'count']).reset_index()
                    volume_por_rede.columns = ['Rede', 'Volume_Total', 'Volume_Medio', 'Qtd_Labs']
                    volume_por_rede = volume_por_rede.sort_values('Volume_Total', ascending=False)

                    # Gráfico de ranking
                    fig_ranking = px.bar(
                        volume_por_rede.head(10),
                        x='Rede',
                        y='Volume_Total',
                        title="🏆 Top 10 Redes por Volume Total",
                        color='Volume_Medio',
                        color_continuous_scale='Viridis',
                        text='Volume_Total'
                    )
                    fig_ranking.update_traces(texttemplate='%{text:.0f}', textposition='outside')
                    fig_ranking.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_ranking, use_container_width=True)

                    # Tabela detalhada
                    st.dataframe(
                        volume_por_rede.round(2),
                        use_container_width=True,
                        column_config={
                            "Rede": st.column_config.TextColumn("🏢 Rede"),
                            "Volume_Total": st.column_config.NumberColumn("📦 Volume Total", format="%.0f"),
                            "Volume_Medio": st.column_config.NumberColumn("📊 Volume Médio", format="%.1f"),
                            "Qtd_Labs": st.column_config.NumberColumn("🏥 Qtd Labs")
                        }
                    )

                elif tipo_analise == "Por Performance":
                    st.subheader("📈 Análise de Performance por Rede")

                    # Performance por rede (baseado em crescimento/variacao) - remover duplicatas
                    if 'Variacao_Percentual' in df_rede_filtrado.columns:
                        df_sem_duplicatas_perf = df_rede_filtrado.drop_duplicates(subset=['CNPJ_PCL'], keep='first')
                        perf_rede = df_sem_duplicatas_perf.groupby('Rede').agg({
                            'Variacao_Percentual': ['mean', 'count'],
                            'Volume_Total_2025': 'sum'
                        }).reset_index()

                        perf_rede.columns = ['Rede', 'Variacao_Media', 'Qtd_Labs', 'Volume_Total']
                        perf_rede = perf_rede.sort_values('Variacao_Media', ascending=False)

                        col1, col2 = st.columns(2)

                        with col1:
                            # Performance por variação
                            fig_perf = px.bar(
                                perf_rede.head(10),
                                x='Rede',
                                y='Variacao_Media',
                                title="📈 Top 10 Redes por Performance (Variação %)",
                                color='Variacao_Media',
                                color_continuous_scale='RdYlGn',
                                text='Variacao_Media'
                            )
                            fig_perf.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                            fig_perf.update_layout(xaxis_tickangle=-45)
                            st.plotly_chart(fig_perf, use_container_width=True)

                        with col2:
                            # Scatter plot: Volume vs Performance
                            fig_scatter = px.scatter(
                                perf_rede,
                                x='Volume_Total',
                                y='Variacao_Media',
                                size='Qtd_Labs',
                                color='Rede',
                                title="📊 Volume vs Performance por Rede",
                                labels={'Volume_Total': 'Volume Total', 'Variacao_Media': 'Variação Média %'}
                            )
                            st.plotly_chart(fig_scatter, use_container_width=True)

                        # Tabela de performance
                        st.dataframe(
                            perf_rede.round(2),
                            use_container_width=True,
                            column_config={
                                "Rede": st.column_config.TextColumn("🏢 Rede"),
                                "Variacao_Media": st.column_config.NumberColumn("📈 Variação Média %", format="%.2f%%"),
                                "Qtd_Labs": st.column_config.NumberColumn("🏥 Qtd Labs"),
                                "Volume_Total": st.column_config.NumberColumn("📦 Volume Total", format="%.0f")
                            }
                        )

                elif tipo_analise == "Por Risco":
                    st.subheader("⚠️ Análise de Risco por Rede")

                    if 'Score_Risco' in df_rede_filtrado.columns:
                        # Risco por rede
                        risco_rede = df_rede_filtrado.groupby('Rede').agg({
                            'Score_Risco': ['mean', 'max', 'count'],
                            'Volume_Total_2025': 'sum'
                        }).reset_index()

                        risco_rede.columns = ['Rede', 'Score_Medio', 'Score_Max', 'Qtd_Labs', 'Volume_Total']
                        risco_rede = risco_rede.sort_values('Score_Medio', ascending=False)

                        # Distribuição de risco
                        fig_risco = px.bar(
                            risco_rede.head(10),
                            x='Rede',
                            y='Score_Medio',
                            title="⚠️ Top 10 Redes por Score de Risco",
                            color='Score_Medio',
                            color_continuous_scale='Reds',
                            text='Score_Medio'
                        )
                        fig_risco.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                        fig_risco.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig_risco, use_container_width=True)

                        # Distribuição de labs por nível de risco e rede
                        col1, col2 = st.columns(2)

                        with col1:
                            # Labs de alto risco por rede
                            alto_risco = df_rede_filtrado[df_rede_filtrado['Score_Risco'] > 70].groupby('Rede').size().reset_index(name='Qtd_Alto_Risco')
                            alto_risco = alto_risco.sort_values('Qtd_Alto_Risco', ascending=False)

                            fig_alto = px.bar(
                                alto_risco.head(10),
                                x='Rede',
                                y='Qtd_Alto_Risco',
                                title="🚨 Labs de Alto Risco por Rede",
                                color='Qtd_Alto_Risco',
                                color_continuous_scale='Reds'
                            )
                            fig_alto.update_layout(xaxis_tickangle=-45)
                            st.plotly_chart(fig_alto, use_container_width=True)

                        with col2:
                            # Status de risco por rede
                            risco_status = df_rede_filtrado.groupby(['Rede', 'Status_Risco']).size().reset_index(name='Qtd')
                            fig_status = px.bar(
                                risco_status,
                                x='Rede',
                                y='Qtd',
                                color='Status_Risco',
                                title="📊 Status de Risco por Rede",
                                color_discrete_map={'Alto': '#d62728', 'Médio': '#ff7f0e', 'Baixo': '#2ca02c', 'Inativo': '#9467bd'}
                            )
                            fig_status.update_layout(xaxis_tickangle=-45)
                            st.plotly_chart(fig_status, use_container_width=True)

                        # Tabela de risco detalhada
                        st.dataframe(
                            risco_rede.round(2),
                            use_container_width=True,
                            column_config={
                                "Rede": st.column_config.TextColumn("🏢 Rede"),
                                "Score_Medio": st.column_config.NumberColumn("⚠️ Score Médio", format="%.1f"),
                                "Score_Max": st.column_config.NumberColumn("🚨 Score Máximo", format="%.1f"),
                                "Qtd_Labs": st.column_config.NumberColumn("🏥 Qtd Labs"),
                                "Volume_Total": st.column_config.NumberColumn("📦 Volume Total", format="%.0f")
                            }
                        )

                # Análise de relacionamentos (quem pertence a quem)
                st.markdown("---")
                st.subheader("🔗 Análise de Relacionamentos")

                # Mostrar hierarquia Rede -> Ranking -> Labs
                if 'Ranking' in df_rede_filtrado.columns and 'Ranking Rede' in df_rede_filtrado.columns:
                    # Criar tabela hierárquica - garantir que cada laboratório seja contado apenas uma vez
                    # Remover duplicatas baseado no CNPJ antes da contagem
                    df_sem_duplicatas = df_rede_filtrado.drop_duplicates(subset=['CNPJ_PCL'], keep='first')
                    
                    hierarquia = df_sem_duplicatas.groupby(['Rede', 'Ranking', 'Ranking Rede']).agg({
                        'Nome_Fantasia_PCL': 'count',
                        'Volume_Total_2025': 'sum'
                    }).reset_index()

                    hierarquia.columns = ['Rede', 'Ranking', 'Ranking_Rede', 'Qtd_Labs', 'Volume_Total']
                    hierarquia = hierarquia.sort_values(['Rede', 'Ranking', 'Ranking_Rede'])

                    st.dataframe(
                        hierarquia,
                        use_container_width=True,
                        column_config={
                            "Rede": st.column_config.TextColumn("🏢 Rede"),
                            "Ranking": st.column_config.TextColumn("🏆 Ranking"),
                            "Ranking Rede": st.column_config.TextColumn("🏅 Ranking Rede"),
                            "Qtd_Labs": st.column_config.NumberColumn("🏥 Qtd Labs"),
                            "Volume_Total": st.column_config.NumberColumn("📦 Volume Total", format="%.0f")
                        }
                    )

                    # Gráfico de sunburst para hierarquia
                    if len(hierarquia) > 0:
                        # Filtrar apenas dados com volume positivo para evitar erro de normalização
                        hierarquia_plot = hierarquia[hierarquia['Volume_Total'] > 0].copy()

                        if not hierarquia_plot.empty:
                            # Garantir que não há valores zero ou negativos
                            hierarquia_plot['Volume_Total'] = hierarquia_plot['Volume_Total'].clip(lower=0.1)

                            fig_sunburst = px.sunburst(
                                hierarquia_plot,
                                path=['Rede', 'Ranking', 'Ranking_Rede'],
                                values='Volume_Total',
                                title="🌅 Hierarquia: Rede → Ranking → Ranking Rede",
                                color='Qtd_Labs',
                                color_continuous_scale='Blues'
                            )
                            st.plotly_chart(fig_sunburst, use_container_width=True)
                        else:
                            st.info("ℹ️ Não há dados suficientes com volume positivo para gerar o gráfico hierárquico.")

            else:
                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
        else:
            st.warning("⚠️ Dados VIP não disponíveis. Verifique se o arquivo Excel foi carregado corretamente.")

    # ========================================
    # RODAPÉ
    # ========================================
    st.markdown("---")
    # ========================================
    # ABA 6: MANUTENÇÃO VIPs
    # ========================================
    with tab6:
        st.header("🔧 Manutenção de Dados VIP")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 1rem; border-radius: 8px; margin-bottom: 2rem;">
            <h3 style="margin: 0; color: white;">Gerenciamento de Laboratórios VIP</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Adicione, edite e gerencie laboratórios VIP com validação completa e histórico de alterações.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Importar módulos necessários
        try:
            from vip_history_manager import VIPHistoryManager
            from vip_integration import VIPIntegration
            import json
            import shutil
        except ImportError as e:
            st.error(f"Erro ao importar módulos VIP: {e}")
            st.stop()
        
        # Inicializar gerenciadores
        history_manager = VIPHistoryManager(OUTPUT_DIR)
        vip_integration = VIPIntegration(OUTPUT_DIR)
        
        # Sub-abas para diferentes funcionalidades
        sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
            "📋 Visualizar VIPs",
            "➕ Adicionar VIP",
            "✏️ Editar VIP",
            "📊 Histórico"
        ])
        
        with sub_tab1:
            st.subheader("📋 Lista de Laboratórios VIP")
            
            # Carregar dados VIP
            df_vip = DataManager.carregar_dados_vip()
            
            if df_vip is not None and not df_vip.empty:
                # Filtros
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    ranking_filtro = st.selectbox(
                        "🏆 Ranking:",
                        options=["Todos"] + sorted(df_vip['Ranking'].dropna().unique().tolist()),
                        help="Filtrar por ranking individual"
                    )
                
                with col2:
                    ranking_rede_filtro = st.selectbox(
                        "🏅 Ranking Rede:",
                        options=["Todos"] + sorted(df_vip['Ranking Rede'].dropna().unique().tolist()),
                        help="Filtrar por ranking de rede"
                    )
                
                with col3:
                    rede_filtro = st.selectbox(
                        "🏢 Rede:",
                        options=["Todas"] + sorted(df_vip['Rede'].dropna().unique().tolist()),
                        help="Filtrar por rede"
                    )
                
                # Aplicar filtros
                df_filtrado = df_vip.copy()
                
                if ranking_filtro != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['Ranking'] == ranking_filtro]
                
                if ranking_rede_filtro != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['Ranking Rede'] == ranking_rede_filtro]
                
                if rede_filtro != "Todas":
                    df_filtrado = df_filtrado[df_filtrado['Rede'] == rede_filtro]
                
                # Estatísticas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📊 Total VIPs", len(df_filtrado))
                
                with col2:
                    st.metric("🏆 Rankings", len(df_filtrado['Ranking'].unique()))
                
                with col3:
                    st.metric("🏢 Redes", len(df_filtrado['Rede'].unique()))
                
                with col4:
                    st.metric("🏅 Rankings Rede", len(df_filtrado['Ranking Rede'].unique()))
                
                # Tabela de dados
                st.subheader("📋 Dados VIP Filtrados")
                
                # Configurar colunas para exibição
                colunas_exibir = ['CNPJ', 'RAZÃO SOCIAL', 'NOME FANTASIA', 'Cidade ', 'UF', 
                                'Ranking', 'Ranking Rede', 'Rede', 'STATUS']
                
                colunas_existentes = [col for col in colunas_exibir if col in df_filtrado.columns]
                
                if colunas_existentes:
                    st.dataframe(
                        df_filtrado[colunas_existentes],
                        use_container_width=True,
                        height=400,
                        column_config={
                            "CNPJ": st.column_config.TextColumn("📄 CNPJ", help="CNPJ do laboratório"),
                            "RAZÃO SOCIAL": st.column_config.TextColumn("🏢 Razão Social"),
                            "NOME FANTASIA": st.column_config.TextColumn("🏥 Nome Fantasia"),
                            "Cidade ": st.column_config.TextColumn("🏙️ Cidade"),
                            "UF": st.column_config.TextColumn("🗺️ Estado"),
                            "Ranking": st.column_config.TextColumn("🏆 Ranking"),
                            "Ranking Rede": st.column_config.TextColumn("🏅 Ranking Rede"),
                            "Rede": st.column_config.TextColumn("🏢 Rede"),
                            "STATUS": st.column_config.TextColumn("📊 Status")
                        }
                    )
                else:
                    st.warning("Nenhuma coluna válida encontrada para exibição")
            else:
                st.warning("⚠️ Nenhum dado VIP encontrado. Execute primeiro o script de normalização.")
        
        with sub_tab2:
            st.subheader("➕ Adicionar Novo Laboratório VIP")
            
            # Formulário para adicionar VIP
            with st.form("form_adicionar_vip"):
                col1, col2 = st.columns(2)
                
                with col1:
                    cnpj_novo = st.text_input(
                        "📄 CNPJ:",
                        placeholder="00.000.000/0000-00",
                        help="CNPJ do laboratório (será validado automaticamente)"
                    )
                    
                    razao_social = st.text_input(
                        "🏢 Razão Social:",
                        placeholder="Nome da empresa"
                    )
                    
                    nome_fantasia = st.text_input(
                        "🏥 Nome Fantasia:",
                        placeholder="Nome comercial"
                    )
                    
                    cidade = st.text_input(
                        "🏙️ Cidade:",
                        placeholder="Nome da cidade"
                    )
                
                with col2:
                    uf = st.selectbox(
                        "🗺️ Estado:",
                        options=[""] + ESTADOS_BRASIL,
                        help="Selecione o estado"
                    )
                    
                    ranking = st.selectbox(
                        "🏆 Ranking:",
                        options=list(CATEGORIAS_RANKING.keys()),
                        help="Ranking individual do laboratório"
                    )
                    
                    ranking_rede = st.selectbox(
                        "🏅 Ranking Rede:",
                        options=list(CATEGORIAS_RANKING_REDE.keys()),
                        help="Ranking da rede"
                    )
                    
                    rede = st.text_input(
                        "🏢 Rede:",
                        placeholder="Nome da rede"
                    )
                
                contato = st.text_input(
                    "👤 Contato:",
                    placeholder="Nome do contato"
                )
                
                telefone = st.text_input(
                    "📞 Telefone/WhatsApp:",
                    placeholder="(00) 00000-0000"
                )
                
                observacoes = st.text_area(
                    "📝 Observações:",
                    placeholder="Observações adicionais (opcional)"
                )
                
                submitted = st.form_submit_button("➕ Adicionar VIP", type="primary")
                
                if submitted:
                    # Validações
                    erros = []
                    
                    # Validar CNPJ
                    if not cnpj_novo:
                        erros.append("CNPJ é obrigatório")
                    else:
                        valido, mensagem = vip_integration.validar_cnpj(cnpj_novo)
                        if not valido:
                            erros.append(f"CNPJ inválido: {mensagem}")
                        elif vip_integration.verificar_cnpj_vip_existe(cnpj_novo):
                            erros.append("CNPJ já existe na lista VIP")
                    
                    # Validar campos obrigatórios
                    if not razao_social:
                        erros.append("Razão Social é obrigatória")
                    
                    if not nome_fantasia:
                        erros.append("Nome Fantasia é obrigatório")
                    
                    if not uf:
                        erros.append("Estado é obrigatório")
                    
                    if not rede:
                        erros.append("Rede é obrigatória")
                    
                    if erros:
                        for erro in erros:
                            st.error(f"❌ {erro}")
                    else:
                        # Auto-completar dados se CNPJ existe nos laboratórios
                        dados_lab = vip_integration.buscar_laboratorio_por_cnpj(cnpj_novo)
                        if dados_lab:
                            if not razao_social:
                                razao_social = dados_lab.get('razao_social', '')
                            if not nome_fantasia:
                                nome_fantasia = dados_lab.get('nome_fantasia', '')
                            if not cidade:
                                cidade = dados_lab.get('cidade', '')
                            if not uf:
                                uf = dados_lab.get('estado', '')
                        
                        # Criar backup antes de adicionar
                        if VIP_AUTO_BACKUP:
                            try:
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                backup_path = os.path.join(VIP_BACKUP_DIR, f"vip_backup_{timestamp}.csv")
                                os.makedirs(VIP_BACKUP_DIR, exist_ok=True)
                                
                                if os.path.exists(os.path.join(OUTPUT_DIR, VIP_CSV_FILE)):
                                    shutil.copy2(os.path.join(OUTPUT_DIR, VIP_CSV_FILE), backup_path)
                                    st.success(f"✅ Backup criado: {backup_path}")
                            except Exception as e:
                                st.warning(f"⚠️ Erro ao criar backup: {e}")
                        
                        # Adicionar novo VIP
                        try:
                            # Carregar dados existentes
                            df_vip_atual = DataManager.carregar_dados_vip()
                            if df_vip_atual is None:
                                df_vip_atual = pd.DataFrame()
                            
                            # Criar novo registro
                            novo_registro = {
                                'CNPJ': cnpj_novo,
                                'RAZÃO SOCIAL': razao_social,
                                'NOME FANTASIA': nome_fantasia,
                                'Cidade ': cidade,
                                'UF': uf,
                                'Contato PCL': contato,
                                'Whatsapp/telefone': telefone,
                                'REP': '',  # Será preenchido automaticamente se CNPJ existir
                                'CS': '',   # Será preenchido automaticamente se CNPJ existir
                                'STATUS': 'ATIVO',
                                'Ranking': ranking,
                                'Ranking Rede': ranking_rede,
                                'Rede': rede
                            }
                            
                            # Adicionar ao DataFrame
                            df_novo = pd.DataFrame([novo_registro])
                            df_vip_atualizado = pd.concat([df_vip_atual, df_novo], ignore_index=True)
                            
                            # Salvar CSV atualizado
                            caminho_csv = os.path.join(OUTPUT_DIR, VIP_CSV_FILE)
                            df_vip_atualizado.to_csv(caminho_csv, index=False, encoding='utf-8-sig')
                            
                            # Registrar no histórico
                            history_manager.registrar_insercao(
                                cnpj=cnpj_novo,
                                dados_novos=novo_registro,
                                usuario="streamlit_user",
                                observacoes=observacoes
                            )
                            
                            # Limpar cache
                            DataManager.carregar_dados_vip.clear()
                            
                            st.success(f"✅ Laboratório VIP adicionado com sucesso!")
                            st.success(f"📄 CNPJ: {cnpj_novo}")
                            st.success(f"🏥 Nome: {nome_fantasia}")
                            
                            # Mostrar sugestões de laboratórios similares
                            sugestoes = vip_integration.obter_sugestoes_laboratorios(limite=5)
                            if sugestoes:
                                st.info("💡 Outros laboratórios que ainda não são VIP:")
                                for sug in sugestoes[:3]:
                                    st.write(f"• {sug['nome_fantasia']} ({sug['cnpj']}) - {sug['estado']}")
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao adicionar VIP: {e}")
        
        with sub_tab3:
            st.subheader("✏️ Editar Laboratório VIP")
            
            # Carregar dados VIP
            df_vip = DataManager.carregar_dados_vip()
            
            if df_vip is not None and not df_vip.empty:
                # Selecionar VIP para editar
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Busca por CNPJ ou nome
                    busca = st.text_input(
                        "🔍 Buscar VIP:",
                        placeholder="Digite CNPJ ou nome do laboratório"
                    )
                
                with col2:
                    if busca:
                        # Filtrar resultados
                        mask = (
                            df_vip['CNPJ'].str.contains(busca, case=False, na=False) |
                            df_vip['NOME FANTASIA'].str.contains(busca, case=False, na=False) |
                            df_vip['RAZÃO SOCIAL'].str.contains(busca, case=False, na=False)
                        )
                        df_filtrado = df_vip[mask]
                    else:
                        df_filtrado = df_vip
                
                if not df_filtrado.empty:
                    # Selecionar VIP
                    vip_selecionado = st.selectbox(
                        "📋 Selecionar VIP para editar:",
                        options=df_filtrado.index,
                        format_func=lambda x: f"{df_filtrado.loc[x, 'NOME FANTASIA']} - {df_filtrado.loc[x, 'CNPJ']}",
                        help="Selecione o laboratório VIP para editar"
                    )
                    
                    if vip_selecionado is not None:
                        vip_data = df_filtrado.loc[vip_selecionado]
                        
                        st.markdown("---")
                        st.subheader(f"✏️ Editando: {vip_data['NOME FANTASIA']}")
                        
                        # Formulário de edição
                        with st.form("form_editar_vip"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                cnpj_edit = st.text_input(
                                    "📄 CNPJ:",
                                    value=vip_data['CNPJ'],
                                    disabled=True,  # CNPJ não pode ser alterado
                                    help="CNPJ não pode ser alterado"
                                )
                                
                                razao_social_edit = st.text_input(
                                    "🏢 Razão Social:",
                                    value=vip_data.get('RAZÃO SOCIAL', '')
                                )
                                
                                nome_fantasia_edit = st.text_input(
                                    "🏥 Nome Fantasia:",
                                    value=vip_data.get('NOME FANTASIA', '')
                                )
                                
                                cidade_edit = st.text_input(
                                    "🏙️ Cidade:",
                                    value=vip_data.get('Cidade ', '')
                                )
                            
                            with col2:
                                uf_edit = st.selectbox(
                                    "🗺️ Estado:",
                                    options=ESTADOS_BRASIL,
                                    index=ESTADOS_BRASIL.index(vip_data.get('UF', '')) if vip_data.get('UF', '') in ESTADOS_BRASIL else 0
                                )
                                
                                ranking_edit = st.selectbox(
                                    "🏆 Ranking:",
                                    options=list(CATEGORIAS_RANKING.keys()),
                                    index=list(CATEGORIAS_RANKING.keys()).index(vip_data.get('Ranking', 'BRONZE')) if vip_data.get('Ranking', '') in CATEGORIAS_RANKING else 0
                                )
                                
                                ranking_rede_edit = st.selectbox(
                                    "🏅 Ranking Rede:",
                                    options=list(CATEGORIAS_RANKING_REDE.keys()),
                                    index=list(CATEGORIAS_RANKING_REDE.keys()).index(vip_data.get('Ranking Rede', 'BRONZE')) if vip_data.get('Ranking Rede', '') in CATEGORIAS_RANKING_REDE else 0
                                )
                                
                                rede_edit = st.text_input(
                                    "🏢 Rede:",
                                    value=vip_data.get('Rede', '')
                                )
                            
                            contato_edit = st.text_input(
                                "👤 Contato:",
                                value=vip_data.get('Contato PCL', '')
                            )
                            
                            telefone_edit = st.text_input(
                                "📞 Telefone/WhatsApp:",
                                value=vip_data.get('Whatsapp/telefone', '')
                            )
                            
                            status_edit = st.selectbox(
                                "📊 Status:",
                                options=['ATIVO', 'INATIVO', 'DELETADO'],
                                index=['ATIVO', 'INATIVO', 'DELETADO'].index(vip_data.get('STATUS', 'ATIVO'))
                            )
                            
                            observacoes_edit = st.text_area(
                                "📝 Observações da Edição:",
                                placeholder="Descreva as alterações realizadas"
                            )
                            
                            submitted_edit = st.form_submit_button("💾 Salvar Alterações", type="primary")
                            
                            if submitted_edit:
                                # Verificar se houve alterações
                                alteracoes = []
                                
                                if razao_social_edit != vip_data.get('RAZÃO SOCIAL', ''):
                                    alteracoes.append(('RAZÃO SOCIAL', vip_data.get('RAZÃO SOCIAL', ''), razao_social_edit))
                                
                                if nome_fantasia_edit != vip_data.get('NOME FANTASIA', ''):
                                    alteracoes.append(('NOME FANTASIA', vip_data.get('NOME FANTASIA', ''), nome_fantasia_edit))
                                
                                if ranking_edit != vip_data.get('Ranking', ''):
                                    alteracoes.append(('Ranking', vip_data.get('Ranking', ''), ranking_edit))
                                
                                if ranking_rede_edit != vip_data.get('Ranking Rede', ''):
                                    alteracoes.append(('Ranking Rede', vip_data.get('Ranking Rede', ''), ranking_rede_edit))
                                
                                if rede_edit != vip_data.get('Rede', ''):
                                    alteracoes.append(('Rede', vip_data.get('Rede', ''), rede_edit))
                                
                                if status_edit != vip_data.get('STATUS', ''):
                                    alteracoes.append(('STATUS', vip_data.get('STATUS', ''), status_edit))
                                
                                if alteracoes:
                                    # Criar backup antes de editar
                                    if VIP_AUTO_BACKUP:
                                        try:
                                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                            backup_path = os.path.join(VIP_BACKUP_DIR, f"vip_backup_{timestamp}.csv")
                                            os.makedirs(VIP_BACKUP_DIR, exist_ok=True)
                                            
                                            if os.path.exists(os.path.join(OUTPUT_DIR, VIP_CSV_FILE)):
                                                shutil.copy2(os.path.join(OUTPUT_DIR, VIP_CSV_FILE), backup_path)
                                                st.success(f"✅ Backup criado: {backup_path}")
                                        except Exception as e:
                                            st.warning(f"⚠️ Erro ao criar backup: {e}")
                                    
                                    # Atualizar dados
                                    try:
                                        # Atualizar DataFrame
                                        df_vip_atualizado = df_vip.copy()
                                        df_vip_atualizado.loc[vip_selecionado, 'RAZÃO SOCIAL'] = razao_social_edit
                                        df_vip_atualizado.loc[vip_selecionado, 'NOME FANTASIA'] = nome_fantasia_edit
                                        df_vip_atualizado.loc[vip_selecionado, 'Cidade '] = cidade_edit
                                        df_vip_atualizado.loc[vip_selecionado, 'UF'] = uf_edit
                                        df_vip_atualizado.loc[vip_selecionado, 'Ranking'] = ranking_edit
                                        df_vip_atualizado.loc[vip_selecionado, 'Ranking Rede'] = ranking_rede_edit
                                        df_vip_atualizado.loc[vip_selecionado, 'Rede'] = rede_edit
                                        df_vip_atualizado.loc[vip_selecionado, 'Contato PCL'] = contato_edit
                                        df_vip_atualizado.loc[vip_selecionado, 'Whatsapp/telefone'] = telefone_edit
                                        df_vip_atualizado.loc[vip_selecionado, 'STATUS'] = status_edit
                                        
                                        # Salvar CSV atualizado
                                        caminho_csv = os.path.join(OUTPUT_DIR, VIP_CSV_FILE)
                                        df_vip_atualizado.to_csv(caminho_csv, index=False, encoding='utf-8-sig')
                                        
                                        # Registrar alterações no histórico
                                        for campo, valor_anterior, valor_novo in alteracoes:
                                            history_manager.registrar_edicao(
                                                cnpj=vip_data['CNPJ'],
                                                campo_alterado=campo,
                                                valor_anterior=valor_anterior,
                                                valor_novo=valor_novo,
                                                dados_antes=vip_data.to_dict(),
                                                dados_depois=df_vip_atualizado.loc[vip_selecionado].to_dict(),
                                                usuario="streamlit_user",
                                                observacoes=observacoes_edit
                                            )
                                        
                                        # Limpar cache
                                        DataManager.carregar_dados_vip.clear()
                                        
                                        st.success(f"✅ Laboratório VIP atualizado com sucesso!")
                                        st.success(f"📝 {len(alteracoes)} campo(s) alterado(s)")
                                        
                                        # Mostrar resumo das alterações
                                        for campo, valor_anterior, valor_novo in alteracoes:
                                            st.info(f"🔄 {campo}: '{valor_anterior}' → '{valor_novo}'")
                                        
                                    except Exception as e:
                                        st.error(f"❌ Erro ao atualizar VIP: {e}")
                                else:
                                    st.info("ℹ️ Nenhuma alteração detectada")
            else:
                st.warning("⚠️ Nenhum dado VIP encontrado. Execute primeiro o script de normalização.")
        
        with sub_tab4:
            st.subheader("📊 Histórico de Alterações")
            
            # Estatísticas do histórico
            stats = history_manager.obter_estatisticas()
            
            if stats['total_alteracoes'] > 0:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📊 Total Alterações", stats['total_alteracoes'])
                
                with col2:
                    st.metric("➕ Inserções", stats['por_tipo'].get('insercao', 0))
                
                with col3:
                    st.metric("✏️ Edições", stats['por_tipo'].get('edicao', 0))
                
                with col4:
                    st.metric("🗑️ Exclusões", stats['por_tipo'].get('exclusao', 0))
                
                # Filtros para histórico
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    tipo_filtro = st.selectbox(
                        "🔍 Tipo de Alteração:",
                        options=["Todos"] + list(stats['por_tipo'].keys()),
                        help="Filtrar por tipo de alteração"
                    )
                
                with col2:
                    cnpj_filtro = st.text_input(
                        "📄 CNPJ:",
                        placeholder="Digite CNPJ para filtrar",
                        help="Filtrar por CNPJ específico"
                    )
                
                with col3:
                    dias_filtro = st.selectbox(
                        "📅 Período:",
                        options=["Todos", "Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias"],
                        help="Filtrar por período"
                    )
                
                # Obter histórico filtrado
                if cnpj_filtro:
                    historico_filtrado = history_manager.buscar_historico_cnpj(cnpj_filtro)
                else:
                    historico_filtrado = history_manager.historico
                
                # Filtrar por tipo
                if tipo_filtro != "Todos":
                    historico_filtrado = [alt for alt in historico_filtrado if alt['tipo'] == tipo_filtro]
                
                # Filtrar por período
                if dias_filtro != "Todos":
                    dias = {"Últimos 7 dias": 7, "Últimos 30 dias": 30, "Últimos 90 dias": 90}[dias_filtro]
                    data_limite = datetime.now() - timedelta(days=dias)
                    historico_filtrado = [alt for alt in historico_filtrado 
                                        if datetime.fromisoformat(alt['timestamp']) >= data_limite]
                
                # Mostrar histórico
                if historico_filtrado:
                    st.subheader(f"📋 Histórico Filtrado ({len(historico_filtrado)} registros)")
                    
                    # Ordenar por timestamp (mais recente primeiro)
                    historico_filtrado.sort(key=lambda x: x['timestamp'], reverse=True)
                    
                    for i, alt in enumerate(historico_filtrado[:20]):  # Mostrar apenas os 20 mais recentes
                        with st.expander(f"{alt['tipo'].title()} - {alt['cnpj']} - {alt['timestamp'][:19]}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Tipo:** {alt['tipo'].title()}")
                                st.write(f"**CNPJ:** {alt['cnpj']}")
                                st.write(f"**Data/Hora:** {alt['timestamp'][:19]}")
                                st.write(f"**Usuário:** {alt.get('usuario', 'N/A')}")
                            
                            with col2:
                                if alt['tipo'] == 'edicao':
                                    st.write(f"**Campo:** {alt.get('campo_alterado', 'N/A')}")
                                    st.write(f"**De:** {alt.get('valor_anterior', 'N/A')}")
                                    st.write(f"**Para:** {alt.get('valor_novo', 'N/A')}")
                                
                                if alt.get('observacoes'):
                                    st.write(f"**Observações:** {alt['observacoes']}")
                    
                    # Botão para exportar histórico
                    if st.button("📥 Exportar Histórico CSV"):
                        try:
                            caminho_export = history_manager.exportar_historico_csv()
                            if caminho_export:
                                st.success(f"✅ Histórico exportado: {caminho_export}")
                        except Exception as e:
                            st.error(f"❌ Erro ao exportar histórico: {e}")
                else:
                    st.info("ℹ️ Nenhum registro encontrado com os filtros aplicados")
            else:
                st.info("ℹ️ Nenhuma alteração registrada ainda")

    st.markdown("""
    <div class="footer">
        <p>📊 <strong>Churn PCLs v2.0</strong> - Dashboard profissional de análise de retenção de laboratórios</p>
        <p>Desenvolvido com ❤️ para otimizar a gestão de relacionamento com PCLs</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
