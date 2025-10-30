"""
Sistema Syntox Churn
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
# Importar sistema de autenticação Microsoft
from auth_microsoft import MicrosoftAuth, AuthManager, create_login_page, create_user_header
# ============================================
# FUNÇÕES DE INTEGRAÇÃO SHAREPOINT/ONEDRIVE
# ============================================
def _get_graph_config() -> Optional[Dict[str, Any]]:
    """Extrai configurações do Graph API dos secrets do Streamlit."""
    try:
        graph = st.secrets.get("graph", {})
        files = st.secrets.get("files", {})
        onedrive = st.secrets.get("onedrive", {})
        if not graph:
            return None
        return {
            "tenant_id": graph.get("tenant_id", ""),
            "client_id": graph.get("client_id", ""),
            "client_secret": graph.get("client_secret", ""),
            "hostname": graph.get("hostname", ""),
            "site_path": graph.get("site_path", ""),
            "library_name": graph.get("library_name", "Documents"),
            "user_upn": onedrive.get("user_upn", ""),
            "arquivo": files.get("arquivo", ""),
        }
    except Exception:
        return None
def _is_valid_csv(path: str) -> bool:
    """Verifica se arquivo CSV é válido."""
    try:
        if not os.path.exists(path):
            return False
        df = pd.read_csv(path, nrows=5)
        return len(df.columns) > 0
    except:
        return False
def _is_valid_parquet(path: str) -> bool:
    """Verifica se arquivo Parquet é válido."""
    try:
        if not os.path.exists(path):
            return False
        df = pd.read_parquet(path)
        return len(df.columns) > 0
    except:
        return False
def should_download_sharepoint(arquivo_remoto: str = None, force: bool = False) -> bool:
    """Verifica se deve baixar arquivo do SharePoint."""
    if force:
        return True
    # Determinar qual arquivo verificar (baseado no arquivo remoto solicitado)
    if arquivo_remoto:
        base_name = os.path.basename(arquivo_remoto)
        if base_name:
            arquivo_local = os.path.join(OUTPUT_DIR, base_name)
        else:
            arquivo_local = os.path.join(OUTPUT_DIR, "churn_analysis_latest.csv")
    else:
        arquivo_local = os.path.join(OUTPUT_DIR, "churn_analysis_latest.csv")
    # Verificar se existe arquivo local recente (< 5 minutos)
    if os.path.exists(arquivo_local):
        import time
        idade_arquivo = time.time() - os.path.getmtime(arquivo_local)
        if idade_arquivo < CACHE_TTL: # CACHE_TTL definido em config_churn.py
            return False
    return True
def baixar_sharepoint(arquivo_remoto: str = None, force: bool = False) -> Optional[str]:
    """
    Baixa arquivo do OneDrive/SharePoint via Microsoft Graph.
 
    Args:
        arquivo_remoto: Caminho do arquivo no OneDrive (usa config padrão se None)
        force: Força download mesmo se cache válido
 
    Returns:
        Caminho local do arquivo baixado ou None se falhar
    """
    cfg = _get_graph_config()
 
    # Sem configuração Graph, retornar arquivo local se existir
    if not cfg or not (cfg.get("tenant_id") and cfg.get("client_id") and cfg.get("client_secret")):
        arquivo_local = os.path.join(OUTPUT_DIR, "churn_analysis_latest.csv")
        if os.path.exists(arquivo_local):
            return arquivo_local
        return None
 
    # Verificar se precisa baixar
    if not should_download_sharepoint(arquivo_remoto=arquivo_remoto, force=force):
        # Retornar o arquivo local correspondente ao solicitado
        if arquivo_remoto:
            base_name = os.path.basename(arquivo_remoto)
            if base_name:
                arquivo_local = os.path.join(OUTPUT_DIR, base_name)
            else:
                arquivo_local = os.path.join(OUTPUT_DIR, "churn_analysis_latest.csv")
        else:
            arquivo_local = os.path.join(OUTPUT_DIR, "churn_analysis_latest.csv")
        if os.path.exists(arquivo_local):
            return arquivo_local
 
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
     
        # Usar ChurnSPConnector
        from churn_sp_connector import ChurnSPConnector
     
        connector = ChurnSPConnector(config=st.secrets)
     
        # Determinar arquivo remoto
        if arquivo_remoto is None:
            arquivo_remoto = cfg.get("arquivo", "Data Analysis/Churn PCLs/churn_analysis_latest.csv")
     
        # Baixar arquivo
        content = connector.download(arquivo_remoto)
     
        # Salvar localmente
        base_name = os.path.basename(arquivo_remoto)
        if not base_name:
            base_name = "churn_analysis_latest.csv"
     
        local_path = os.path.join(OUTPUT_DIR, base_name)
     
        with open(local_path, "wb") as f:
            f.write(content)
     
        # Validar arquivo baixado
        if _is_valid_csv(local_path) or _is_valid_parquet(local_path):
            return local_path
     
        return None
     
    except Exception as e:
        st.warning(f"⚠️ Não foi possível baixar do SharePoint: {e}")
        # Tentar usar arquivo local se existir
        arquivo_local = os.path.join(OUTPUT_DIR, "churn_analysis_latest.csv")
        if os.path.exists(arquivo_local):
            return arquivo_local
        return None
# Configuração da página
st.set_page_config(
    page_title="📊 Syntox Churn",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Syntox Churn - Sistema profissional para monitoramento de retenção de PCLs"
    }
)
# CSS moderno e profissional - Atualizado com melhorias de layout
CSS_STYLES = """
<style>
    /* Tema profissional atualizado */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ca02c;
        --warning-color: #ff7f0e;
        --danger-color: #d62728;
        --info-color: #17a2b8;
        --light-bg: #f8f9fa;
        --dark-bg: #343a40;
        --border-radius: 12px; /* Aumentado para visual mais moderno */
        --shadow: 0 4px 8px rgba(0,0,0,0.1); /* Sombra mais suave */
        --transition: all 0.3s ease;
    }
    /* Reset e base */
    * { box-sizing: border-box; }
    /* Header profissional */
    .main-header {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        padding: 2.5rem 1.5rem; /* Aumentado padding */
        border-radius: var(--border-radius);
        margin-bottom: 2.5rem;
        text-align: center;
        box-shadow: var(--shadow);
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.8rem; /* Aumentado tamanho */
        font-weight: 400;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.2rem;
    }
    /* Cards de métricas modernas - Melhorados */
    .metric-card {
        background: white;
        border-radius: var(--border-radius);
        padding: 1.5rem;
        box-shadow: var(--shadow);
        border: 1px solid #e9ecef;
        transition: var(--transition);
        text-align: center;
        margin-bottom: 1.5rem; /* Aumentado espaçamento */
        display: flex;               /* Estabilidade de altura */
        flex-direction: column;      /* Empilha valor, label, delta */
        justify-content: center;     /* Centraliza verticalmente */
        min-height: 140px;           /* Altura mínima consistente */
    }
    .metric-card:hover {
        transform: translateY(-4px); /* Mais elevação */
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .metric-value {
        font-size: 2.2rem; /* Aumentado */
        font-weight: 700;
        margin: 0.5rem 0;
        color: var(--primary-color);
    }
    .metric-label {
        font-size: 1rem; /* Ajustado */
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 0;
    }
    .metric-delta {
        font-size: 0.9rem;
        margin-top: 0.5rem;
        min-height: 1rem;            /* Reserva espaço mesmo vazia */
    }
    .metric-delta.positive { color: var(--success-color); }
    .metric-delta.negative { color: var(--danger-color); }
    /* Status badges - Ajustados */
    .status-badge {
        display: inline-block;
        padding: 0.35rem 0.85rem; /* Ajustado espaçamento */
        border-radius: 20px;
        font-size: 0.9rem;
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
        padding: 0.85rem 1.75rem; /* Ajustado */
        font-weight: 600;
        transition: var(--transition);
        box-shadow: var(--shadow);
    }
    .stButton > button:hover {
        transform: translateY(-2px); /* Mais elevação */
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
    }
    /* Sidebar moderna */
    .sidebar-header {
        background: var(--light-bg);
        padding: 1.2rem;
        border-radius: var(--border-radius);
        margin-bottom: 1.2rem;
        border-left: 5px solid var(--primary-color);
    }
    .sidebar-header h3 {
        margin: 0;
        color: var(--primary-color);
        font-size: 1.2rem;
        font-weight: 600;
    }
    /* Tabelas modernas */
    .dataframe-container {
        background: white;
        border-radius: var(--border-radius);
        padding: 1.2rem;
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
            margin-bottom: 1.5rem;
        }
        .main-header h1 {
            font-size: 2.2rem;
        }
        .metric-value {
            font-size: 1.8rem;
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
    /* Melhorias de espaçamento e layout */
    section[data-testid="stExpander"] > div {
        margin-bottom: 1rem;
    }
    .stTabs [data-testid="stMarkdownContainer"] {
        font-size: 1.1rem;
        font-weight: 600;
    }
    /* Ajuste para gráficos */
    .plotly-chart {
        margin: 1rem 0;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
        padding: 1rem;
        background: white;
    }
</style>
"""
# Injetar CSS
st.markdown(CSS_STYLES, unsafe_allow_html=True)
# ========================================
# CLASSES DO SISTEMA v2.0 - Atualizado com correções de bugs
# ========================================
@dataclass
class KPIMetrics:
    """Classe para armazenar métricas calculadas."""
    total_labs: int = 0
    churn_rate: float = 0.0
    total_coletas: int = 0
    labs_em_risco: int = 0
    ativos_7d: float = 0.0
    ativos_30d: float = 0.0
    labs_alto_risco: int = 0
    labs_medio_risco: int = 0
    labs_baixo_risco: int = 0
    labs_inativos: int = 0
    labs_critico: int = 0
    labs_recuperando: int = 0
    labs_sem_coleta_48h: int = 0
    vol_hoje_total: int = 0
    vol_d1_total: int = 0
    ativos_7d_count: int = 0
    ativos_30d_count: int = 0
class DataManager:
    """Gerenciador de dados com cache inteligente."""
    @staticmethod
    def normalizar_cnpj(cnpj: str) -> str:
        """Remove formatação do CNPJ (pontos, traços, barras)"""
        if pd.isna(cnpj) or cnpj == '':
            return ''
        # Converter numéricos para string sem decimais (evita sufixo '.0')
        if isinstance(cnpj, (int, float)):
            try:
                cnpj = str(int(cnpj))
            except Exception:
                cnpj = str(cnpj)
        # Remove tudo exceto dígitos
        cnpj_limpo = ''.join(filter(str.isdigit, str(cnpj)))
        # Garantir 14 dígitos
        if len(cnpj_limpo) < 14:
            cnpj_limpo = cnpj_limpo.zfill(14)
        elif len(cnpj_limpo) > 14:
            cnpj_limpo = cnpj_limpo[-14:]
        return cnpj_limpo
    @staticmethod
    @st.cache_data(ttl=CACHE_TTL)
    def carregar_dados_churn() -> Optional[pd.DataFrame]:
        """Carrega dados de análise de churn com cache inteligente."""
        try:
            # PRIMEIRO: Tentar baixar do SharePoint/OneDrive
            arquivo_sharepoint = baixar_sharepoint()
         
            if arquivo_sharepoint and os.path.exists(arquivo_sharepoint):
                # Tentar ler como CSV primeiro
                try:
                    df = pd.read_csv(arquivo_sharepoint, encoding=ENCODING, low_memory=False)
                    return df
                except Exception:
                    # Tentar como Parquet
                    try:
                        df = pd.read_parquet(arquivo_sharepoint, engine='pyarrow')
                        return df
                    except Exception:
                        pass
         
            # FALLBACK: Tentar arquivos locais
            # Primeiro tenta CSV (mais comum)
            arquivo_csv = os.path.join(OUTPUT_DIR, "churn_analysis_latest.csv")
            if os.path.exists(arquivo_csv):
                df = pd.read_csv(arquivo_csv, encoding=ENCODING, low_memory=False)
                return df
         
            # Fallback para parquet
            arquivo_path = os.path.join(OUTPUT_DIR, CHURN_ANALYSIS_FILE)
            if os.path.exists(arquivo_path):
                df = pd.read_parquet(arquivo_path, engine='pyarrow')
                return df
         
            return None
         
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados: {e}")
            return None
    @staticmethod
    def preparar_dados(df: pd.DataFrame) -> pd.DataFrame:
        """Prepara e limpa os dados carregados - Atualizado para coerência entre telas."""
        if df is None or df.empty:
            return pd.DataFrame()
        # Removido bloco de debug da sidebar para manter interface limpa
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
        # Filtro Active == True para coerência
        if 'Active' in df.columns:
            df = df[df['Active'] == True]
        # === Nova régua de risco diário ===
        colunas_novas = [
            "Vol_Hoje", "Vol_D1", "MM7", "MM30", "MM90", "DOW_Media",
            "Delta_D1", "Delta_MM7", "Delta_MM30", "Delta_MM90",
            "Risco_Diario", "Recuperacao"
        ]
        try:
            registros = []
            for _, r in df.iterrows():
                res = RiskEngine.classificar(r)
                registros.append(res if res else {c: None for c in colunas_novas})
            df_risk = pd.DataFrame(registros, index=df.index)
            for c in colunas_novas:
                df[c] = df_risk.get(c)
        except Exception:
            for c in colunas_novas:
                if c not in df.columns:
                    df[c] = None
        # Opcional: preservar a coluna antiga para auditoria
        if 'Status_Risco' in df.columns and 'Risco_Diario' in df.columns:
            df.rename(columns={'Status_Risco': 'Status_Risco_Legado'}, inplace=True)
        return df
    @staticmethod
    @st.cache_data(ttl=CACHE_TTL)
    def carregar_matriz_cs_normalizada() -> Optional[pd.DataFrame]:
        """Carrega dados da matriz CS normalizada com cache inteligente."""
        try:
            # PRIMEIRO: Tentar baixar do SharePoint/OneDrive
            arquivo_vip_remoto = "Data Analysis/Churn PCLs/matriz_cs_normalizada.csv"
            arquivo_sharepoint = baixar_sharepoint(arquivo_remoto=arquivo_vip_remoto)
            if arquivo_sharepoint and os.path.exists(arquivo_sharepoint):
                # Tentar ler como CSV
                try:
                    df = pd.read_csv(arquivo_sharepoint, encoding='utf-8-sig', low_memory=False)
                    # Verificar se tem coluna CNPJ ou CNPJ_PCL
                    if 'CNPJ' in df.columns:
                        coluna_cnpj = 'CNPJ'
                    elif 'CNPJ_PCL' in df.columns:
                        coluna_cnpj = 'CNPJ_PCL'
                        # Renomear para CNPJ para compatibilidade
                        df['CNPJ'] = df['CNPJ_PCL']
                    else:
                    # Warning removido - será tratado onde a função é chamada
                        return None
                    # Ler CNPJ como string para preservar zeros à esquerda
                    df['CNPJ'] = df['CNPJ'].astype(str)
                    df['CNPJ_Normalizado'] = df['CNPJ'].apply(DataManager.normalizar_cnpj)
                    # Toast removido - será exibido onde a função é chamada
                    return df
                except Exception as e:
                    # Warning removido - será tratado onde a função é chamada
                    pass
            # FALLBACK: Tentar arquivos locais
            caminhos_possiveis = [
                VIP_CSV_FILE,
                os.path.join(OUTPUT_DIR, VIP_CSV_FILE),
                os.path.join(os.path.dirname(OUTPUT_DIR), VIP_CSV_FILE),
            ]
            arquivo_csv = None
            for caminho in caminhos_possiveis:
                if os.path.exists(caminho):
                    arquivo_csv = caminho
                    break
            if arquivo_csv:
                # Ler CNPJ como string para preservar zeros à esquerda
                df = pd.read_csv(
                    arquivo_csv,
                    encoding='utf-8-sig',
                    dtype={'CNPJ': 'string'},
                    low_memory=False
                )
                # Garantir que CNPJ seja string e normalizar
                df['CNPJ'] = df['CNPJ'].astype(str)
                df['CNPJ_Normalizado'] = df['CNPJ'].apply(DataManager.normalizar_cnpj)
                # Toast removido - será exibido onde a função é chamada
                return df
            return None
        except Exception as e:
            # Error removido - será tratado onde a função é chamada
            return None
    @staticmethod
    @st.cache_data(ttl=VIP_CACHE_TTL)
    def carregar_dados_vip() -> Optional[pd.DataFrame]:
        """Carrega dados VIP do CSV normalizado com cache."""
        try:
            # Tentar baixar matriz CS do SharePoint
            arquivo_vip_remoto = "Data Analysis/Churn PCLs/matriz_cs_normalizada.csv"
            arquivo_sharepoint = baixar_sharepoint(arquivo_remoto=arquivo_vip_remoto, force=False)
            if arquivo_sharepoint and os.path.exists(arquivo_sharepoint):
                # Ler arquivo VIP
                df_vip = pd.read_csv(
                    arquivo_sharepoint,
                    encoding='utf-8-sig'
                )
                # Verificar se tem coluna CNPJ ou CNPJ_PCL
                if 'CNPJ' in df_vip.columns:
                    coluna_cnpj = 'CNPJ'
                elif 'CNPJ_PCL' in df_vip.columns:
                    coluna_cnpj = 'CNPJ_PCL'
                    # Renomear para CNPJ para compatibilidade
                    df_vip['CNPJ'] = df_vip['CNPJ_PCL']
                else:
                    # Warning removido - será tratado onde a função é chamada
                    return None
                # Ler CNPJ como string para preservar zeros à esquerda
                df_vip['CNPJ'] = df_vip['CNPJ'].astype(str)
                df_vip['CNPJ_Normalizado'] = df_vip['CNPJ'].apply(DataManager.normalizar_cnpj)
                # Toast removido - será exibido onde a função é chamada
                return df_vip
         
            # FALLBACK: Tentar múltiplos caminhos locais
            caminhos_possiveis = [
                VIP_CSV_FILE,
                os.path.join(OUTPUT_DIR, VIP_CSV_FILE),
                os.path.join(os.path.dirname(OUTPUT_DIR), VIP_CSV_FILE),
            ]
            arquivo_csv = None
            for caminho in caminhos_possiveis:
                if os.path.exists(caminho):
                    arquivo_csv = caminho
                    break
            if arquivo_csv:
                # Ler CNPJ como string para preservar zeros à esquerda
                df_vip = pd.read_csv(
                    arquivo_csv,
                    encoding='utf-8-sig',
                    dtype={'CNPJ': 'string'}
                )
                # Garantir que CNPJ seja string e normalizar
                df_vip['CNPJ'] = df_vip['CNPJ'].astype(str)
                df_vip['CNPJ_Normalizado'] = df_vip['CNPJ'].apply(DataManager.normalizar_cnpj)
                # Toast removido - será exibido onde a função é chamada
                return df_vip
            else:
                # Warning removido - será tratado onde a função é chamada
                return None
        except Exception as e:
            st.warning(f"Erro ao carregar arquivo VIP: {e}")
            return None


class RiskEngine:
    """Calcula MM7/MM30/MM90, D-1, DOW e classifica o risco diário (nova régua)."""

    @staticmethod
    def _serie_diaria_from_json(json_str: str) -> pd.Series:
        """Converte 'Dados_Diarios_2025' (dict 'YYYY-MM' -> {dia:coletas}) em série diária."""
        if pd.isna(json_str) or str(json_str).strip() in ("", "{}", "null"):
            return pd.Series(dtype="float")
        import json
        try:
            j = json.loads(json_str)
        except Exception:
            return pd.Series(dtype="float")
        rows = []
        for ym, dias in j.items():
            try:
                y, m = ym.split("-")
            except Exception:
                continue
            for d_str, v in dias.items():
                try:
                    d = int(d_str)
                    rows.append((pd.Timestamp(int(y), int(m), d), int(v)))
                except Exception:
                    continue
        if not rows:
            return pd.Series(dtype="float")
        s = pd.Series({d: v for d, v in rows}).sort_index()
        full_idx = pd.date_range(s.index.min(), s.index.max(), freq="D")
        return s.reindex(full_idx).fillna(0)

    @staticmethod
    def _rolling_means(s: pd.Series, ref_date: pd.Timestamp) -> dict:
        """MM7/MM30/MM90, D-1, média por DOW e contadores auxiliares."""
        if s.empty:
            return dict(MM7=0, MM30=0, MM90=0, D1=0, DOW=0, HOJE=0, zeros_consec=0, quedas50_consec=0)
        s = s.sort_index()
        if ref_date not in s.index:
            ref_date = s.index.max()
        hoje = float(s.loc[ref_date])
        d1 = float(s.shift(1).loc[ref_date]) if ref_date - pd.Timedelta(days=1) in s.index else 0.0
        mm7 = float(s.loc[:ref_date].tail(7).mean())
        mm30 = float(s.loc[:ref_date].tail(30).mean())
        mm90 = float(s.loc[:ref_date].tail(90).mean())
        dow = int(ref_date.weekday())
        ult_90 = s.loc[:ref_date].tail(90)
        dow_vals = ult_90[ult_90.index.weekday == dow]
        dow_mean = float(dow_vals.mean()) if len(dow_vals) else 0.0
        zeros_consec = int((s.loc[:ref_date][::-1] == 0).astype(int)
                           .groupby((s.loc[:ref_date][::-1] != 0).cumsum()).cumcount()[0] + 1) if hoje == 0 else 0

        def _is_queda50(idx):
            mm7_local = s.loc[:idx].tail(7).mean()
            return s.loc[idx] < 0.5 * mm7_local if mm7_local > 0 else False

        ultimos = s.loc[:ref_date].tail(3)
        quedas50_consec = sum([_is_queda50(idx) for idx in ultimos.index])
        return dict(MM7=mm7, MM30=mm30, MM90=mm90, D1=d1, DOW=dow_mean, HOJE=hoje,
                    zeros_consec=zeros_consec, quedas50_consec=quedas50_consec)

    @staticmethod
    def classificar(row: pd.Series) -> dict:
        """Aplica as regras do anexo e retorna métricas + 'Risco_Diario' e 'Recuperacao'."""
        s = RiskEngine._serie_diaria_from_json(row.get("Dados_Diarios_2025", "{}"))
        if s.empty:
            return {}
        ref_date = s.index.max()
        m = RiskEngine._rolling_means(s, ref_date)
        hoje, d1 = m["HOJE"], m["D1"]
        mm7, mm30, mm90, dow = m["MM7"], m["MM30"], m["MM90"], m["DOW"]

        def pct(a, b):
            return (a - b) / b * 100 if b and b != 0 else 0.0

        d_vs_d1 = pct(hoje, d1)
        d_vs_mm7 = pct(hoje, mm7)
        d_vs_mm30 = pct(hoje, mm30)
        d_vs_mm90 = pct(hoje, mm90)
        risco = "🟢 Normal"
        if (hoje >= 0.90 * mm7) and (hoje <= 1.20 * d1 if d1 > 0 else True):
            risco = "🟢 Normal"
        elif ((hoje >= 0.70 * mm7) or (hoje >= 0.70 * d1)) and (hoje >= 0.85 * mm30):
            risco = "🟡 Atenção"
        elif ((hoje >= 0.50 * mm7 and hoje < 0.70 * mm7) or (d1 > 0 and hoje >= 0.60 * d1 and hoje < 0.70 * d1)):
            risco = "🟠 Moderado"
        elif (((hoje < 0.50 * mm7) or (d1 > 0 and hoje < 0.60 * d1)) and (hoje < 0.70 * mm30)):
            risco = "🔴 Alto"
        if m["zeros_consec"] >= 7 or m["quedas50_consec"] >= 3:
            risco = "⚫ Crítico"
        if dow > 0 and abs(hoje - dow) / dow <= 0.15 and risco in {"🟡 Atenção", "🟠 Moderado"}:
            risco = "🟢 Normal"
        if m["zeros_consec"] >= 2 and risco in {"🟢 Normal", "🟡 Atenção"}:
            risco = "🟠 Moderado" if risco == "🟡 Atenção" else "🟡 Atenção"
        recuperacao = False
        ultimos_4 = s.loc[:ref_date].tail(4)
        if len(ultimos_4) == 4 and hoje >= mm7 and (ultimos_4.iloc[:3].mean() < 0.9 * mm7):
            recuperacao = True
        return {
            "Vol_Hoje": int(hoje), "Vol_D1": int(d1),
            "MM7": round(mm7, 1), "MM30": round(mm30, 1), "MM90": round(mm90, 1), "DOW_Media": round(dow, 1),
            "Delta_D1": round(d_vs_d1, 1), "Delta_MM7": round(d_vs_mm7, 1),
            "Delta_MM30": round(d_vs_mm30, 1), "Delta_MM90": round(d_vs_mm90, 1),
            "Risco_Diario": risco, "Recuperacao": recuperacao
        }


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
        # Filtro por período - Anos e Meses (dados mensais)
        st.sidebar.markdown("**📅 Período de Análise (Mensal)**")
        # Verificar anos disponíveis nos dados
        anos_disponiveis = []
        if 'N_Coletas_Jan_24' in df.columns:
            anos_disponiveis.append(2024)
        if 'N_Coletas_Jan_25' in df.columns:
            anos_disponiveis.append(2025)
        if not anos_disponiveis:
            st.sidebar.warning("⚠️ Nenhum dado mensal encontrado")
            anos_disponiveis = [2024, 2025] # fallback
        # Seleção de ano
        ano_selecionado = st.sidebar.selectbox(
            "📊 Ano de Análise:",
            options=anos_disponiveis,
            index=len(anos_disponiveis)-1, # Padrão: último ano disponível
            help="Selecione o ano para análise mensal"
        )
        # Mapeamento de meses
        meses_map = {
            'Jan': 'Janeiro', 'Fev': 'Fevereiro', 'Mar': 'Março', 'Abr': 'Abril',
            'Mai': 'Maio', 'Jun': 'Junho', 'Jul': 'Julho', 'Ago': 'Agosto',
            'Set': 'Setembro', 'Out': 'Outubro', 'Nov': 'Novembro', 'Dez': 'Dezembro'
        }
        # Meses disponíveis para o ano selecionado
        sufixo_ano = str(ano_selecionado)[-2:] # '24' ou '25'
        meses_disponiveis = []
        for mes_codigo in ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                          'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']:
            coluna_mes = f'N_Coletas_{mes_codigo}_{sufixo_ano}'
            if coluna_mes in df.columns:
                meses_disponiveis.append(mes_codigo)
        if not meses_disponiveis:
            st.sidebar.warning(f"⚠️ Nenhum mês encontrado para {ano_selecionado}")
            meses_disponiveis = ['Jan', 'Fev', 'Mar'] # fallback
        # Seleção de meses
        meses_opcoes = [f"{mes} - {meses_map.get(mes, mes)}" for mes in meses_disponiveis]
        meses_selecionados_opcoes = st.sidebar.multiselect(
            f"📅 Meses de {ano_selecionado}:",
            options=meses_opcoes,
            default=meses_opcoes, # Todos selecionados por padrão
            help=f"Selecione os meses de {ano_selecionado} para análise. Deixe todos selecionados para visão completa do ano.",
            key=f"meses_{ano_selecionado}"
        )
        # Converter para códigos de mês
        meses_selecionados = []
        for opcao in meses_selecionados_opcoes:
            mes_codigo = opcao.split(' - ')[0]
            if mes_codigo in meses_disponiveis:
                meses_selecionados.append(mes_codigo)
        # Armazenar filtros para uso posterior
        filtros['ano_selecionado'] = ano_selecionado
        filtros['meses_selecionados'] = meses_selecionados
        filtros['sufixo_ano'] = sufixo_ano
        # Mostrar período selecionado (texto discreto)
        meses_nomes = [meses_map.get(mes, mes) for mes in meses_selecionados]
        periodo_texto = f"{ano_selecionado}: {', '.join(meses_nomes[:3])}" # Max 3 meses no texto
        if len(meses_selecionados) > 3:
            periodo_texto += f" +{len(meses_selecionados)-3}..."
        st.sidebar.markdown(f"<small>📊 {periodo_texto}</small>", unsafe_allow_html=True)
        self.filtros = filtros
        return filtros
    def aplicar_filtros(self, df: pd.DataFrame, filtros: Dict[str, Any]) -> pd.DataFrame:
        """Aplica filtros otimizados ao DataFrame - Atualizado para coerência."""
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
        # Filtro por período (compatibilidade com filtros antigos)
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
        # Para dados mensais, o filtro principal será usado nos cálculos dos gráficos
        # Os filtros 'ano_selecionado', 'meses_selecionados' e 'sufixo_ano' são usados
        # diretamente nas funções de cálculo dos gráficos
        return df_filtrado
class KPIManager:
    """Gerenciador de cálculos de KPIs - Atualizado para coerência entre telas."""
    @staticmethod
    def calcular_kpis(df: pd.DataFrame) -> KPIMetrics:
        if df.empty:
            return KPIMetrics()
        metrics = KPIMetrics()
        df_recent = df[df['Dias_Sem_Coleta'] <= 90].copy() if 'Dias_Sem_Coleta' in df.columns else df.copy()
        metrics.total_labs = len(df_recent)
        # Distribuição por Risco_Diario
        labs_normal = labs_atencao = labs_moderado = labs_alto = labs_critico = 0
        if 'Risco_Diario' in df_recent.columns:
            c = df_recent['Risco_Diario'].value_counts()
            labs_normal = c.get('🟢 Normal', 0)
            labs_atencao = c.get('🟡 Atenção', 0)
            labs_moderado = c.get('🟠 Moderado', 0)
            labs_alto = c.get('🔴 Alto', 0)
            labs_critico = c.get('⚫ Crítico', 0)
        metrics.labs_baixo_risco = labs_normal + labs_atencao
        metrics.labs_medio_risco = labs_moderado
        metrics.labs_alto_risco = labs_alto + labs_critico
        metrics.labs_em_risco = labs_moderado + labs_alto + labs_critico
        metrics.labs_critico = labs_critico
        metrics.churn_rate = (metrics.labs_em_risco / metrics.total_labs * 100) if metrics.total_labs else 0
        # Total coletas 2025
        meses_2025 = ChartManager._meses_ate_hoje(df_recent, 2025)
        cols = [f'N_Coletas_{m}_25' for m in meses_2025 if f'N_Coletas_{m}_25' in df_recent.columns]
        metrics.total_coletas = int(df_recent[cols].sum().sum()) if cols else 0
        # Volumes diários
        metrics.vol_hoje_total = int(df_recent['Vol_Hoje'].fillna(0).sum()) if 'Vol_Hoje' in df_recent.columns else 0
        metrics.vol_d1_total = int(df_recent['Vol_D1'].fillna(0).sum()) if 'Vol_D1' in df_recent.columns else 0
        # Recuperação e zeros consecutivos
        if 'Recuperacao' in df_recent.columns:
            metrics.labs_recuperando = int(df_recent['Recuperacao'].fillna(False).sum())
        if {'Vol_Hoje', 'Vol_D1'}.issubset(df_recent.columns):
            zeros_48h = df_recent[
                df_recent['Vol_Hoje'].fillna(0).eq(0) &
                df_recent['Vol_D1'].fillna(0).eq(0)
            ]
            metrics.labs_sem_coleta_48h = len(zeros_48h)
        # Ativos recentes
        if 'Dias_Sem_Coleta' in df_recent.columns and metrics.total_labs > 0:
            ativos_7d_df = df_recent[df_recent['Dias_Sem_Coleta'] <= 7]
            ativos_30d_df = df_recent[df_recent['Dias_Sem_Coleta'] <= 30]
            metrics.ativos_7d_count = len(ativos_7d_df)
            metrics.ativos_30d_count = len(ativos_30d_df)
            metrics.ativos_7d = metrics.ativos_7d_count / metrics.total_labs * 100
            metrics.ativos_30d = metrics.ativos_30d_count / metrics.total_labs * 100
        return metrics
class ChartManager:
    """Gerenciador de criação de gráficos - Atualizado com correções de bugs e layouts."""
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
        if df.empty:
            st.info("📊 Nenhum dado disponível para o gráfico")
            return
        if 'Risco_Diario' not in df.columns:
            st.warning("⚠️ Coluna 'Risco_Diario' não encontrada nos dados.")
            return
        status_counts = df['Risco_Diario'].value_counts()
        cores_map = {
            '🟢 Normal': '#16A34A',
            '🟡 Atenção': '#F59E0B',
            '🟠 Moderado': '#FB923C',
            '🔴 Alto': '#DC2626',
            '⚫ Crítico': '#111827'
        }
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="📊 Distribuição de Risco Diário",
            color=status_counts.index,
            color_discrete_map=cores_map
        )
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label+value',
            texttemplate='%{label}<br>%{value} labs<br>(%{percent})',
            hovertemplate='<b>%{label}</b><br>%{value} laboratórios<br>%{percent}<extra></extra>'
        )
        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            height=500,
            margin=dict(l=40, r=40, t=40, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)
    @staticmethod
    def criar_grafico_top_labs(df: pd.DataFrame, top_n: int = 10):
        if df.empty:
            st.info("📊 Nenhum dado disponível para o gráfico")
            return
        if 'Risco_Diario' not in df.columns:
            st.warning("⚠️ Coluna 'Risco_Diario' não encontrada nos dados.")
            return
        labs_risco = df[df['Risco_Diario'].isin(['🟠 Moderado', '🔴 Alto', '⚫ Crítico'])].copy()
        if labs_risco.empty:
            st.info("✅ Nenhum laboratório em risco encontrado!")
            return
        # Ordenar por maior queda vs MM7 e menor volume do dia
        if 'Delta_MM7' in labs_risco.columns:
            labs_risco = labs_risco.sort_values(['Delta_MM7', 'Vol_Hoje'], ascending=[True, True])
        else:
            labs_risco = labs_risco.sort_values('Vol_Hoje', ascending=True)
        cores_map = {'🟠 Moderado': '#FB923C', '🔴 Alto': '#DC2626', '⚫ Crítico': '#111827'}
        fig = px.bar(
            labs_risco.head(top_n),
            x='Vol_Hoje',
            y='Nome_Fantasia_PCL',
            orientation='h',
            title=f"🚨 Top {top_n} Laboratórios em Risco (Diário)",
            color='Risco_Diario',
            color_discrete_map=cores_map,
            text='Delta_MM7'
        )
        fig.update_traces(texttemplate='%{text:.1f}% vs MM7', textposition='outside')
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            xaxis_title="Coletas (Hoje)",
            yaxis_title="Laboratório",
            showlegend=True,
            height=500,
            margin=dict(l=40, r=40, t=40, b=100)
        )
        st.plotly_chart(fig, use_container_width=True)
    @staticmethod
    def criar_grafico_media_diaria(df: pd.DataFrame, lab_selecionado: str = None):
        """Cria gráfico de média diária por mês usando dados reais de 2025."""
        if df.empty:
            st.info("📊 Nenhum dado disponível para o gráfico")
            return
        if not lab_selecionado:
            st.info("📊 Selecione um laboratório para visualizar a média diária")
            return
            
        lab_data = df[df['Nome_Fantasia_PCL'] == lab_selecionado]
        if lab_data.empty:
            st.info("📊 Laboratório não encontrado")
            return
            
        lab = lab_data.iloc[0]
        
        # Verificar se temos dados diários reais de 2025
        if 'Dados_Diarios_2025' not in lab or pd.isna(lab['Dados_Diarios_2025']) or lab['Dados_Diarios_2025'] == '{}':
            st.info("📊 Nenhum dado diário disponível para 2025. Use o gerador para atualizar os dados.")
            return
        
        import json
        try:
            # Carregar dados diários reais
            dados_diarios = json.loads(lab['Dados_Diarios_2025'])
        except (json.JSONDecodeError, TypeError):
            st.info("📊 Erro ao carregar dados diários. Use o gerador para atualizar os dados.")
            return
        
        if not dados_diarios:
            st.info("📊 Nenhum dado diário disponível para 2025.")
            return
        
        # Calcular média diária real baseada em dias com coleta
        meses_ordem = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        medias_diarias = []
        meses_com_dados = []
        
        for mes_key, dias_mes in dados_diarios.items():
            # Extrair mês do formato "2025-10"
            try:
                ano, mes_num = mes_key.split('-')
                mes_num = int(mes_num)
                if mes_num >= 1 and mes_num <= 12:
                    mes_nome = meses_ordem[mes_num - 1]
                    
                    # Calcular total de coletas e dias com coleta para este mês
                    total_coletas = sum(int(coletas) for coletas in dias_mes.values())
                    dias_com_coleta = len(dias_mes)
                    
                    # Média diária = total de coletas / dias com coleta (não dias do mês)
                    if dias_com_coleta > 0:
                        media_diaria = total_coletas / dias_com_coleta
                        medias_diarias.append(media_diaria)
                        meses_com_dados.append(mes_nome)
            except (ValueError, IndexError):
                continue
        
        if not medias_diarias:
            st.info("📊 Nenhuma coleta encontrada nos dados diários de 2025.")
            return
        
        # Criar gráfico
        fig = px.bar(
            x=meses_com_dados,
            y=medias_diarias,
            title=f"📊 Média Diária Real por Mês - {lab_selecionado}<br><sup>Baseado em dias com coleta real</sup>",
            color=medias_diarias,
            color_continuous_scale='Blues',
            text=[f"{val:.1f}" for val in medias_diarias]
        )
     
        fig.update_traces(
            texttemplate='%{text} coletas',
            textposition='outside',
            hovertemplate='<b>Mês:</b> %{x}<br><b>Média Diária:</b> %{y:.1f} coletas<br><sup>Baseado em dias com coleta real</sup><extra></extra>'
        )
     
        fig.update_layout(
            xaxis_title="Mês",
            yaxis_title="Média Diária (Coletas)",
            showlegend=False,
            height=600,
            margin=dict(l=60, r=60, t=80, b=80),
            autosize=True,
            font=dict(size=14)
        )
     
        st.plotly_chart(fig, use_container_width=True)
        
        # Explicação metodológica
        with st.expander("ℹ️ Sobre Esta Análise", expanded=False):
            st.markdown(f"""
            **Como é calculada a média diária real:**
            1. **Base de dados**: Dados reais de coletas de 2025 por dia
            2. **Cálculo**: Total de coletas do mês ÷ dias com coleta (não dias do mês)
            3. **Vantagem**: Mostra a produtividade real nos dias de trabalho
            4. **Exemplo**: Se em Outubro houve 8 coletas em 4 dias diferentes, a média é 2.0 coletas/dia
            
            **💡 Insight**: Esta análise mostra:
            - Produtividade real nos dias de coleta
            - Padrões de intensidade de trabalho
            - Comparação mais precisa entre meses
            """)
    @staticmethod
    def criar_grafico_coletas_por_dia(df: pd.DataFrame, lab_selecionado: str = None):
        """Cria gráfico de coletas por dia do mês usando dados reais de 2025."""
        if df.empty:
            st.info("📊 Nenhum dado disponível para o gráfico")
            return
        if lab_selecionado:
            lab_data = df[df['Nome_Fantasia_PCL'] == lab_selecionado]
            if not lab_data.empty:
                lab = lab_data.iloc[0]
             
                # Verificar se temos dados diários reais de 2025
                if 'Dados_Diarios_2025' not in lab or pd.isna(lab['Dados_Diarios_2025']) or lab['Dados_Diarios_2025'] == '{}':
                    st.info("📊 Nenhum dado diário disponível para 2025. Use o gerador para atualizar os dados.")
                    return
                
                import json
                try:
                    # Carregar dados diários reais
                    dados_diarios = json.loads(lab['Dados_Diarios_2025'])
                except (json.JSONDecodeError, TypeError):
                    st.info("📊 Erro ao carregar dados diários. Use o gerador para atualizar os dados.")
                    return
                
                if not dados_diarios:
                    st.info("📊 Nenhum dado diário disponível para 2025.")
                    return
                
                # Converter dados para DataFrame
                dados_grafico = []
                meses_ordem = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                
                for mes_key, dias_mes in dados_diarios.items():
                    # Extrair mês do formato "2025-10"
                    try:
                        ano, mes_num = mes_key.split('-')
                        mes_num = int(mes_num)
                        if mes_num >= 1 and mes_num <= 12:
                            mes_nome = meses_ordem[mes_num - 1]
                            
                            # Adicionar apenas dias com coletas reais
                            for dia_str, coletas in dias_mes.items():
                                dia = int(dia_str)
                                if coletas > 0:  # Só mostrar dias com coletas
                                    dados_grafico.append({
                                        'Dia': dia,
                                        'Mês': mes_nome,
                                        'Coletas': int(coletas)
                                    })
                    except (ValueError, IndexError):
                        continue
                
                if not dados_grafico:
                    st.info("📊 Nenhuma coleta encontrada nos dados diários de 2025.")
                    return
                
                df_grafico = pd.DataFrame(dados_grafico)
             
                # Criar gráfico de linha interativo
                fig = px.line(
                    df_grafico,
                    x='Dia',
                    y='Coletas',
                    color='Mês',
                    title=f"📅 Coletas por Dia do Mês - {lab_selecionado}",
                    markers=True,
                    line_shape='linear'
                )
             
                # Configurar tooltip personalizado com nome correto do mês
                fig.update_traces(
                    hovertemplate='<b>Dia:</b> %{x}<br><b>Mês:</b> %{fullData.name}<br><b>Coletas:</b> %{y:.0f}<extra></extra>'
                )
             
                fig.update_layout(
                    xaxis_title="Dia do Mês (1-31)",
                    yaxis_title="Número de Coletas",
                    xaxis=dict(tickmode='linear', tick0=1, dtick=5),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.15,
                        xanchor="center",
                        x=0.5,
                        bgcolor="rgba(255,255,255,0.8)",
                        bordercolor="rgba(0,0,0,0.2)",
                        borderwidth=1
                    ),
                    height=600,
                    margin=dict(l=60, r=60, t=80, b=120),  # Margem inferior maior para legenda
                    autosize=True,
                    font=dict(size=14),
                    # Tornar o gráfico mais interativo
                    hovermode='x unified',
                    # Melhorar a aparência das linhas
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                
                # Adicionar anotação explicativa
                fig.add_annotation(
                    text="💡 Clique nos meses na legenda para mostrar/ocultar linhas e comparar visualmente",
                    xref="paper", yref="paper",
                    x=0.5, y=-0.25,
                    showarrow=False,
                    font=dict(size=12, color="gray"),
                    xanchor="center"
                )
             
                st.plotly_chart(fig, use_container_width=True)
    @staticmethod
    def criar_grafico_media_dia_semana_novo(df: pd.DataFrame, lab_selecionado: str = None, filtros: dict = None):
        """NOVA VERSÃO - Cria gráfico de distribuição de coletas por dia da semana usando dados reais de 2025."""
        if df.empty:
            st.info("📊 Nenhum dado disponível para o gráfico")
            return
        if not lab_selecionado:
            st.info("📊 Selecione um laboratório para visualizar a distribuição semanal")
            return
            
        lab_data = df[df['Nome_Fantasia_PCL'] == lab_selecionado]
        if lab_data.empty:
            st.info("📊 Laboratório não encontrado")
            return
            
        lab = lab_data.iloc[0]
        
        # Verificar se temos dados semanais reais de 2025
        if 'Dados_Semanais_2025' not in lab or pd.isna(lab['Dados_Semanais_2025']) or lab['Dados_Semanais_2025'] == '{}':
            st.info("📊 Nenhum dado semanal disponível para 2025. Use o gerador para atualizar os dados.")
            return
        
        import json
        try:
            dados_semanais = json.loads(lab['Dados_Semanais_2025'])
        except (json.JSONDecodeError, TypeError):
            st.info("📊 Erro ao carregar dados semanais. Use o gerador para atualizar os dados.")
            return
        
        if not dados_semanais:
            st.info("📊 Nenhum dado semanal disponível para 2025.")
            return
        
        # NOVA IMPLEMENTAÇÃO - Criar dados de forma mais simples e direta
        dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        cores_dias = {
            'Segunda': '#1f77b4', 'Terça': '#ff7f0e', 'Quarta': '#2ca02c', 'Quinta': '#d62728',
            'Sexta': '#9467bd', 'Sábado': '#8c564b', 'Domingo': '#e377c2'
        }
        
        # Criar lista de dados de forma mais direta
        dados_grafico = []
        total_coletas = 0
        
        for dia in dias_semana:
            coletas = dados_semanais.get(dia, 0)
            total_coletas += coletas
            dados_grafico.append({
                'dia': dia,
                'coletas': coletas,
                'cor': cores_dias[dia]
            })
        
        max_coletas = max((item['coletas'] for item in dados_grafico), default=0)
        y_axis_max = max_coletas * 1.2 if max_coletas > 0 else 10

        # Calcular percentuais
        for item in dados_grafico:
            if total_coletas > 0:
                item['percentual'] = round((item['coletas'] / total_coletas) * 100, 1)
            else:
                item['percentual'] = 0.0
        
        # CRIAR GRÁFICO NOVO DO ZERO
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        # Adicionar barras uma por uma para ter controle total
        for i, row in enumerate(dados_grafico):
            fig.add_trace(go.Bar(
                x=[row['dia']],
                y=[row['coletas']],
                name=row['dia'],
                marker_color=row['cor'],
                text=[f"{row['coletas']} coletas<br>({row['percentual']:.1f}%)"],
                textposition='outside',
                hovertemplate=f"<b>{row['dia']}</b><br>" +
                             f"Coletas: {row['coletas']}<br>" +
                             f"Percentual: {row['percentual']:.1f}% da semana<extra></extra>",
                showlegend=False
            ))
        
        # Configurar layout
        fig.update_layout(
            title=f"📅 Distribuição Real de Coletas por Dia da Semana<br><sup>{lab_selecionado} | Total semanal: {total_coletas} coletas</sup>",
            xaxis_title="Dia da Semana",
            yaxis_title="Coletas por Dia",
            height=600,
            margin=dict(l=60, r=60, t=100, b=80),
            font=dict(size=14),
            title_font_size=18,
            yaxis=dict(range=[0, y_axis_max])
        )
        
        # Adicionar linha de média diária
        if total_coletas > 0:
            media_diaria = total_coletas / 7
            fig.add_hline(
                y=media_diaria,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Média diária: {media_diaria:.1f} coletas",
                annotation_position="top right"
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            dia_max = max(dados_grafico, key=lambda x: x['coletas'])
            st.metric("📈 Dia Mais Forte", dia_max['dia'], f"{dia_max['coletas']:.0f} coletas")
        with col2:
            dia_min = min(dados_grafico, key=lambda x: x['coletas'])
            st.metric("📉 Dia Mais Fraco", dia_min['dia'], f"{dia_min['coletas']:.0f} coletas")
        with col3:
            max_coletas = max(item['coletas'] for item in dados_grafico)
            min_coletas = min(item['coletas'] for item in dados_grafico)
            variacao = ((max_coletas - min_coletas) / max_coletas * 100) if max_coletas > 0 else 0
            st.metric("📊 Variação Semanal", f"{variacao:.1f}%", "diferença máxima")
        
        # Debug removido após validação dos percentuais

    @staticmethod
    def criar_grafico_media_dia_semana(df: pd.DataFrame, lab_selecionado: str = None, filtros: dict = None):
        """Cria gráfico de distribuição de coletas por dia da semana usando dados reais de 2025."""
        if df.empty:
            st.info("📊 Nenhum dado disponível para o gráfico")
            return
        if not lab_selecionado:
            st.info("📊 Selecione um laboratório para visualizar a distribuição semanal")
            return
        lab_data = df[df['Nome_Fantasia_PCL'] == lab_selecionado]
        if not lab_data.empty:
            lab = lab_data.iloc[0]
            
            # Verificar se temos dados semanais reais de 2025
            if 'Dados_Semanais_2025' not in lab or pd.isna(lab['Dados_Semanais_2025']) or lab['Dados_Semanais_2025'] == '{}':
                st.info("📊 Nenhum dado semanal disponível para 2025. Use o gerador para atualizar os dados.")
                return
            
            import json
            try:
                # Carregar dados semanais reais
                dados_semanais = json.loads(lab['Dados_Semanais_2025'])
            except (json.JSONDecodeError, TypeError):
                st.info("📊 Erro ao carregar dados semanais. Use o gerador para atualizar os dados.")
                return
            
            if not dados_semanais:
                st.info("📊 Nenhum dado semanal disponível para 2025.")
                return
            
            # Converter dados para DataFrame
            dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            cores_dias = {
                'Segunda': '#1f77b4', # Azul
                'Terça': '#ff7f0e', # Laranja
                'Quarta': '#2ca02c', # Verde
                'Quinta': '#d62728', # Vermelho
                'Sexta': '#9467bd', # Roxo
                'Sábado': '#8c564b', # Marrom
                'Domingo': '#e377c2' # Rosa
            }
            
            dados_semana = []
            total_coletas_semana = 0
            
            for dia in dias_semana:
                coletas_dia = dados_semanais.get(dia, 0)
                total_coletas_semana += coletas_dia
                dados_semana.append({
                    'Dia_Semana': dia,
                    'Coletas_Reais': coletas_dia,
                    'Cor': cores_dias[dia]
                })
            
            df_semana = pd.DataFrame(dados_semana)
            
            # Calcular percentuais corretos baseados nos dados reais
            if total_coletas_semana > 0:
                df_semana['Percentual'] = (df_semana['Coletas_Reais'] / total_coletas_semana * 100).round(1)
            else:
                df_semana['Percentual'] = 0.0
            # Criar título informativo
            periodo_texto = "dados reais de 2025"
            
            # Calcular média diária correta (soma das coletas semanais / 7)
            media_diaria = total_coletas_semana / 7 if total_coletas_semana > 0 else 0
            
            # Gráfico de barras
            max_coletas_semana = df_semana['Coletas_Reais'].max() if not df_semana.empty else 0
            y_axis_max = max_coletas_semana * 1.2 if max_coletas_semana > 0 else 10
            fig = px.bar(
                df_semana,
                x='Dia_Semana',
                y='Coletas_Reais',
                title=f"📅 Distribuição Real de Coletas por Dia da Semana<br><sup>{lab_selecionado} | Baseado em: {periodo_texto} | Total semanal: {total_coletas_semana:.0f} coletas</sup>",
                color='Dia_Semana',
                color_discrete_map=cores_dias,
                text='Coletas_Reais'
            )
            # Usar hovertemplate com cálculo direto do percentual
            fig.update_traces(
                texttemplate='%{text:.0f} coletas<br>(%{customdata:.1f}%)',
                textposition='outside',
                customdata=df_semana['Percentual'],
                hovertemplate='<b>%{x}</b><br>Coletas: %{y:.0f}<br>Percentual: %{customdata:.1f}% da semana<extra></extra>'
            )
            fig.update_layout(
                xaxis_title="Dia da Semana",
                yaxis_title="Coletas por Dia",
                showlegend=False,
                coloraxis_showscale=False,
                height=700,  # Aumentado significativamente para destaque
                margin=dict(l=60, r=60, t=100, b=80),  # Margens aumentadas
                autosize=True,  # Responsivo
                font=dict(size=14),  # Fonte maior para melhor legibilidade
                title_font_size=18,  # Título maior
                yaxis=dict(range=[0, y_axis_max])
            )
            # Adicionar linha de referência da média diária
            if media_diaria > 0:
                fig.add_hline(
                    y=media_diaria,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Média diária: {media_diaria:.1f} coletas",
                    annotation_position="top right"
                )
            st.plotly_chart(fig, use_container_width=True)
            # Métricas adicionais
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "📈 Dia Mais Forte",
                    df_semana.loc[df_semana['Coletas_Reais'].idxmax(), 'Dia_Semana'],
                    f"{df_semana['Coletas_Reais'].max():.0f} coletas"
                )
            with col2:
                st.metric(
                    "📉 Dia Mais Fraco",
                    df_semana.loc[df_semana['Coletas_Reais'].idxmin(), 'Dia_Semana'],
                    f"{df_semana['Coletas_Reais'].min():.0f} coletas"
                )
            with col3:
                variacao_semanal = (df_semana['Coletas_Reais'].max() - df_semana['Coletas_Reais'].min()) / df_semana['Coletas_Reais'].max() * 100 if df_semana['Coletas_Reais'].max() > 0 else 0
                st.metric(
                    "📊 Variação Semanal",
                    f"{variacao_semanal:.1f}%",
                    "diferença máxima"
                )
            # Explicação metodológica
            with st.expander("ℹ️ Sobre Esta Análise", expanded=False):
                st.markdown(f"""
                **Como é calculada a distribuição semanal:**
                1. **Base de dados**: Dados reais de coletas de 2025 ({periodo_texto})
                2. **Distribuição real**: Baseada nas datas exatas das coletas (createdAt)
                   - **Total semanal**: {total_coletas_semana:.0f} coletas
                   - **Percentuais**: Calculados baseados na distribuição real dos dados
                3. **Média diária**: {media_diaria:.1f} coletas (total semanal ÷ 7)
                **💡 Insight**: Esta análise mostra:
                - Padrões reais de coleta do laboratório
                - Dias com maior/menor movimento baseado em dados históricos
                - Oportunidades de otimização de recursos
                **⚠️ Importante**: Estes são valores estimados baseados em padrões históricos.
                Dados diários reais forneceriam análise mais precisa.
                """)
    @staticmethod
    def criar_grafico_evolucao_mensal(df: pd.DataFrame, lab_selecionado: str = None, chart_key: str = "default"):
        """Cria gráfico de evolução mensal - Atualizado com correções de diferença 2024/2025."""
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
                valores_2025 = [lab.get(col, 0) for col in colunas_meses]
             
                # Dados 2024 (mesmos meses para comparação direta)
                colunas_2024 = [f'N_Coletas_{mes}_24' for mes in meses]
                valores_2024 = [lab.get(col, 0) for col in colunas_2024]
             
                # Calcular médias - Corrigido agrupamento temporal
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
                fig.data[0].line.color = '#1f77b4' # Azul para 2025
                fig.data[1].line.color = '#ff7f0e' # Laranja para 2024
                fig.data[2].line.color = '#1f77b4' # Azul claro para média 2025
                fig.data[2].line.dash = 'dash'
                fig.data[3].line.color = '#ff7f0e' # Laranja claro para média 2024
                fig.data[3].line.dash = 'dash'
                fig.update_layout(
                    xaxis_title="Mês",
                    yaxis_title="Número de Coletas",
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.15,
                        xanchor="center",
                        x=0.5
                    ),
                    height=600,  # Aumentado conforme solicitado
                    margin=dict(l=60, r=60, t=60, b=80),  # Margens aumentadas para evitar cortes
                    autosize=True,  # Responsivo
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True, key=f"evolucao_mensal_lab_{chart_key}")
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
                hovermode='x unified',
                height=600,  # Aumentado conforme solicitado
                margin=dict(l=60, r=60, t=60, b=80),  # Margens aumentadas
                autosize=True  # Responsivo
            )
            st.plotly_chart(fig, use_container_width=True, key=f"evolucao_mensal_agregado_{chart_key}")
class UIManager:
    """Gerenciador da interface do usuário - Atualizado com tabs."""
    @staticmethod
    def renderizar_header():
        """Renderiza o cabeçalho principal."""
        st.markdown("""
        <div class="main-header">
            <h1>📊 Syntox Churn</h1>
            <p>Dashboard profissional para análise de retenção de laboratórios</p>
        </div>
        """, unsafe_allow_html=True)
    @staticmethod
    def renderizar_kpi_cards(metrics: KPIMetrics):
        """Renderiza cards de KPIs modernos - Atualizado rótulo total labs."""
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            risco_total_txt = f"Risco total: {metrics.labs_em_risco:,}" if metrics.labs_em_risco else "Risco total: 0"
            recuperacao_txt = f"Recuperação: {metrics.labs_recuperando:,}" if metrics.labs_recuperando else "Recuperação: 0"
            delta_text = f"{risco_total_txt} | {recuperacao_txt}"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{metrics.total_labs:,}</div>
                <div class="metric-label">Labs monitorados (≤90 dias)</div>
                <div class="metric-delta">{delta_text}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            delta_text = f"D-1: {metrics.vol_d1_total:,} | YTD: {metrics.total_coletas:,}"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{metrics.vol_hoje_total:,}</div>
                <div class="metric-label">Coletas Hoje</div>
                <div class="metric-delta">{delta_text}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            delta_text = f"⚫ Críticos: {metrics.labs_critico:,}"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{metrics.labs_alto_risco:,}</div>
                <div class="metric-label">Labs 🔴 & ⚫ (Alto + Crítico)</div>
                <div class="metric-delta">{delta_text}</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            delta_class = "positive" if metrics.ativos_7d >= 80 else "negative"
            ativos_label = f"Ativos 7D: {metrics.ativos_7d:.1f}% ({metrics.ativos_7d_count}/{metrics.total_labs})" if metrics.total_labs else "Ativos 7D: --"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{metrics.labs_sem_coleta_48h:,}</div>
                <div class="metric-label">Sem Coleta (48h)</div>
                <div class="metric-delta {delta_class}">{ativos_label}</div>
            </div>
            """, unsafe_allow_html=True)
class MetricasAvancadas:
    """Classe para métricas avançadas de laboratórios - Atualizado organização e comparativos."""
 
    @staticmethod
    def calcular_metricas_lab(df: pd.DataFrame, lab_nome: str) -> dict:
        """Calcula métricas avançadas para um laboratório específico - Atualizado score."""
        lab_data = df[df['Nome_Fantasia_PCL'] == lab_nome]
     
        if lab_data.empty:
            return {}
     
        lab = lab_data.iloc[0]
     
        # Total de coletas 2025 (até o mês atual)
        meses_2025 = ChartManager._meses_ate_hoje(df, 2025)
        colunas_2025 = [f'N_Coletas_{mes}_25' for mes in meses_2025]
        total_coletas_2025 = sum(lab.get(col, 0) for col in colunas_2025)
     
        # Média dos últimos 3 meses (dinâmico)
        if len(meses_2025) >= 3:
            ultimos_3_meses = meses_2025[-3:]
        else:
            ultimos_3_meses = meses_2025
        colunas_3_meses = [f'N_Coletas_{mes}_25' for mes in ultimos_3_meses]
        media_3_meses = sum(lab.get(col, 0) for col in colunas_3_meses) / len(colunas_3_meses) if colunas_3_meses else 0
     
        # Média diária (últimos 3 meses)
        dias_3_meses = 90 # Aproximadamente 3 meses
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

        vol_hoje = lab.get('Vol_Hoje', 0)
        vol_hoje = int(vol_hoje) if pd.notna(vol_hoje) else 0
        vol_d1 = lab.get('Vol_D1', 0)
        vol_d1 = int(vol_d1) if pd.notna(vol_d1) else 0
        delta_mm7_val = lab.get('Delta_MM7', None)
        delta_mm7 = round(float(delta_mm7_val), 1) if pd.notna(delta_mm7_val) else None
        delta_d1_val = lab.get('Delta_D1', None)
        delta_d1 = round(float(delta_d1_val), 1) if pd.notna(delta_d1_val) else None
        risco_diario = lab.get('Risco_Diario', 'N/A')
        if pd.isna(risco_diario):
            risco_diario = 'N/A'
     
        return {
            'total_coletas': int(total_coletas_2025),
            'media_3_meses': round(media_3_meses, 1),
            'media_diaria': round(media_diaria, 1),
            'vol_hoje': vol_hoje,
            'vol_d1': vol_d1,
            'delta_mm7': delta_mm7,
            'delta_d1': delta_d1,
            'agudo': agudo,
            'cronico': cronico,
            'dias_sem_coleta': int(dias_sem_coleta),
            'variacao_percentual': round(variacao, 1),
            'risco_diario': risco_diario
        }
    @staticmethod
    def calcular_metricas_evolucao(df: pd.DataFrame, lab_nome: str) -> dict:
        """Calcula métricas de evolução e comparativos para um laboratório específico - Atualizado organização e comparativo."""
        lab_data = df[df['Nome_Fantasia_PCL'] == lab_nome]
        if lab_data.empty:
            return {}
        lab = lab_data.iloc[0]
        # Total de coletas 2024 (todos os meses disponíveis)
        meses_2024 = ChartManager._meses_ate_hoje(df, 2024)
        colunas_2024 = [f'N_Coletas_{mes}_24' for mes in meses_2024]
        total_coletas_2024 = sum(lab.get(col, 0) for col in colunas_2024)
        # Total de coletas 2025 (até o mês atual)
        meses_2025 = ChartManager._meses_ate_hoje(df, 2025)
        colunas_2025 = [f'N_Coletas_{mes}_25' for mes in meses_2025]
        total_coletas_2025 = sum(lab.get(col, 0) for col in colunas_2025)
        # Média de 2024
        media_2024 = total_coletas_2024 / len(colunas_2024) if colunas_2024 else 0
        # Média de 2025
        media_2025 = total_coletas_2025 / len(colunas_2025) if colunas_2025 else 0
        # Último mês (mês mais recente disponível)
        ultimo_mes_2025 = meses_2025[-1] if meses_2025 else None
        coluna_ultimo_mes = f'N_Coletas_{ultimo_mes_2025}_25' if ultimo_mes_2025 else None
        media_ultimo_mes = lab.get(coluna_ultimo_mes, 0)
        # Máxima histórica 2024
        max_2024 = max(lab.get(col, 0) for col in colunas_2024)
        # Máxima histórica 2025
        max_2025 = max(lab.get(col, 0) for col in colunas_2025)
        return {
            'total_coletas_2024': int(total_coletas_2024),
            'total_coletas_2025': int(total_coletas_2025),
            'media_2024': round(media_2024, 1),
            'media_2025': round(media_2025, 1),
            'media_ultimo_mes': int(media_ultimo_mes),
            'max_2024': int(max_2024),
            'max_2025': int(max_2025)
        }
class AnaliseInteligente:
    """Classe para análises inteligentes e insights automáticos - Atualizado score."""
 
    @staticmethod
    def calcular_insights_automaticos(df: pd.DataFrame) -> pd.DataFrame:
        """Calcula insights automáticos para cada laboratório."""
        df_insights = df.copy()
     
        # Volume atual (último mês disponível dinâmico)
        meses_validos_2025 = ChartManager._meses_ate_hoje(df_insights, 2025)
        ultima_coluna_2025 = f"N_Coletas_{meses_validos_2025[-1]}_25" if meses_validos_2025 else None
        if ultima_coluna_2025 and ultima_coluna_2025 in df_insights.columns:
            df_insights['Volume_Atual_2025'] = df_insights[ultima_coluna_2025].fillna(0)
        else:
            df_insights['Volume_Atual_2025'] = 0
     
        # Volume máximo do ano passado
        colunas_2024 = [col for col in df_insights.columns if 'N_Coletas_' in col and '24' in col]
        if colunas_2024:
            df_insights['Volume_Maximo_2024'] = df_insights[colunas_2024].max(axis=1).fillna(0)
        else:
            df_insights['Volume_Maximo_2024'] = 0
     
        # Tendência de volume (comparação atual vs máximo histórico)
        df_insights['Tendencia_Volume'] = df_insights.apply(
            lambda row: 'Crescimento' if row['Volume_Atual_2025'] > row['Volume_Maximo_2024']
            else 'Declínio' if row['Volume_Atual_2025'] < row['Volume_Maximo_2024'] * 0.5
            else 'Estável', axis=1
        )
     
        # Insights automáticos
        df_insights['Insights_Automaticos'] = df_insights.apply(
            lambda row: AnaliseInteligente._gerar_insights(row), axis=1
        )
     
        return df_insights
 
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
        • Total de Coletas: {metrics.total_coletas:,}
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
            top_quedas = df.nsmallest(10, 'Variacao_Percentual')[['Nome_Fantasia_PCL', 'Variacao_Percentual', 'Estado']].copy()
            top_quedas['Ranking'] = range(1, len(top_quedas) + 1)
            top_quedas = top_quedas[['Ranking', 'Nome_Fantasia_PCL', 'Variacao_Percentual', 'Estado']]
            
            top_recuperacoes = df.nlargest(10, 'Variacao_Percentual')[['Nome_Fantasia_PCL', 'Variacao_Percentual', 'Estado']].copy()
            top_recuperacoes['Ranking'] = range(1, len(top_recuperacoes) + 1)
            top_recuperacoes = top_recuperacoes[['Ranking', 'Nome_Fantasia_PCL', 'Variacao_Percentual', 'Estado']]
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
                st.dataframe(
                    top_quedas,
                    use_container_width=True,
                    column_config={
                        "Ranking": st.column_config.NumberColumn("🏆", width="small", help="Posição no ranking"),
                        "Nome_Fantasia_PCL": st.column_config.TextColumn("Laboratório", help="Nome do laboratório"),
                        "Variacao_Percentual": st.column_config.NumberColumn("Variação %", format="%.2f%%", help="Variação percentual"),
                        "Estado": st.column_config.TextColumn("Estado", help="Estado do laboratório")
                    },
                    hide_index=True
                )
            with col2:
                st.subheader("📈 Top 10 Recuperações")
                st.dataframe(
                    top_recuperacoes,
                    use_container_width=True,
                    column_config={
                        "Ranking": st.column_config.NumberColumn("🏆", width="small", help="Posição no ranking"),
                        "Nome_Fantasia_PCL": st.column_config.TextColumn("Laboratório", help="Nome do laboratório"),
                        "Variacao_Percentual": st.column_config.NumberColumn("Variação %", format="%.2f%%", help="Variação percentual"),
                        "Estado": st.column_config.TextColumn("Estado", help="Estado do laboratório")
                    },
                    hide_index=True
                )
        # Download do relatório
        st.download_button(
            "📥 Download Relatório Mensal",
            sumario,
            file_name=f"relatorio_mensal_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            key="download_relatorio_mensal"
        )
def show_toast_once(message: str, key: str):
    """Mostra um toast apenas uma vez por sessão."""
    if key not in st.session_state:
        st.toast(message)
        st.session_state[key] = True

def main():
    """Função principal do dashboard v2.0 - Atualizado com tabs e navegação."""
    # ============================================
    # AUTENTICAÇÃO MICROSOFT
    # ============================================
    try:
        # Inicializar autenticador Microsoft
        auth = MicrosoftAuth()
        # Verificar autenticação
        if not create_login_page(auth):
            # Se não conseguiu fazer login, parar execução
            return
        # Criar cabeçalho com informações do usuário
        create_user_header()
    except Exception as e:
        st.error(f"❌ Erro no sistema de autenticação: {str(e)}")
        st.warning("Verifique as configurações de autenticação no arquivo secrets.toml")
        return
    # ============================================
    # DASHBOARD PRINCIPAL (APENAS PARA USUÁRIOS AUTENTICADOS)
    # ============================================
    # Renderizar header do dashboard
    UIManager.renderizar_header()
    # Carregar e preparar dados
    with st.spinner("🔄 Carregando dados..."):
        df_raw = DataManager.carregar_dados_churn()
        if df_raw is None:
            st.error("❌ Não foi possível carregar os dados. Execute o gerador de dados primeiro.")
            return
        df = DataManager.preparar_dados(df_raw)
        show_toast_once(f"✅ Dados carregados: {len(df):,} laboratórios", "dados_carregados")
    # Indicador de última atualização
    if not df.empty and 'Data_Analise' in df.columns:
        ultima_atualizacao = df['Data_Analise'].max()
        st.markdown(f"**Última Atualização:** {ultima_atualizacao.strftime('%d/%m/%Y %H:%M:%S')}")
    # ========================================
    # NAVEGAÇÃO (PRIMEIRO - NO TOPO DA SIDEBAR)
    # ========================================
    # Removido cabeçalho "Navegação" da sidebar; botões de páginas mantidos abaixo
   
    pages = ["🏠 Visão Geral", "📋 Análise Detalhada", "🏢 Ranking Rede", "🔧 Manutenção VIPs"]
   
    if "page" not in st.session_state:
        st.session_state.page = pages[0]
   
    for page in pages:
        if st.sidebar.button(page, key=page, use_container_width=True):
            st.session_state.page = page
   
    # Separador visual
    st.sidebar.markdown("---")
   
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
        st.toast("✅ Cache limpo! Os dados serão recarregados automaticamente.")
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
    # RENDERIZAÇÃO DA PÁGINA SELECIONADA - Atualizado com tabs
    # ========================================
    if st.session_state.page == "🏠 Visão Geral":
        st.header("🏠 Visão Geral")
        # KPIs principais com cards modernos
        UIManager.renderizar_kpi_cards(metrics)
        # Usar tabs para organização
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Resumo", "📈 Tendências", "📊 Distribuição", "🚨 Alto Risco", "🏆 Top 100 PCLs"])
        with tab1:
            st.subheader("📊 Resumo Geral")
            st.markdown("### 🚨 Alertas Prioritários")
            if df_filtrado.empty:
                st.info("📊 Nenhum dado disponível para avaliar alertas.")
            else:
                if 'Risco_Diario' in df_filtrado.columns:
                    criticos = df_filtrado[df_filtrado['Risco_Diario'] == '⚫ Crítico'].copy()
                    if not criticos.empty:
                        st.error(f"⚠️ {len(criticos)} laboratório(s) em risco **CRÍTICO** — intervenção imediata necessária.")
                        colunas_alerta = ['Nome_Fantasia_PCL', 'Estado', 'Vol_Hoje', 'Vol_D1', 'Delta_MM7', 'Dias_Sem_Coleta']
                        colunas_alerta = [c for c in colunas_alerta if c in criticos.columns]
                        if colunas_alerta:
                            st.dataframe(
                                criticos[colunas_alerta].sort_values('Vol_Hoje', ascending=True).head(10),
                                use_container_width=True,
                                column_config={
                                    "Nome_Fantasia_PCL": st.column_config.TextColumn("Laboratório"),
                                    "Estado": st.column_config.TextColumn("UF"),
                                    "Vol_Hoje": st.column_config.NumberColumn("Coletas (Hoje)"),
                                    "Vol_D1": st.column_config.NumberColumn("Coletas (D-1)"),
                                    "Delta_MM7": st.column_config.NumberColumn("Δ vs MM7", format="%.1f%%"),
                                    "Dias_Sem_Coleta": st.column_config.NumberColumn("Dias sem Coleta")
                                },
                                hide_index=True
                            )
                    else:
                        st.success("Nenhum laboratório classificado como ⚫ Crítico hoje.")
                else:
                    st.warning("⚠️ Coluna 'Risco_Diario' ausente — impossível gerar alertas prioritários.")

                if {'Delta_MM7', 'Risco_Diario'}.issubset(df_filtrado.columns):
                    quedas_relevantes = df_filtrado[
                        (df_filtrado['Delta_MM7'] <= -50) &
                        (df_filtrado['Risco_Diario'].isin(['🟠 Moderado', '🔴 Alto']))
                    ].copy()
                    if not quedas_relevantes.empty:
                        st.warning(
                            f"🔻 {len(quedas_relevantes)} laboratório(s) com queda ≥50% vs MM7 e risco elevado — priorize contato de recuperação."
                        )
                        colunas_queda = ['Nome_Fantasia_PCL', 'Estado', 'Vol_Hoje', 'Vol_D1', 'Delta_MM7', 'Risco_Diario', 'Recuperacao']
                        colunas_queda = [c for c in colunas_queda if c in quedas_relevantes.columns]
                        if colunas_queda:
                            st.dataframe(
                                quedas_relevantes[colunas_queda].sort_values(['Delta_MM7', 'Vol_Hoje']).head(15),
                                use_container_width=True,
                                column_config={
                                    "Nome_Fantasia_PCL": st.column_config.TextColumn("Laboratório"),
                                    "Estado": st.column_config.TextColumn("UF"),
                                    "Vol_Hoje": st.column_config.NumberColumn("Coletas (Hoje)"),
                                    "Vol_D1": st.column_config.NumberColumn("Coletas (D-1)"),
                                    "Delta_MM7": st.column_config.NumberColumn("Δ vs MM7", format="%.1f%%"),
                                    "Risco_Diario": st.column_config.TextColumn("Risco"),
                                    "Recuperacao": st.column_config.CheckboxColumn("Em Recuperação")
                                },
                                hide_index=True
                            )

                if {'Vol_Hoje', 'Vol_D1'}.issubset(df_filtrado.columns):
                    dois_dias_sem_coleta = df_filtrado[(df_filtrado['Vol_Hoje'] == 0) & (df_filtrado['Vol_D1'] == 0)].copy()
                    if not dois_dias_sem_coleta.empty:
                        st.error(
                            f"🛑 {len(dois_dias_sem_coleta)} laboratório(s) com **dois dias seguidos sem coleta** — alinhar com operações/logística."
                        )
                        colunas_zero = ['Nome_Fantasia_PCL', 'Estado', 'Risco_Diario', 'Vol_D1', 'Dias_Sem_Coleta']
                        colunas_zero = [c for c in colunas_zero if c in dois_dias_sem_coleta.columns]
                        if colunas_zero:
                            st.dataframe(
                                dois_dias_sem_coleta[colunas_zero].head(15),
                                use_container_width=True,
                                column_config={
                                    "Nome_Fantasia_PCL": st.column_config.TextColumn("Laboratório"),
                                    "Estado": st.column_config.TextColumn("UF"),
                                    "Risco_Diario": st.column_config.TextColumn("Risco"),
                                    "Vol_D1": st.column_config.NumberColumn("Coletas (D-1)"),
                                    "Dias_Sem_Coleta": st.column_config.NumberColumn("Dias sem Coleta")
                                },
                                hide_index=True
                            )

            st.markdown("---")
            with st.expander("ℹ️ Legenda das métricas diárias"):
                st.markdown("""
- **Vol_Hoje**: total de coletas registradas na data de referência (dia mais recente da série diária).
- **Vol_D1**: volume de coletas do dia imediatamente anterior ao atual.
- **MM7 / MM30 / MM90**: médias móveis de 7, 30 e 90 dias da série diária, incluindo dias sem coleta (zero).
- **Δ vs MM7 / MM30 / MM90**: variação percentual do volume de hoje em relação às respectivas médias móveis.
- **Δ vs D-1**: variação percentual do volume de hoje comparado ao dia anterior.
- **DOW_Media**: média de coletas para o mesmo dia da semana (ex.: todas as segundas) nos últimos 90 dias.
- **Risco_Diario**: classificação gerada pelo RiskEngine considerando os limiares de volume, médias e quedas consecutivas.
- **Recuperacao**: indica que o laboratório voltou a operar acima da MM7 após período de queda.
- **Sem Coleta (48h)**: quantidade de laboratórios com dois dias consecutivos sem registrar coletas (Vol_Hoje = 0 e Vol_D1 = 0).
                """)

            # Adicionar métricas adicionais aqui
        with tab2:
            st.subheader("📈 Tendências e Variações (Diário)")
            if df_filtrado.empty:
                st.info("📊 Nenhum dado disponível para esta análise.")
            else:
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### 📉 Maiores Quedas vs MM7")
                    if {'Delta_MM7', 'Vol_Hoje', 'MM7'}.issubset(df_filtrado.columns):
                        quedas_diarias = df_filtrado[df_filtrado['Delta_MM7'].notna()].copy()
                        if not quedas_diarias.empty:
                            quedas_diarias = quedas_diarias.sort_values('Delta_MM7').head(10)
                            colunas_quedas = [
                                'Nome_Fantasia_PCL', 'Estado', 'Vol_Hoje', 'Vol_D1', 'MM7',
                                'Delta_MM7', 'Delta_D1', 'Risco_Diario', 'Dias_Sem_Coleta'
                            ]
                            colunas_quedas = [c for c in colunas_quedas if c in quedas_diarias.columns]
                            st.dataframe(
                                quedas_diarias[colunas_quedas],
                                use_container_width=True,
                                column_config={
                                    "Nome_Fantasia_PCL": st.column_config.TextColumn("Laboratório"),
                                    "Estado": st.column_config.TextColumn("UF"),
                                    "Vol_Hoje": st.column_config.NumberColumn("Coletas (Hoje)"),
                                    "Vol_D1": st.column_config.NumberColumn("Coletas (D-1)"),
                                    "MM7": st.column_config.NumberColumn("MM7", format="%.1f"),
                                    "Delta_MM7": st.column_config.NumberColumn("Δ vs MM7", format="%.1f%%"),
                                    "Delta_D1": st.column_config.NumberColumn("Δ vs D-1", format="%.1f%%"),
                                    "Risco_Diario": st.column_config.TextColumn("Risco"),
                                    "Dias_Sem_Coleta": st.column_config.NumberColumn("Dias s/ Coleta")
                                },
                                hide_index=True
                            )
                        else:
                            st.success("Nenhuma queda relevante detectada hoje.")
                    else:
                        st.warning("⚠️ Colunas necessárias para a análise de quedas (Δ vs MM7) não encontradas.")

                with col2:
                    st.markdown("#### 📈 Altas vs MM7")
                    if {'Delta_MM7', 'Vol_Hoje', 'MM7'}.issubset(df_filtrado.columns):
                        altas_diarias = df_filtrado[df_filtrado['Delta_MM7'].notna()].copy()
                        altas_diarias = altas_diarias[altas_diarias['Delta_MM7'] > 0]
                        if not altas_diarias.empty:
                            altas_diarias = altas_diarias.sort_values('Delta_MM7', ascending=False).head(10)
                            colunas_altas = [
                                'Nome_Fantasia_PCL', 'Estado', 'Vol_Hoje', 'Vol_D1', 'MM7',
                                'Delta_MM7', 'Delta_D1', 'Risco_Diario', 'Recuperacao'
                            ]
                            colunas_altas = [c for c in colunas_altas if c in altas_diarias.columns]
                            st.dataframe(
                                altas_diarias[colunas_altas],
                                use_container_width=True,
                                column_config={
                                    "Nome_Fantasia_PCL": st.column_config.TextColumn("Laboratório"),
                                    "Estado": st.column_config.TextColumn("UF"),
                                    "Vol_Hoje": st.column_config.NumberColumn("Coletas (Hoje)"),
                                    "Vol_D1": st.column_config.NumberColumn("Coletas (D-1)"),
                                    "MM7": st.column_config.NumberColumn("MM7", format="%.1f"),
                                    "Delta_MM7": st.column_config.NumberColumn("Δ vs MM7", format="%.1f%%"),
                                    "Delta_D1": st.column_config.NumberColumn("Δ vs D-1", format="%.1f%%"),
                                    "Risco_Diario": st.column_config.TextColumn("Risco"),
                                    "Recuperacao": st.column_config.CheckboxColumn("Recuperação")
                                },
                                hide_index=True
                            )
                        else:
                            st.info("Nenhum crescimento significativo vs MM7 identificado hoje.")
                    else:
                        st.warning("⚠️ Colunas necessárias para a análise de altas (Δ vs MM7) não encontradas.")

                st.markdown("#### 🔁 Recuperações em Andamento")
                if 'Recuperacao' in df_filtrado.columns:
                    recuperacoes = df_filtrado[(df_filtrado['Recuperacao'] == True) & df_filtrado['Delta_MM7'].notna()].copy()
                    if not recuperacoes.empty:
                        recuperacoes = recuperacoes.sort_values('Delta_MM7', ascending=False)
                        colunas_recuperacao = [
                            'Nome_Fantasia_PCL', 'Estado', 'Vol_Hoje', 'Vol_D1', 'MM7',
                            'Delta_MM7', 'Delta_D1', 'Risco_Diario', 'Dias_Sem_Coleta'
                        ]
                        colunas_recuperacao = [c for c in colunas_recuperacao if c in recuperacoes.columns]
                        st.dataframe(
                            recuperacoes[colunas_recuperacao].head(10),
                            use_container_width=True,
                            column_config={
                                "Nome_Fantasia_PCL": st.column_config.TextColumn("Laboratório"),
                                "Estado": st.column_config.TextColumn("UF"),
                                "Vol_Hoje": st.column_config.NumberColumn("Coletas (Hoje)"),
                                "Vol_D1": st.column_config.NumberColumn("Coletas (D-1)"),
                                "MM7": st.column_config.NumberColumn("MM7", format="%.1f"),
                                "Delta_MM7": st.column_config.NumberColumn("Δ vs MM7", format="%.1f%%"),
                                "Delta_D1": st.column_config.NumberColumn("Δ vs D-1", format="%.1f%%"),
                                "Risco_Diario": st.column_config.TextColumn("Risco"),
                                "Dias_Sem_Coleta": st.column_config.NumberColumn("Dias s/ Coleta")
                            },
                            hide_index=True
                        )
                    else:
                        st.info("Nenhuma recuperação consistente detectada (labs com Δ vs MM7 positivo e flag de recuperação).")
                else:
                    st.warning("⚠️ Coluna 'Recuperacao' não encontrada nos dados.")
        with tab3:
            st.subheader("📊 Distribuição por Status")
            ChartManager.criar_grafico_distribuicao_risco(df_filtrado)
        with tab4:
            st.subheader("🚨 Labs em Risco")
            ChartManager.criar_grafico_top_labs(df_filtrado, top_n=10)
            if 'Risco_Diario' in df_filtrado.columns:
                labs_em_risco = df_filtrado[df_filtrado['Risco_Diario'].isin(['🟠 Moderado', '🔴 Alto', '⚫ Crítico'])]
            else:
                st.warning("⚠️ Coluna 'Risco_Diario' não encontrada nos dados.")
                labs_em_risco = pd.DataFrame()
            if not labs_em_risco.empty:
                colunas_resumo = ['Nome_Fantasia_PCL', 'Estado', 'Representante_Nome',
                                  'Vol_Hoje', 'Delta_MM7', 'Risco_Diario']
                st.dataframe(
                    labs_em_risco[colunas_resumo],
                    use_container_width=True,
                    height=300,
                    column_config={
                        "Nome_Fantasia_PCL": st.column_config.TextColumn("Laboratório"),
                        "Estado": st.column_config.TextColumn("UF"),
                        "Representante_Nome": st.column_config.TextColumn("Representante"),
                        "Vol_Hoje": st.column_config.NumberColumn("Coletas (Hoje)"),
                        "Delta_MM7": st.column_config.NumberColumn("Δ vs MM7", format="%.1f%%"),
                        "Risco_Diario": st.column_config.TextColumn("Risco Diário")
                    },
                    hide_index=True
                )
            else:
                st.success("✅ Nenhum laboratório em risco encontrado!")
        with tab5:
            st.subheader("🏆 Top 100 PCLs - Maiores Coletas")
            
            # Calcular total de coletas para cada laboratório
            if not df_filtrado.empty:
                # Calcular total de coletas 2025
                meses_2025 = ChartManager._meses_ate_hoje(df_filtrado, 2025)
                colunas_2025 = [f'N_Coletas_{mes}_25' for mes in meses_2025]
                colunas_existentes = [col for col in colunas_2025 if col in df_filtrado.columns]
                
                if colunas_existentes:
                    df_filtrado['Total_Coletas_2025_Calculado'] = df_filtrado[colunas_existentes].sum(axis=1)
                else:
                    df_filtrado['Total_Coletas_2025_Calculado'] = 0
                
                # Criar ranking dos top 100
                top_100 = df_filtrado.nlargest(100, 'Total_Coletas_2025_Calculado')
                
                # Preparar dados para exibição
                ranking_data = []
                for idx, (_, row) in enumerate(top_100.iterrows(), 1):
                    ranking_data.append({
                        'Ranking': idx,
                        'CNPJ': row.get('CNPJ_PCL', 'N/A'),
                        'Laboratório': row.get('Nome_Fantasia_PCL', 'N/A'),
                        'Coletas': int(row.get('Total_Coletas_2025_Calculado', 0)),
                        'Representante': row.get('Representante_Nome', 'N/A'),
                        'Estado': row.get('Estado', 'N/A'),
                        'Cidade': row.get('Cidade', 'N/A')
                    })
                
                df_ranking = pd.DataFrame(ranking_data)
                
                # Filtros de busca
                col1, col2 = st.columns([2, 1])
                with col1:
                    busca = st.text_input("🔍 Faça sua Pesquisa", placeholder="Digite CNPJ, nome do laboratório ou representante...")
                with col2:
                    estado_filtro = st.selectbox("📍 Estado", ["Todos"] + sorted(df_ranking['Estado'].unique().tolist()))
                
                # Aplicar filtros
                df_filtrado_ranking = df_ranking.copy()
                
                if busca:
                    mask = (
                        df_filtrado_ranking['CNPJ'].str.contains(busca, case=False, na=False) |
                        df_filtrado_ranking['Laboratório'].str.contains(busca, case=False, na=False) |
                        df_filtrado_ranking['Representante'].str.contains(busca, case=False, na=False)
                    )
                    df_filtrado_ranking = df_filtrado_ranking[mask]
                
                if estado_filtro != "Todos":
                    df_filtrado_ranking = df_filtrado_ranking[df_filtrado_ranking['Estado'] == estado_filtro]
                
                # Exibir tabela
                if not df_filtrado_ranking.empty:
                    # Estilizar a tabela
                    st.markdown("""
                    <style>
                    .ranking-table {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        border-collapse: collapse;
                        width: 100%;
                        margin-top: 1rem;
                    }
                    .ranking-table th {
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 12px 8px;
                        text-align: left;
                        font-weight: 600;
                        font-size: 0.9rem;
                    }
                    .ranking-table td {
                        padding: 10px 8px;
                        border-bottom: 1px solid #e9ecef;
                        font-size: 0.85rem;
                    }
                    .ranking-table tr:nth-child(even) {
                        background-color: #f8f9fa;
                    }
                    .ranking-table tr:hover {
                        background-color: #e3f2fd;
                        transition: background-color 0.2s;
                    }
                    .ranking-number {
                        font-weight: bold;
                        color: #667eea;
                        text-align: center;
                    }
                    .coletas-number {
                        font-weight: bold;
                        color: #28a745;
                        text-align: right;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Mostrar estatísticas
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("🏆 Total de Labs", f"{len(df_filtrado_ranking):,}")
                    with col2:
                        total_coletas = df_filtrado_ranking['Coletas'].sum()
                        st.metric("📊 Total de Coletas", f"{total_coletas:,}")
                    with col3:
                        media_coletas = df_filtrado_ranking['Coletas'].mean()
                        st.metric("📈 Média por Lab", f"{media_coletas:.0f}")
                    with col4:
                        top_coletas = df_filtrado_ranking['Coletas'].max() if not df_filtrado_ranking.empty else 0
                        st.metric("🥇 Maior Volume", f"{top_coletas:,}")
                    
                    # Exibir tabela com formatação
                    st.dataframe(
                        df_filtrado_ranking[['Ranking', 'CNPJ', 'Laboratório', 'Coletas', 'Representante', 'Estado', 'Cidade']],
                        use_container_width=True,
                        height=600,
                        column_config={
                            "Ranking": st.column_config.NumberColumn(
                                "Ranking",
                                help="Posição no ranking",
                                format="%d",
                                width="small"
                            ),
                            "CNPJ": st.column_config.TextColumn(
                                "CNPJ",
                                help="CNPJ do laboratório",
                                width="medium"
                            ),
                            "Laboratório": st.column_config.TextColumn(
                                "Laboratório",
                                help="Nome fantasia do laboratório",
                                width="large"
                            ),
                            "Coletas": st.column_config.NumberColumn(
                                "Coletas",
                                help="Total de coletas em 2025",
                                format="%d",
                                width="small"
                            ),
                            "Representante": st.column_config.TextColumn(
                                "Representante",
                                help="Nome do representante",
                                width="medium"
                            ),
                            "Estado": st.column_config.TextColumn(
                                "Estado",
                                help="Estado do laboratório",
                                width="small"
                            ),
                            "Cidade": st.column_config.TextColumn(
                                "Cidade",
                                help="Cidade do laboratório",
                                width="medium"
                            )
                        },
                        hide_index=True
                    )
                    
                    # Botões de download
                    col_download1, col_download2 = st.columns(2)
                    
                    with col_download1:
                        csv_data = df_filtrado_ranking.to_csv(index=False, encoding='utf-8')
                        st.download_button(
                            "📥 Download CSV",
                            csv_data,
                            file_name=f"ranking_top_100_pcls_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    with col_download2:
                        # Preparar dados para Excel
                        excel_buffer = BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                            # Adicionar metadados na primeira aba
                            metadata_df = pd.DataFrame({
                                'Métrica': ['Total de Laboratórios', 'Total de Coletas', 'Média por Laboratório', 'Maior Volume', 'Data de Geração'],
                                'Valor': [
                                    f"{len(df_filtrado_ranking):,}",
                                    f"{df_filtrado_ranking['Coletas'].sum():,}",
                                    f"{df_filtrado_ranking['Coletas'].mean():.0f}",
                                    f"{df_filtrado_ranking['Coletas'].max():,}",
                                    datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                                ]
                            })
                            metadata_df.to_excel(writer, sheet_name='Resumo', index=False)
                            
                            # Adicionar ranking na segunda aba
                            df_filtrado_ranking.to_excel(writer, sheet_name='Ranking Top 100', index=False)
                            
                            # Formatação da planilha
                            workbook = writer.book
                            
                            # Formatar aba de resumo
                            summary_sheet = writer.sheets['Resumo']
                            summary_sheet.column_dimensions['A'].width = 25
                            summary_sheet.column_dimensions['B'].width = 20
                            
                            # Formatar aba de ranking
                            ranking_sheet = writer.sheets['Ranking Top 100']
                            ranking_sheet.column_dimensions['A'].width = 8   # Ranking
                            ranking_sheet.column_dimensions['B'].width = 18  # CNPJ
                            ranking_sheet.column_dimensions['C'].width = 40  # Laboratório
                            ranking_sheet.column_dimensions['D'].width = 12  # Coletas
                            ranking_sheet.column_dimensions['E'].width = 25  # Representante
                            ranking_sheet.column_dimensions['F'].width = 8   # Estado
                            ranking_sheet.column_dimensions['G'].width = 20  # Cidade
                            
                            # Aplicar formatação condicional para destacar top 10
                            from openpyxl.styles import PatternFill, Font
                            yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
                            bold_font = Font(bold=True)
                            
                            for row in range(2, min(12, len(df_filtrado_ranking) + 2)):  # Top 10
                                for col in range(1, 8):
                                    cell = ranking_sheet.cell(row=row, column=col)
                                    cell.fill = yellow_fill
                                    cell.font = bold_font
                        
                        excel_data = excel_buffer.getvalue()
                        st.download_button(
                            "📊 Download Excel",
                            excel_data,
                            file_name=f"ranking_top_100_pcls_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                else:
                    st.info("🔍 Nenhum resultado encontrado para os filtros aplicados.")
            else:
                st.warning("⚠️ Nenhum dado disponível para gerar o ranking.")
    elif st.session_state.page == "📋 Análise Detalhada":
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
                    st.write("") # Espaço vazio para alinhar com o campo de texto
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
                # Informações de ajuda - Atualizado espaçamento dica busca
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
                        if len(cnpj_limpo) >= 8: # CNPJ válido tem pelo menos 8 dígitos
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
                                st.toast(f"✅ Laboratório encontrado: {lab_final}")
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
                        st.markdown("---") # Separador antes dos dados
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
                            representante = lab_info.get('Representante_Nome', 'N/A')
                            # Limpar dados vazios
                            telefone = telefone if telefone and telefone != 'N/A' else 'N/A'
                            email = email if email and email != 'N/A' else 'N/A'
                            contato = contato if contato else 'N/A'
                            representante = representante if representante and representante != 'N/A' else 'N/A'
                         
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
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666; margin-bottom: 0.3rem;">Representante</div>
                                        <div style="font-size: 1rem; font-weight: bold; color: #495057;">{representante}</div>
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
                                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; text-align: center;">
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
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666;">Coletas (Hoje)</div>
                                        <div style="font-size: 1.3rem; font-weight: bold; color: #28a745;">{metricas['vol_hoje']:,}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            # Status e Risco
                            status_color = "#28a745" if metricas['agudo'] == "Ativo" else "#dc3545"
                            risco_color = "#28a745" if metricas['dias_sem_coleta'] <= 7 else "#ffc107" if metricas['dias_sem_coleta'] <= 30 else "#dc3545"
                            risco_diario = metricas.get('risco_diario', 'N/A')
                            cores_risco = {
                                '🟢 Normal': '#16A34A',
                                '🟡 Atenção': '#F59E0B',
                                '🟠 Moderado': '#FB923C',
                                '🔴 Alto': '#DC2626',
                                '⚫ Crítico': '#111827'
                            }
                            risco_diario_color = cores_risco.get(risco_diario, "#6c757d")
                            delta_mm7 = metricas.get('delta_mm7')
                            if isinstance(delta_mm7, (int, float)):
                                delta_mm7_color = "#28a745" if delta_mm7 >= 0 else "#dc3545"
                                delta_mm7_display = f"{delta_mm7:.1f}%"
                            else:
                                delta_mm7_color = "#6c757d"
                                delta_mm7_display = "--"
                         
                            st.markdown(f"""
                            <div style="background: #f8f9fa; border-radius: 6px; padding: 1rem; margin-bottom: 1rem; border-left: 4px solid {risco_color};">
                                <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem; font-weight: 600;">STATUS & RISCO</div>
                                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; text-align: center;">
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666;">Status Atual</div>
                                        <div style="font-size: 1.1rem; font-weight: bold; color: {status_color};">{metricas['agudo']}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666;">Dias sem Coleta</div>
                                        <div style="font-size: 1.1rem; font-weight: bold; color: {risco_color};">{metricas['dias_sem_coleta']}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666;">Risco Diário</div>
                                        <div style="font-size: 1.1rem; font-weight: bold; color: {risco_diario_color};">{risco_diario}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666;">Δ vs MM7</div>
                                        <div style="font-size: 1.1rem; font-weight: bold; color: {delta_mm7_color};">{delta_mm7_display}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            # Histórico de Performance - Reorganizado conforme solicitação
                            # Calcular máxima de coletas histórica (respeitando meses disponíveis)
                            metricas_evolucao = MetricasAvancadas.calcular_metricas_evolucao(df_filtrado, lab_final)
                            st.markdown(f"""
                            <div style="background: #f8f9fa; border-radius: 6px; padding: 1rem; margin-bottom: 1rem; border-left: 4px solid #17a2b8;">
                                <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem; font-weight: 600;">HISTÓRICO DE PERFORMANCE</div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; text-align: center;">
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666;">Média 2024</div>
                                        <div style="font-size: 1.3rem; font-weight: bold; color: #17a2b8;">{metricas_evolucao['media_2024']:.1f}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666;">Média 2025</div>
                                        <div style="font-size: 1.3rem; font-weight: bold; color: #17a2b8;">{metricas_evolucao['media_2025']:.1f}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666;">Máxima 2024</div>
                                        <div style="font-size: 1.3rem; font-weight: bold; color: #17a2b8;">{metricas_evolucao['max_2024']:,}</div>
                                    </div>
                                    <div>
                                        <div style="font-size: 0.8rem; color: #666;">Máxima 2025</div>
                                        <div style="font-size: 1.3rem; font-weight: bold; color: #17a2b8;">{metricas_evolucao['max_2025']:,}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                        # Seção de Gráficos com Abas - Refatorado conforme solicitação
                        st.markdown("""
                        <div style="background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem;
                                    border: 1px solid #e9ecef; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h3 style="margin: 0 0 1rem 0; color: #2c3e50; font-weight: 600; border-bottom: 2px solid #007bff; padding-bottom: 0.5rem;">
                                📊 Análise Visual Detalhada
                            </h3>
                        """, unsafe_allow_html=True)
                        
                        # Criar abas para organizar os gráficos
                        tab_resumo, tab_distribuicao, tab_media_diaria, tab_coletas_dia = st.tabs([
                            "📋 Resumo Executivo", "📊 Distribuição por Dia", "📅 Média Diária", "📈 Coletas por Dia"
                        ])
                        
                        with tab_resumo:
                            st.subheader("📋 Resumo Executivo")
                            # Calcular métricas de evolução
                            metricas_evolucao = MetricasAvancadas.calcular_metricas_evolucao(df_filtrado, lab_final)
                            if metricas_evolucao:
                                # Primeiro bloco: Totais de Coletas
                                st.markdown(f"""
                                <div style="background: #f8f9fa; border-radius: 6px; padding: 1rem; margin-bottom: 1rem; border-left: 4px solid #28a745;">
                                    <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem; font-weight: 600;">TOTAIS DE COLETAS</div>
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; text-align: center;">
                                        <div>
                                            <div style="font-size: 0.8rem; color: #666;">Total 2024</div>
                                            <div style="font-size: 1.4rem; font-weight: bold; color: #28a745;">{metricas_evolucao['total_coletas_2024']:,}</div>
                                        </div>
                                        <div>
                                            <div style="font-size: 0.8rem; color: #666;">Total 2025</div>
                                            <div style="font-size: 1.4rem; font-weight: bold; color: #007bff;">{metricas_evolucao['total_coletas_2025']:,}</div>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Comparativos - Último mês vs Média 2025 e vs Máxima de 2025
                                variacao_ultimo_vs_media = ((metricas_evolucao['media_ultimo_mes'] - metricas_evolucao['media_2025']) / metricas_evolucao['media_2025'] * 100) if metricas_evolucao['media_2025'] > 0 else 0
                                percentual_maxima = (metricas_evolucao['media_ultimo_mes'] / metricas_evolucao['max_2025'] * 100) if metricas_evolucao['max_2025'] > 0 else 0
                                cor_variacao = "#28a745" if variacao_ultimo_vs_media >= 0 else "#dc3545"
                                cor_percentual = "#28a745" if percentual_maxima >= 80 else "#ffc107" if percentual_maxima >= 50 else "#dc3545"
                                st.markdown(f"""
                                <div style="background: #f8f9fa; border-radius: 6px; padding: 1rem; margin-bottom: 1rem; border-left: 4px solid #6f42c1;">
                                    <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem; font-weight: 600;">COMPARATIVOS</div>
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; text-align: center;">
                                        <div>
                                            <div style="font-size: 0.8rem; color: #666;">Último Mês vs Média 2025</div>
                                            <div style="font-size: 1.2rem; font-weight: bold; color: {cor_variacao};">
                                                {'+' if variacao_ultimo_vs_media >= 0 else ''}{variacao_ultimo_vs_media:.1f}%
                                            </div>
                                            <div style="font-size: 0.7rem; color: #666;">{metricas_evolucao['media_ultimo_mes']:,} vs {metricas_evolucao['media_2025']:.1f}</div>
                                        </div>
                                        <div>
                                            <div style="font-size: 0.8rem; color: #666;">Último Mês vs Máxima 2025</div>
                                            <div style="font-size: 1.2rem; font-weight: bold; color: {cor_percentual};">
                                                {percentual_maxima:.1f}%
                                            </div>
                                            <div style="font-size: 0.7rem; color: #666;">{metricas_evolucao['media_ultimo_mes']:,} vs {metricas_evolucao['max_2025']:,}</div>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Gráfico de Evolução Mensal integrado no Resumo Executivo
                                st.markdown("---")
                                st.subheader("📈 Evolução Mensal")
                                ChartManager.criar_grafico_evolucao_mensal(df_filtrado, lab_final, "resumo")
                            else:
                                st.info("📊 Dados insuficientes para análise de evolução")
                        
                        with tab_distribuicao:
                            st.subheader("📊 Distribuição de Coletas por Dia da Semana")
                            # Gráfico com destaque maior conforme solicitado
                            ChartManager.criar_grafico_media_dia_semana_novo(df_filtrado, lab_final, filtros)
                        
                        with tab_media_diaria:
                            st.subheader("📊 Média Diária por Mês")
                            ChartManager.criar_grafico_media_diaria(df_filtrado, lab_final)

                        with tab_coletas_dia:
                            st.subheader("📈 Coletas por Dia do Mês")
                            ChartManager.criar_grafico_coletas_por_dia(df_filtrado, lab_final)
                # Fechar container
                st.markdown('</div>', unsafe_allow_html=True)

        # Seção organizada com tabs para melhor visualização
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

        # Conteúdo único da análise detalhada
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
            # Verificar quais colunas VIP estão disponíveis
            colunas_vip_disponiveis = ['CNPJ_Normalizado']
            colunas_vip_opcionais = ['Rede', 'Ranking', 'Ranking Rede']
            for col in colunas_vip_opcionais:
                if col in df_vip_tabela.columns:
                    colunas_vip_disponiveis.append(col)
            # Fazer merge apenas com colunas disponíveis
            if len(colunas_vip_disponiveis) > 1: # Mais que apenas CNPJ_Normalizado
                df_tabela = df_tabela.merge(
                    df_vip_tabela[colunas_vip_disponiveis],
                    on='CNPJ_Normalizado',
                    how='left'
                )
                mostrar_rede = 'Rede' in colunas_vip_disponiveis
            else:
                # Se não há colunas VIP disponíveis, não fazer merge
                mostrar_rede = False
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
                    st.toast("✅ Filtro de rede limpo! Todas as redes serão exibidas.")
            else:
                # Seleção manual de rede
                rede_filtro = st.selectbox(
                    "🏢 Filtrar por Rede:",
                    options=redes_disponiveis,
                    index=0, # Sempre "Todas" por padrão
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
                'labs_risco_alto': (
                    df_tabela_filtrada['Risco_Diario'].isin(['🔴 Alto', '⚫ Crítico']).sum()
                    if 'Risco_Diario' in df_tabela_filtrada.columns else 0
                ),
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
            'CNPJ_PCL', 'Nome_Fantasia_PCL', 'Estado', 'Cidade', 'Representante_Nome',
            'Risco_Diario', 'Dias_Sem_Coleta', 'Variacao_Percentual',
            'Volume_Atual_2025', 'Volume_Maximo_2024', 'Tendencia_Volume',
            'Vol_Hoje', 'Vol_D1', 'MM7', 'MM30', 'MM90',
            'Delta_D1', 'Delta_MM7', 'Delta_MM30', 'Delta_MM90'
        ]

        # Adicionar colunas de coletas mensais (2024 e 2025)
        meses_nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        # Mapeamento dos códigos dos meses para nomes completos em português
        meses_nomes_completos = {
            "Jan": "Janeiro", "Fev": "Fevereiro", "Mar": "Março", "Abr": "Abril",
            "Mai": "Maio", "Jun": "Junho", "Jul": "Julho", "Ago": "Agosto",
            "Set": "Setembro", "Out": "Outubro", "Nov": "Novembro", "Dez": "Dezembro"
        }
        mes_limite_2025 = min(datetime.now().month, 12)
        
        # Colunas de 2024 (todos os meses)
        cols_2024 = [f'N_Coletas_{m}_24' for m in meses_nomes]
        # Colunas de 2025 (até o mês atual)
        cols_2025 = [f'N_Coletas_{m}_25' for m in meses_nomes[:mes_limite_2025]]

        colunas_principais.extend(cols_2024 + cols_2025)

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
            # Criar configuração de colunas de forma mais explícita
            column_config = {
                "CNPJ_PCL": st.column_config.TextColumn(
                    "📄 CNPJ",
                    help="CNPJ do laboratório"
                ),
                "Nome_Fantasia_PCL": st.column_config.TextColumn(
                    "🏥 Nome Fantasia",
                    help="Nome fantasia do laboratório"
                ),
                "Estado": st.column_config.TextColumn(
                    "🗺️ Estado",
                    help="Estado do laboratório"
                ),
                "Cidade": st.column_config.TextColumn(
                    "🏙️ Cidade",
                    help="Cidade do laboratório"
                ),
                "Representante_Nome": st.column_config.TextColumn(
                    "👤 Representante",
                    help="Nome do representante responsável"
                ),
                "Risco_Diario": st.column_config.TextColumn(
                    "Risco Diário",
                    help="Classificação de risco diária pela nova régua"
                ),
                "Dias_Sem_Coleta": st.column_config.NumberColumn(
                    "Dias Sem Coleta",
                    help="Número de dias sem coleta"
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
                )
            }

            column_config.update({
                "Vol_Hoje": st.column_config.NumberColumn("Coletas (Hoje)"),
                "Vol_D1": st.column_config.NumberColumn("D-1"),
                "MM7": st.column_config.NumberColumn("MM7"),
                "MM30": st.column_config.NumberColumn("MM30"),
                "MM90": st.column_config.NumberColumn("MM90"),
                "Delta_D1": st.column_config.NumberColumn("Δ vs D-1", format="%.1f%%"),
                "Delta_MM7": st.column_config.NumberColumn("Δ vs MM7", format="%.1f%%"),
                "Delta_MM30": st.column_config.NumberColumn("Δ vs MM30", format="%.1f%%"),
                "Delta_MM90": st.column_config.NumberColumn("Δ vs MM90", format="%.1f%%")
            })
            
            # Adicionar configurações para colunas mensais de 2024
            for col in cols_2024:
                if col in df_exibicao.columns:
                    mes_codigo = col.split('_')[2]  # Corrigido: pegar o terceiro elemento (índice 2)
                    mes_nome = meses_nomes_completos.get(mes_codigo, mes_codigo)
                    # Usar configuração mais simples
                    column_config[col] = st.column_config.NumberColumn(
                        f"{mes_nome}/24",
                        help=f"Número de coletas em {mes_nome} de 2024"
                    )
            
            # Adicionar configurações para colunas mensais de 2025
            for col in cols_2025:
                if col in df_exibicao.columns:
                    mes_codigo = col.split('_')[2]  # Corrigido: pegar o terceiro elemento (índice 2)
                    mes_nome = meses_nomes_completos.get(mes_codigo, mes_codigo)
                    # Usar configuração mais simples
                    column_config[col] = st.column_config.NumberColumn(
                        f"{mes_nome}/25",
                        help=f"Número de coletas em {mes_nome} de 2025"
                    )
            
            # Adicionar colunas de rede se disponível
            if 'Rede' in df_exibicao.columns:
                column_config["Rede"] = st.column_config.TextColumn(
                    "🏢 Rede",
                    help="Rede à qual o laboratório pertence"
                )
            if 'Ranking' in df_exibicao.columns:
                column_config["Ranking"] = st.column_config.TextColumn(
                    "🏆 Ranking",
                    help="Ranking individual do laboratório"
                )
            if 'Ranking_Rede' in df_exibicao.columns:
                column_config["Ranking_Rede"] = st.column_config.TextColumn(
                    "🏅 Ranking Rede",
                    help="Ranking da rede do laboratório"
                )
            
            # Renomear as colunas diretamente no dataframe para exibir nomes completos dos meses
            df_exibicao_renamed = df_exibicao.copy()
            rename_dict = {}
            
            # Renomear colunas principais para nomes mais legíveis
            rename_dict.update({
                "CNPJ_PCL": "CNPJ",
                "Nome_Fantasia_PCL": "Nome Fantasia",
                "Representante_Nome": "Representante",
                "Risco_Diario": "Risco Diário",
                "Dias_Sem_Coleta": "Dias Sem Coleta",
                "Variacao_Percentual": "Variação %",
                "Volume_Atual_2025": "Volume Atual 2025",
                "Volume_Maximo_2024": "Volume Máximo 2024",
                "Tendencia_Volume": "Tendência",
                "Vol_Hoje": "Coletas (Hoje)",
                "Vol_D1": "D-1",
                "MM7": "MM7",
                "MM30": "MM30",
                "MM90": "MM90",
                "Delta_D1": "Δ vs D-1",
                "Delta_MM7": "Δ vs MM7",
                "Delta_MM30": "Δ vs MM30",
                "Delta_MM90": "Δ vs MM90",
                "Ranking_Rede": "Ranking Rede"
            })
            
            # Renomear colunas de 2024
            for col in cols_2024:
                if col in df_exibicao_renamed.columns:
                    mes_codigo = col.split('_')[2]  # Corrigido: pegar o terceiro elemento (índice 2)
                    mes_nome = meses_nomes_completos.get(mes_codigo, mes_codigo)
                    rename_dict[col] = f"{mes_nome}/24"
            
            # Renomear colunas de 2025
            for col in cols_2025:
                if col in df_exibicao_renamed.columns:
                    mes_codigo = col.split('_')[2]  # Corrigido: pegar o terceiro elemento (índice 2)
                    mes_nome = meses_nomes_completos.get(mes_codigo, mes_codigo)
                    rename_dict[col] = f"{mes_nome}/25"
            
            df_exibicao_renamed = df_exibicao_renamed.rename(columns=rename_dict)
            
            # Mostrar tabela com contador
            st.markdown(f"**Mostrando {len(df_exibicao_renamed)} laboratórios**")
            st.dataframe(
                df_exibicao_renamed,
                use_container_width=True,
                height=500,
                hide_index=True
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

        # Fechar container principal
        st.markdown("</div>", unsafe_allow_html=True)
    elif st.session_state.page == "🏢 Ranking Rede":
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
                        margin: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="margin: 0;">🔍 Filtros Gerais de Redes</h4>
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
                # Categorias de redes (ouro, prata, bronze, diamante)
                categorias_rede = []
                if 'Ranking Rede' in df_com_rede.columns:
                    df_cats = df_com_rede.copy()
                    df_cats['Categoria_Rede'] = df_cats['Ranking Rede'].apply(
                        lambda x: 'Diamante' if str(x).upper() in ['DIAMANTE', 'DIAMOND'] else
                                 'Ouro' if str(x).upper() in ['OURO', 'GOLD', 'ORO'] else
                                 'Prata' if str(x).upper() in ['PRATA', 'SILVER', 'PLATA'] else
                                 'Bronze' if str(x).upper() in ['BRONZE', 'BRONCE'] else
                                 'Outros'
                    )
                    categorias_rede = sorted(df_cats['Categoria_Rede'].unique())
                categoria_selecionada = st.multiselect(
                    "🏆 Categoria Rede:",
                    options=categorias_rede,
                    default=categorias_rede if len(categorias_rede) <= 4 else [],
                    help="Filtrar por categoria da rede (Diamante, Ouro, Prata, Bronze)"
                )
            # Quarta coluna para tipo de análise
            col4 = st.columns(1)[0]
            with col4:
                tipo_analise = st.selectbox(
                    "📊 Tipo de Análise:",
                    options=["Visão Geral", "Por Volume", "Por Performance", "Por Risco", "🔄 Comparação de Redes"],
                    help="Escolha o tipo de análise a ser realizada"
                )
            # Aplicar filtros
            df_rede_filtrado = df_com_rede.copy()
            # Nota explicativa sobre filtros
            st.info("💡 **Dica:** Use os filtros acima para análise geral. Para exploração detalhada de uma rede específica, role para baixo até a seção 'Explorador Detalhado por Rede'.")
            if rede_selecionada:
                df_rede_filtrado = df_rede_filtrado[df_rede_filtrado['Rede'].isin(rede_selecionada)]
            if ranking_rede_selecionado:
                df_rede_filtrado = df_rede_filtrado[df_rede_filtrado['Ranking Rede'].isin(ranking_rede_selecionado)]
            # Aplicar filtro de categoria de rede
            if categoria_selecionada:
                df_cats_filtro = df_rede_filtrado.copy()
                df_cats_filtro['Categoria_Rede'] = df_cats_filtro['Ranking Rede'].apply(
                    lambda x: 'Diamante' if str(x).upper() in ['DIAMANTE', 'DIAMOND'] else
                             'Ouro' if str(x).upper() in ['OURO', 'GOLD', 'ORO'] else
                             'Prata' if str(x).upper() in ['PRATA', 'SILVER', 'PLATA'] else
                             'Bronze' if str(x).upper() in ['BRONZE', 'BRONCE'] else
                             'Outros'
                )
                df_rede_filtrado = df_cats_filtro[df_cats_filtro['Categoria_Rede'].isin(categoria_selecionada)]
            # ========================================
            # CÁLCULO GLOBAL DE ESTATÍSTICAS DE REDES
            # ========================================
            # Calcular rede_stats para uso em todas as análises
            rede_stats = pd.DataFrame() # Inicializar vazio por segurança
            if not df_rede_filtrado.empty and 'Rede' in df_rede_filtrado.columns:
                # Remover duplicatas baseado no CNPJ antes da contagem
                df_sem_duplicatas_rede = df_rede_filtrado.drop_duplicates(subset=['CNPJ_PCL'], keep='first')
                # Estatísticas expandidas por rede
                rede_stats = df_sem_duplicatas_rede.groupby('Rede').agg(
                    Qtd_Labs=('Nome_Fantasia_PCL', 'count'),
                    Volume_Total=('Volume_Total_2025', 'sum'),
                    Volume_Medio=('Volume_Total_2025', 'mean'),
                    Volume_Std=('Volume_Total_2025', 'std'),
                    Estado_Principal=('Estado', lambda x: x.mode().iloc[0] if not x.mode().empty else 'N/A'),
                    Cidades_Unicas=('Cidade', 'nunique'),
                    Labs_Churn=('Risco_Diario', lambda x: x.isin(['🟠 Moderado', '🔴 Alto', '⚫ Crítico']).sum())
                ).reset_index()
                # Adicionar mais métricas calculadas
                rede_stats['Taxa_Churn'] = (rede_stats['Labs_Churn'] / rede_stats['Qtd_Labs'] * 100).round(1)
                rede_stats['Volume_por_Lab'] = (rede_stats['Volume_Total'] / rede_stats['Qtd_Labs']).round(0)
                # Adicionar categoria da rede se disponível
                if 'Ranking Rede' in df_sem_duplicatas_rede.columns:
                    rede_ranking = df_sem_duplicatas_rede.groupby('Rede')['Ranking Rede'].first().reset_index()
                    rede_stats = rede_stats.merge(rede_ranking, on='Rede', how='left')
                    # Adicionar categoria
                    rede_stats['Categoria_Rede'] = rede_stats['Ranking Rede'].apply(
                        lambda x: 'Diamante' if str(x).upper() in ['DIAMANTE', 'DIAMOND'] else
                                 'Ouro' if str(x).upper() in ['OURO', 'GOLD', 'ORO'] else
                                 'Prata' if str(x).upper() in ['PRATA', 'SILVER', 'PLATA'] else
                                 'Bronze' if str(x).upper() in ['BRONZE', 'BRONCE'] else
                                 'Outros'
                    )
                else:
                    rede_stats['Ranking Rede'] = 'N/A'
                    rede_stats['Categoria_Rede'] = 'N/A'
            if not df_rede_filtrado.empty:
                # Análise baseada no tipo selecionado
                if tipo_analise == "Visão Geral":
                    # Cards de métricas gerais
                    col1, col2, col3, col4 = st.columns(4)
                    total_redes = len(rede_stats) if not rede_stats.empty else 0
                    total_labs_rede = rede_stats['Qtd_Labs'].sum() if not rede_stats.empty else 0
                    volume_total_rede = rede_stats['Volume_Total'].sum() if not rede_stats.empty else 0
                    with col1:
                        st.metric("🏢 Total de Redes", total_redes)
                    with col2:
                        st.metric("🏥 Labs nas Redes", f"{total_labs_rede:,}")
                    with col3:
                        st.metric("📦 Volume Total", f"{volume_total_rede:,}")
                    with col4:
                        media_por_rede = volume_total_rede / total_redes if total_redes > 0 else 0
                        st.metric("📊 Média por Rede", f"{media_por_rede:,.0f}")
                    # ========================================
                    # CARDS DE LOCALIDADE E VOLUMES
                    # ========================================
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
                                color: white; padding: 1rem; border-radius: 8px;
                                margin: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h4 style="margin: 0;">📍 Distribuição por Localidade</h4>
                    </div>
                    """, unsafe_allow_html=True)
                    # Cards de localidade
                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                    # Calcular métricas por estado
                    df_sem_duplicatas_local = df_rede_filtrado.drop_duplicates(subset=['CNPJ_PCL'], keep='first')
                    # Número total de laboratórios
                    total_labs = len(df_sem_duplicatas_local)
                    # Por estado
                    estados_stats = df_sem_duplicatas_local.groupby('Estado').agg({
                        'Nome_Fantasia_PCL': 'count',
                        'Volume_Total_2025': ['sum', 'mean']
                    }).round(2)
                    # Achatar colunas multi-índice
                    estados_stats.columns = ['Qtd_Labs', 'Volume_Total', 'Volume_Medio']
                    estados_stats = estados_stats.reset_index()
                    # Top 5 estados por quantidade
                    top_estados = estados_stats.nlargest(5, 'Qtd_Labs')
                    # Por cidade
                    cidades_stats = df_sem_duplicatas_local.groupby('Cidade').agg({
                        'Nome_Fantasia_PCL': 'count',
                        'Volume_Total_2025': ['sum', 'mean']
                    }).round(2)
                    cidades_stats.columns = ['Qtd_Labs', 'Volume_Total', 'Volume_Medio']
                    cidades_stats = cidades_stats.reset_index()
                    # Top 5 cidades por quantidade
                    top_cidades = cidades_stats.nlargest(5, 'Qtd_Labs')
                    with col1:
                        st.metric("🏥 Total Labs", f"{total_labs:,}")
                    with col2:
                        total_estados = df_sem_duplicatas_local['Estado'].nunique()
                        st.metric("🗺️ Estados", f"{total_estados}")
                    with col3:
                        total_cidades = df_sem_duplicatas_local['Cidade'].nunique()
                        st.metric("🏙️ Cidades", f"{total_cidades}")
                    with col4:
                        volume_total_3m = df_sem_duplicatas_local['Volume_Total_2025'].sum()
                        st.metric("📦 Vol. Total 2025", f"{volume_total_3m:,.0f}")
                    with col5:
                        volume_medio_3m = df_sem_duplicatas_local['Volume_Total_2025'].mean()
                        st.metric("📊 Vol. Médio 2025", f"{volume_medio_3m:,.0f}")
                    with col6:
                        volume_medio_por_lab = volume_total_3m / total_labs if total_labs > 0 else 0
                        st.metric("📈 Vol/Lab", f"{volume_medio_por_lab:,.0f}")
                    # Tabelas detalhadas por localidade
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("📍 Top Estados")
                        # Adicionar ranking para top_estados
                        top_estados_display = top_estados.copy()
                        top_estados_display['Ranking'] = range(1, len(top_estados_display) + 1)
                        top_estados_display = top_estados_display[['Ranking', 'Estado', 'Qtd_Labs', 'Volume_Total', 'Volume_Medio']]
                        st.dataframe(
                            top_estados_display,
                            use_container_width=True,
                            column_config={
                                "Ranking": st.column_config.NumberColumn("🏆", width="small", help="Posição no ranking"),
                                "Estado": st.column_config.TextColumn("🏛️ Estado"),
                                "Qtd_Labs": st.column_config.NumberColumn("🏥 Labs"),
                                "Volume_Total": st.column_config.NumberColumn("📦 Vol. Total", format="%.0f"),
                                "Volume_Medio": st.column_config.NumberColumn("📊 Vol. Médio", format="%.0f")
                            },
                            hide_index=True
                        )
                    with col2:
                        st.subheader("🏙️ Top Cidades")
                        # Adicionar ranking para top_cidades
                        top_cidades_display = top_cidades.copy()
                        top_cidades_display['Ranking'] = range(1, len(top_cidades_display) + 1)
                        top_cidades_display = top_cidades_display[['Ranking', 'Cidade', 'Qtd_Labs', 'Volume_Total', 'Volume_Medio']]
                        st.dataframe(
                            top_cidades_display,
                            use_container_width=True,
                            column_config={
                                "Ranking": st.column_config.NumberColumn("🏆", width="small", help="Posição no ranking"),
                                "Cidade": st.column_config.TextColumn("🏙️ Cidade"),
                                "Qtd_Labs": st.column_config.NumberColumn("🏥 Labs"),
                                "Volume_Total": st.column_config.NumberColumn("📦 Vol. Total", format="%.0f"),
                                "Volume_Medio": st.column_config.NumberColumn("📊 Vol. Médio", format="%.0f")
                            },
                            hide_index=True
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
                    fig_ranking.update_layout(xaxis_tickangle=-45, height=500, margin=dict(l=40, r=40, t=40, b=40))
                    st.plotly_chart(fig_ranking, use_container_width=True)
                    # Tabela detalhada
                    # Adicionar ranking para volume_por_rede
                    volume_por_rede_display = volume_por_rede.round(2).copy()
                    volume_por_rede_display['Ranking'] = range(1, len(volume_por_rede_display) + 1)
                    volume_por_rede_display = volume_por_rede_display[['Ranking', 'Rede', 'Volume_Total', 'Volume_Medio', 'Qtd_Labs']]
                    st.dataframe(
                        volume_por_rede_display,
                        use_container_width=True,
                        column_config={
                            "Ranking": st.column_config.NumberColumn("🏆", width="small", help="Posição no ranking"),
                            "Rede": st.column_config.TextColumn("🏢 Rede"),
                            "Volume_Total": st.column_config.NumberColumn("📦 Volume Total", format="%.0f"),
                            "Volume_Medio": st.column_config.NumberColumn("📊 Volume Médio", format="%.1f"),
                            "Qtd_Labs": st.column_config.NumberColumn("🏥 Qtd Labs")
                        },
                        hide_index=True
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
                            fig_perf.update_layout(xaxis_tickangle=-45, height=500, margin=dict(l=40, r=40, t=40, b=40))
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
                            fig_scatter.update_layout(height=500, margin=dict(l=40, r=40, t=40, b=40))
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
                            },
                            hide_index=True
                        )
                elif tipo_analise == "Por Risco":
                    st.subheader("⚠️ Análise de Risco por Rede")
                    if 'Risco_Diario' not in df_rede_filtrado.columns:
                        st.warning("⚠️ Coluna 'Risco_Diario' não encontrada nos dados.")
                    else:
                        df_risco = df_rede_filtrado.drop_duplicates(subset=['CNPJ_PCL'], keep='first')
                        labs_risco = df_risco[df_risco['Risco_Diario'].isin(['🟠 Moderado', '🔴 Alto', '⚫ Crítico'])]
                        cores_map = {
                            '🟢 Normal': '#16A34A',
                            '🟡 Atenção': '#F59E0B',
                            '🟠 Moderado': '#FB923C',
                            '🔴 Alto': '#DC2626',
                            '⚫ Crítico': '#111827'
                        }
                        if labs_risco.empty:
                            st.success("✅ Nenhuma rede com laboratórios em risco elevado.")
                        else:
                            resumo_rede = labs_risco.groupby('Rede').agg(
                                Labs_Risco=('CNPJ_PCL', 'count'),
                                Vol_Hoje_Medio=('Vol_Hoje', 'mean'),
                                Delta_MM7_Medio=('Delta_MM7', 'mean'),
                                Recuperando=('Recuperacao', lambda x: x.sum())
                            ).reset_index()
                            resumo_rede['Delta_MM7_Medio'] = resumo_rede['Delta_MM7_Medio'].round(1)
                            resumo_rede['Vol_Hoje_Medio'] = resumo_rede['Vol_Hoje_Medio'].round(1)
                            resumo_rede = resumo_rede.sort_values(['Labs_Risco', 'Delta_MM7_Medio'], ascending=[False, True])
                            col1, col2 = st.columns(2)
                            with col1:
                                fig_top = px.bar(
                                    resumo_rede.head(10),
                                    x='Labs_Risco',
                                    y='Rede',
                                    orientation='h',
                                    title="🚨 Redes com Mais Labs em Risco",
                                    color='Delta_MM7_Medio',
                                    color_continuous_scale='Reds',
                                    text='Labs_Risco'
                                )
                                fig_top.update_traces(texttemplate='%{text}', textposition='outside')
                                fig_top.update_layout(xaxis_title="Laboratórios em risco", yaxis_title="Rede",
                                                      height=500, margin=dict(l=40, r=40, t=40, b=40))
                                st.plotly_chart(fig_top, use_container_width=True)
                            with col2:
                                resumo_rede_delta = resumo_rede.sort_values('Delta_MM7_Medio')
                                fig_delta = px.bar(
                                    resumo_rede_delta.head(10),
                                    x='Delta_MM7_Medio',
                                    y='Rede',
                                    orientation='h',
                                    title="📉 Redes com Maior Queda vs MM7",
                                    color='Labs_Risco',
                                    color_continuous_scale='Reds',
                                    text='Delta_MM7_Medio'
                                )
                                fig_delta.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                                fig_delta.update_layout(xaxis_title="Δ vs MM7 (%)", yaxis_title="Rede",
                                                        height=500, margin=dict(l=40, r=40, t=40, b=40))
                                st.plotly_chart(fig_delta, use_container_width=True)
                            st.dataframe(
                                resumo_rede,
                                use_container_width=True,
                                column_config={
                                    "Rede": st.column_config.TextColumn("🏢 Rede"),
                                    "Labs_Risco": st.column_config.NumberColumn("🚨 Labs em Risco"),
                                    "Vol_Hoje_Medio": st.column_config.NumberColumn("📦 Vol. Médio (Hoje)", format="%.1f"),
                                    "Delta_MM7_Medio": st.column_config.NumberColumn("Δ Médio vs MM7", format="%.1f%%"),
                                    "Recuperando": st.column_config.NumberColumn("🔁 Em Recuperação")
                                },
                                hide_index=True
                            )
                        risco_status = df_risco.groupby(['Rede', 'Risco_Diario']).size().reset_index(name='Qtd')
                        fig_status = px.bar(
                            risco_status,
                            x='Rede',
                            y='Qtd',
                            color='Risco_Diario',
                            title="📊 Distribuição de Risco Diário por Rede",
                            color_discrete_map=cores_map,
                            barmode='stack'
                        )
                        fig_status.update_layout(xaxis_tickangle=-45, height=500, margin=dict(l=40, r=40, t=40, b=40))
                        st.plotly_chart(fig_status, use_container_width=True)
                        # Destaques de risco crítico
                        redes_criticas = labs_risco[labs_risco['Risco_Diario'] == '⚫ Crítico']['Rede'].value_counts()
                        if not redes_criticas.empty:
                            st.error("🚨 Redes com laboratórios em risco crítico detectadas!")
                            for rede, qtd in redes_criticas.items():
                                st.write(f"• **{rede}**: {qtd} laboratório(s) crítico(s)")
                elif tipo_analise == "🔄 Comparação de Redes":
                    st.subheader("🔄 Comparação Direta de Redes")
                    # Seletor de redes para comparação (máximo 5 para legibilidade)
                    redes_para_comparar = st.multiselect(
                        "🏢 Selecione até 5 redes para comparar:",
                        options=sorted(rede_stats['Rede'].unique()),
                        default=sorted(rede_stats['Rede'].unique())[:3] if len(rede_stats) >= 3 else sorted(rede_stats['Rede'].unique()),
                        max_selections=5,
                        help="Escolha as redes que deseja comparar diretamente"
                    )
                    if redes_para_comparar:
                        # Filtrar dados apenas das redes selecionadas
                        redes_comparacao = rede_stats[rede_stats['Rede'].isin(redes_para_comparar)].copy()
                        if not redes_comparacao.empty:
                            # ========================================
                            # DASHBOARD DE COMPARAÇÃO
                            # ========================================
                            # Cards de comparação rápida
                            st.markdown("### 📊 Comparação Rápida")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                maior_qtd = redes_comparacao.loc[redes_comparacao['Qtd_Labs'].idxmax()]
                                st.metric(
                                    "🏥 Maior Qtd Labs",
                                    f"{int(maior_qtd['Qtd_Labs'])}",
                                    f"{maior_qtd['Rede'][:15]}..."
                                )
                            with col2:
                                maior_volume = redes_comparacao.loc[redes_comparacao['Volume_Total'].idxmax()]
                                st.metric(
                                    "📦 Maior Volume",
                                    f"{maior_volume['Volume_Total']:,.0f}",
                                    f"{maior_volume['Rede'][:15]}..."
                                )
                            with col3:
                                menor_churn = redes_comparacao.loc[redes_comparacao['Taxa_Churn'].idxmin()]
                                st.metric(
                                    "✅ Menor Churn",
                                    f"{menor_churn['Taxa_Churn']:.1f}%",
                                    f"{menor_churn['Rede'][:15]}..."
                                )
                            with col4:
                                maior_risco = redes_comparacao.loc[redes_comparacao['Labs_Churn'].idxmax()]
                                st.metric(
                                    "⚠️ Mais Labs em Risco",
                                    f"{int(maior_risco['Labs_Churn'])}",
                                    f"{maior_risco['Rede'][:15]}..."
                                )
                            # ========================================
                            # GRÁFICOS COMPARATIVOS
                            # ========================================
                            st.markdown("### 📈 Comparações Visuais")
                            # Gráfico de barras comparativo - múltiplas métricas
                            col1, col2 = st.columns(2)
                            with col1:
                                # Comparação por quantidade de laboratórios e volume
                                fig_comp1 = go.Figure()
                                for _, rede in redes_comparacao.iterrows():
                                    fig_comp1.add_trace(go.Bar(
                                        name=f"{rede['Rede'][:12]}...",
                                        x=['Labs', 'Volume (k)'],
                                        y=[rede['Qtd_Labs'], rede['Volume_Total']/1000],
                                        text=[f"{int(rede['Qtd_Labs'])}", f"{rede['Volume_Total']/1000:.0f}k"],
                                        textposition='auto',
                                    ))
                                fig_comp1.update_layout(
                                    title="🏥 Labs vs 📦 Volume por Rede",
                                    barmode='group',
                                    height=400
                                )
                                st.plotly_chart(fig_comp1, use_container_width=True)
                            with col2:
                                # Comparação de performance (volume médio e taxa churn)
                                fig_comp2 = go.Figure()
                                for _, rede in redes_comparacao.iterrows():
                                    fig_comp2.add_trace(go.Scatter(
                                        name=f"{rede['Rede'][:12]}...",
                                        x=[rede['Volume_Medio']],
                                        y=[rede['Taxa_Churn']],
                                        mode='markers+text',
                                        text=f"{rede['Rede'][:8]}...",
                                        textposition="top center",
                                        marker=dict(size=15)
                                    ))
                                fig_comp2.update_layout(
                                    title="💰 Volume Médio vs 📉 Taxa Churn",
                                    xaxis_title="Volume Médio por Lab",
                                    yaxis_title="Taxa Churn (%)",
                                    height=400
                                )
                                st.plotly_chart(fig_comp2, use_container_width=True)
                            # ========================================
                            # TABELA COMPARATIVA DETALHADA
                            # ========================================
                            st.markdown("### 📋 Comparação Detalhada")
                            # Reordenar colunas para melhor visualização
                            cols_comparacao = [
                                'Rede', 'Categoria_Rede', 'Qtd_Labs', 'Labs_Churn', 'Taxa_Churn',
                                'Volume_Total', 'Volume_Medio', 'Volume_por_Lab'
                            ]
                            # Adicionar indicadores visuais de risco
                            redes_comparacao_display = redes_comparacao[cols_comparacao].copy()
                            # Função para adicionar indicadores de risco
                            def adicionar_indicador_risco(row):
                                indicadores = []
                                # Indicador de alto churn
                                if row['Taxa_Churn'] > 30:
                                    indicadores.append("🔴")
                                elif row['Taxa_Churn'] > 15:
                                    indicadores.append("🟠")
                                else:
                                    indicadores.append("🟢")
                                # Indicador de concentração de labs em risco
                                proporcao_risco = (row['Labs_Churn'] / row['Qtd_Labs']) if row['Qtd_Labs'] else 0
                                if proporcao_risco >= 0.5:
                                    indicadores.append("⚠️")
                                elif proporcao_risco >= 0.3:
                                    indicadores.append("⚡")
                                # Indicador de baixa eficiência (volume por lab)
                                media_geral = redes_comparacao['Volume_por_Lab'].mean()
                                if row['Volume_por_Lab'] < media_geral * 0.7:
                                    indicadores.append("📉")
                                return ' '.join(indicadores) if indicadores else "✅"
                            redes_comparacao_display['🚨 Indicadores'] = redes_comparacao_display.apply(adicionar_indicador_risco, axis=1)
                            # Reordenar para colocar indicadores primeiro
                            cols_final = ['🚨 Indicadores'] + cols_comparacao
                            redes_comparacao_display = redes_comparacao_display[cols_final]
                            st.dataframe(
                                redes_comparacao_display.round(2),
                                use_container_width=True,
                                column_config={
                                    "🚨 Indicadores": st.column_config.TextColumn("🚨 Alertas", width="small"),
                                    "Rede": st.column_config.TextColumn("🏢 Rede", width="medium"),
                                    "Categoria_Rede": st.column_config.TextColumn("🏆 Categoria", width="small"),
                                    "Qtd_Labs": st.column_config.NumberColumn("🏥 Labs", format="%d"),
                                    "Labs_Churn": st.column_config.NumberColumn("❌ Churn", format="%d"),
                                    "Taxa_Churn": st.column_config.NumberColumn("📉 % Churn", format="%.1f%%"),
                                    "Volume_Total": st.column_config.NumberColumn("📦 Vol. Total", format="%.0f"),
                                    "Volume_Medio": st.column_config.NumberColumn("📊 Vol. Médio", format="%.0f"),
                                    "Volume_por_Lab": st.column_config.NumberColumn("💰 Vol/Lab", format="%.0f")
                                },
                                hide_index=True
                            )
                            # ========================================
                            # RANKING COMPARATIVO
                            # ========================================
                            st.markdown("### 🏆 Rankings Comparativos")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.subheader("🥇 Por Volume Total")
                                ranking_volume = redes_comparacao.sort_values('Volume_Total', ascending=False)[['Rede', 'Volume_Total']]
                                for idx, row in ranking_volume.iterrows():
                                    medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "📊"
                                    st.write(f"{medal} {row['Rede'][:20]}...: {row['Volume_Total']:,.0f}")
                            with col2:
                                st.subheader("🥇 Por Eficiência")
                                ranking_eficiencia = redes_comparacao.sort_values('Volume_por_Lab', ascending=False)[['Rede', 'Volume_por_Lab']]
                                for idx, row in ranking_eficiencia.iterrows():
                                    medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "📊"
                                    st.write(f"{medal} {row['Rede'][:20]}...: {row['Volume_por_Lab']:,.0f}")
                            with col3:
                                st.subheader("🥇 Por Menor Risco")
                                ranking_risco = redes_comparacao.sort_values('Taxa_Churn', ascending=True)[['Rede', 'Taxa_Churn']]
                                for idx, row in ranking_risco.iterrows():
                                    medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "📊"
                                    st.write(f"{medal} {row['Rede'][:20]}...: {row['Taxa_Churn']:.1f}%")
                        else:
                            st.warning("⚠️ Nenhuma rede encontrada com os critérios selecionados.")
                    else:
                        st.info("ℹ️ Selecione pelo menos uma rede para iniciar a comparação.")
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
                            "Ranking_Rede": st.column_config.TextColumn("🏅 Ranking Rede"),
                            "Qtd_Labs": st.column_config.NumberColumn("🏥 Qtd Labs"),
                            "Volume_Total": st.column_config.NumberColumn("📦 Volume Total", format="%.0f")
                        },
                        hide_index=True
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
                            fig_sunburst.update_layout(height=500, margin=dict(l=40, r=40, t=40, b=40))
                            st.plotly_chart(fig_sunburst, use_container_width=True)
                        else:
                            st.info("ℹ️ Não há dados suficientes com volume positivo para gerar o gráfico hierárquico.")
            else:
                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
        else:
            st.warning("⚠️ Dados VIP não disponíveis. Verifique se o arquivo Excel foi carregado corretamente.")
    elif st.session_state.page == "🔧 Manutenção VIPs":
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
                        },
                        hide_index=True
                    )
                else:
                    st.warning("Nenhuma coluna válida encontrada para exibição")
            else:
                st.warning("⚠️ Nenhum dado VIP encontrado. Execute primeiro o script de normalização.")
     
        with sub_tab2:
            st.subheader("➕ Adicionar Novo Laboratório VIP")
         
            # Formulário para adicionar adicionar VIP
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
                        erros.append("Razão Social é obrigatório")
                 
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
                                    st.toast(f"✅ Backup criado: {backup_path}")
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
                                'REP': '', # Será preenchido automaticamente se CNPJ existir
                                'CS': '', # Será preenchido automaticamente se CNPJ existir
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
                         
                            st.toast(f"✅ Laboratório VIP adicionado com sucesso!")
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
                                    disabled=True, # CNPJ não pode ser alterado
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
                                                st.toast(f"✅ Backup criado: {backup_path}")
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
                                     
                                        st.toast(f"✅ Laboratório VIP atualizado com sucesso!")
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
         
            if stats.get('total_alteracoes', 0) > 0:
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
                 
                    for i, alt in enumerate(historico_filtrado[:20]): # Mostrar apenas os 20 mais recentes
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
                                st.toast(f"✅ Histórico exportado: {caminho_export}")
                        except Exception as e:
                            st.error(f"❌ Erro ao exportar histórico: {e}")
                else:
                    st.info("ℹ️ Nenhum registro encontrado com os filtros aplicados")
            else:
                st.info("ℹ️ Nenhuma alteração registrada ainda")
    # ========================================
    # RODAPÉ
    # ========================================
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <p>📊 <strong>Syntox Churn</strong> - Dashboard profissional de análise de retenção de laboratórios</p>
        <p>Desenvolvido com ❤️ para otimizar a gestão de relacionamento com PCLs</p>
    </div>
    """, unsafe_allow_html=True)
if __name__ == "__main__":
    main()