import os
import logging
import pymongo
import pytz
import schedule
import time
from bson import ObjectId
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
from typing import Dict, List, Optional, Tuple, Any
try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover
    tomllib = None

try:
    from churn_sp_connector import ChurnSPConnector
except Exception:
    ChurnSPConnector = None

# Importar configurações
from config_churn import *

# Configurações de log
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Importar novos módulos do sistema v2
try:
    from feriados_brasil import is_dia_util, dias_uteis_entre, obter_dias_uteis_no_periodo
    from porte_laboratorio import (
        aplicar_porte_dataframe, 
        aplicar_gatilho_dataframe,
        calcular_porte,
        avaliar_risco_por_dias_sem_coleta,
        classificar_perda_por_dias_sem_coleta
    )
    from alertas_manager import (
        aplicar_cap_alertas,
        processar_alertas_por_uf,
        gerar_relatorio_alertas,
        formatar_relatorio_texto
    )
    MODULOS_V2_DISPONIVEIS = True
except ImportError as e:
    logger.warning(f"Módulos v2 não disponíveis: {e}. Sistema funcionará em modo legado.")
    MODULOS_V2_DISPONIVEIS = False

# Fuso horário
timezone_br = pytz.timezone(TIMEZONE)

def to_local(dt: datetime) -> Optional[datetime]:
    """Converte dt para fuso de São Paulo."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(timezone_br)

def format_datetime_br(dt: datetime) -> Optional[str]:
    """Formata data no estilo brasileiro DD/MM/AAAA HH:MM:SS."""
    if dt is None:
        return None
    return dt.strftime(DATETIME_FORMAT)


def calcular_dias_sem_coleta_uteis(data_ultima: Optional[pd.Timestamp],
                                   estado: Optional[str],
                                   hoje: Optional[datetime] = None) -> int:
    """Calcula dias úteis entre a última coleta e hoje (excluindo o dia da coleta)."""
    if data_ultima is None or pd.isna(data_ultima):
        return 0
    if hoje is None:
        hoje = datetime.now(timezone_br)
    if data_ultima.tzinfo is None:
        data_ultima = pytz.utc.localize(data_ultima)
    data_local = data_ultima.astimezone(timezone_br).date()
    fim = hoje.date()
    if fim <= data_local:
        return 0
    start = data_local + timedelta(days=1)
    try:
        return max(dias_uteis_entre(start, fim, estado), 0)
    except Exception:
        return 0


def gerar_resumo_semanal_mes(base_df: pd.DataFrame,
                             df_gatherings_2025: pd.DataFrame) -> Tuple[pd.Series, dict]:
    """
    Gera resumo semanal (por laboratório) do mês corrente e metadados globais.

    Returns:
        (Series com JSON por laboratório, dict de metadados)
    """
    if base_df is None or base_df.empty:
        return pd.Series(dtype=object), {}

    base_index = base_df.index
    vazio_series = pd.Series(['[]'] * len(base_index), index=base_index, dtype=object)
    hoje = datetime.now(timezone_br)
    ano_ref = hoje.year
    mes_ref = hoje.month

    meta = {
        "referencia": {"ano": ano_ref, "mes": mes_ref},
        "semanas_fechadas": 0,
        "total_semanas": 0,
        "weeks": []
    }

    if df_gatherings_2025 is None or df_gatherings_2025.empty:
        return vazio_series, meta

    df_mes = df_gatherings_2025.copy()
    df_mes['createdAt'] = pd.to_datetime(df_mes.get('createdAt'), errors='coerce', utc=True)
    df_mes = df_mes.dropna(subset=['createdAt'])
    if df_mes.empty:
        return vazio_series, meta

    df_mes['createdAt'] = df_mes['createdAt'].dt.tz_convert(timezone_br)
    df_mes = df_mes[
        (df_mes['createdAt'].dt.year == ano_ref) &
        (df_mes['createdAt'].dt.month == mes_ref)
    ].copy()
    if df_mes.empty:
        return vazio_series, meta

    df_mes['weekday'] = df_mes['createdAt'].dt.weekday
    df_mes = df_mes[df_mes['weekday'] < 5].copy()
    if df_mes.empty:
        return vazio_series, meta

    iso = df_mes['createdAt'].dt.isocalendar()
    df_mes['iso_week'] = iso.week.astype(int)
    df_mes['iso_year'] = iso.year.astype(int)
    df_mes['semana_inicio'] = (df_mes['createdAt'] - pd.to_timedelta(df_mes['weekday'], unit='D')).dt.date

    week_meta_map = {}
    unique_weeks = (
        df_mes[['iso_year', 'iso_week', 'semana_inicio']]
        .drop_duplicates()
        .sort_values(['iso_year', 'iso_week'])
        .reset_index(drop=True)
    )
    for idx, row in unique_weeks.iterrows():
        iso_year = int(row['iso_year'])
        iso_week = int(row['iso_week'])
        semana_no_mes = idx + 1
        semana_inicio = row['semana_inicio']
        semana_fim_util = semana_inicio + timedelta(days=4)
        try:
            semana_fim_util = datetime.fromisocalendar(iso_year, iso_week, 5).date()
        except ValueError:
            semana_fim_util = semana_inicio + timedelta(days=4)
        fechada = hoje.date() > semana_fim_util
        week_meta_map[(iso_year, iso_week)] = {
            "semana_no_mes": semana_no_mes,
            "fechada": fechada,
            "week_end": semana_fim_util
        }

    if not week_meta_map:
        return vazio_series, meta

    meta['total_semanas'] = len(week_meta_map)
    meta['semanas_fechadas'] = len([1 for info in week_meta_map.values() if info['fechada']])

    df_mes['semana_no_mes'] = df_mes.apply(
        lambda r: week_meta_map.get((int(r['iso_year']), int(r['iso_week'])), {}).get('semana_no_mes'),
        axis=1
    )
    df_mes = df_mes.dropna(subset=['semana_no_mes'])
    if df_mes.empty:
        return vazio_series, meta

    volumes = (
        df_mes.groupby(['_laboratory', 'iso_year', 'iso_week', 'semana_no_mes'])
        .size()
        .reset_index(name='volume')
    )

    if volumes.empty:
        return vazio_series, meta

    # Metadados globais por semana
    weeks_meta_list = []
    prev_total = None
    for _, row in volumes.groupby(['iso_year', 'iso_week', 'semana_no_mes'])['volume'].sum().reset_index().sort_values('semana_no_mes').iterrows():
        iso_year = int(row['iso_year'])
        iso_week = int(row['iso_week'])
        semana_no_mes = int(row['semana_no_mes'])
        total_volume = int(row['volume'])
        weeks_meta_list.append({
            "semana": semana_no_mes,
            "iso_week": iso_week,
            "iso_year": iso_year,
            "volume_total": total_volume,
            "volume_semana_anterior": prev_total,
            "fechada": week_meta_map[(iso_year, iso_week)]['fechada']
        })
        prev_total = total_volume
    meta['weeks'] = weeks_meta_list

    # JSON por laboratório
    lab_json_map: Dict[str, str] = {}
    for lab_id, grupo in volumes.groupby('_laboratory'):
        grupo = grupo.sort_values('semana_no_mes')
        registros = []
        prev_volume_lab = None
        for _, row in grupo.iterrows():
            iso_year = int(row['iso_year'])
            iso_week = int(row['iso_week'])
            key = (iso_year, iso_week)
            info_semana = week_meta_map.get(key, {})
            registros.append({
                "semana": int(row['semana_no_mes']),
                "iso_week": iso_week,
                "iso_year": iso_year,
                "volume_util": int(row['volume']),
                "volume_semana_anterior": prev_volume_lab,
                "fechada": info_semana.get('fechada', False)
            })
            prev_volume_lab = int(row['volume'])
        lab_json_map[lab_id] = json.dumps(registros, ensure_ascii=False)

    series_result = base_index.to_series().apply(lambda idx: lab_json_map.get(str(idx), '[]'))
    series_result.index = base_index
    return series_result, meta

def connect_mongodb():
    """Conecta ao MongoDB com tratamento de erro."""
    try:
        client = pymongo.MongoClient(MONGODB_URI, datetime_conversion='DATETIME_AUTO')
        db = client[MONGODB_DATABASE]
        logger.info("Conexão MongoDB OK.")
        return db
    except Exception as e:
        logger.error(f"Erro MongoDB: {e}")
        return None

def get_collections(db) -> Dict[str, Any]:
    """Retorna dicionário de coleções."""
    return {
        "gatherings": db["gatherings"],
        "laboratories": db["laboratories"],
        "representatives": db["representatives"],
        "chainofcustodies": db["chainofcustodies"],
        "prices": db["prices"]
    }

def atualizar_csv_incremental(arquivo_path: str, novos_dados_df: pd.DataFrame, chave_id: str = '_id') -> None:
    """
    Atualiza CSV com merge incremental:
    - Ler CSV existente (se houver)
    - Merge: atualizar registros existentes + adicionar novos
    - Salvar CSV atualizado
    """
    try:
        # Verificar se arquivo existe
        if os.path.exists(arquivo_path):
            # Ler dados existentes
            df_existente = pd.read_csv(arquivo_path, encoding=ENCODING, low_memory=False)
            logger.info(f"Arquivo existente carregado: {len(df_existente)} registros")
            
            # Converter chave_id para string em ambos DataFrames
            df_existente[chave_id] = df_existente[chave_id].astype(str)
            novos_dados_df[chave_id] = novos_dados_df[chave_id].astype(str)
            
            # Merge: atualizar existentes e adicionar novos
            df_final = pd.concat([df_existente, novos_dados_df], ignore_index=True)
            df_final = df_final.drop_duplicates(subset=[chave_id], keep='last')
            
            logger.info(f"Merge concluído: {len(df_final)} registros (existente: {len(df_existente)}, novos: {len(novos_dados_df)})")
        else:
            # Primeira execução - usar apenas novos dados
            df_final = novos_dados_df
            logger.info(f"Primeira execução: {len(df_final)} registros")
        
        # Salvar CSV atualizado
        df_final.to_csv(arquivo_path, index=False, encoding=ENCODING)
        logger.info(f"CSV atualizado: {arquivo_path}")
        
    except Exception as e:
        logger.error(f"Erro ao atualizar CSV {arquivo_path}: {e}")
        # Em caso de erro, salvar apenas os novos dados
        novos_dados_df.to_csv(arquivo_path, index=False, encoding=ENCODING)
        logger.warning(f"Salvando apenas novos dados devido ao erro")

def extrair_gatherings_2024():
    """Extrai gatherings de 2024 apenas se arquivo não existir."""
    arquivo_path = os.path.join(OUTPUT_DIR, GATHERINGS_2024_FILE)
    
    if os.path.exists(arquivo_path):
        logger.info(f"Arquivo {GATHERINGS_2024_FILE} já existe. Pulando extração de 2024.")
        return
    
    logger.info("Iniciando extração de gatherings 2024...")
    
    db = connect_mongodb()
    if db is None:
        return
    
    collections = get_collections(db)
    
    # Definir período 2024
    inicio_2024 = datetime(2024, 1, 1)
    fim_2024 = datetime(2024, 12, 31, 23, 59, 59)
    
    # Buscar gatherings de 2024
    gatherings_2024 = list(collections["gatherings"].find({
        "createdAt": {"$gte": inicio_2024, "$lte": fim_2024},
        "active": True
    }))
    
    logger.info(f"Encontrados {len(gatherings_2024)} gatherings de 2024")
    
    if gatherings_2024:
        # Converter para DataFrame
        df_gatherings = pd.DataFrame(gatherings_2024)
        
        # Salvar CSV
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        df_gatherings.to_csv(arquivo_path, index=False, encoding=ENCODING)
        logger.info(f"Gatherings 2024 salvos: {arquivo_path}")
    else:
        logger.warning("Nenhum gathering encontrado para 2024")

def extrair_gatherings_2025():
    """Extrai gatherings de 2025 com merge incremental."""
    logger.info("Iniciando extração de gatherings 2025...")
    
    db = connect_mongodb()
    if db is None:
        return
    
    collections = get_collections(db)
    
    # Definir período 2025 (desde 1º de janeiro)
    inicio_2025 = datetime(2025, 1, 1)
    
    # Buscar gatherings de 2025
    gatherings_2025 = list(collections["gatherings"].find({
        "createdAt": {"$gte": inicio_2025},
        "active": True
    }))
    
    logger.info(f"Encontrados {len(gatherings_2025)} gatherings de 2025")
    
    if gatherings_2025:
        # Converter para DataFrame
        df_gatherings = pd.DataFrame(gatherings_2025)
        
        # Atualizar CSV com merge incremental
        arquivo_path = os.path.join(OUTPUT_DIR, GATHERINGS_2025_FILE)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        atualizar_csv_incremental(arquivo_path, df_gatherings, '_id')
    else:
        logger.warning("Nenhum gathering encontrado para 2025")

def extrair_laboratories():
    """Extrai laboratories com merge incremental (sem filtro de active)."""
    logger.info("Iniciando extração de laboratories...")
    
    db = connect_mongodb()
    if db is None:
        return
    
    collections = get_collections(db)
    
    # Buscar todos laboratories (sem filtro)
    laboratories = list(collections["laboratories"].find({}))
    
    logger.info(f"Encontrados {len(laboratories)} laboratories")
    
    if laboratories:
        # Converter para DataFrame
        df_laboratories = pd.DataFrame(laboratories)
        
        # Atualizar CSV com merge incremental
        arquivo_path = os.path.join(OUTPUT_DIR, LABORATORIES_FILE)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        atualizar_csv_incremental(arquivo_path, df_laboratories, '_id')
    else:
        logger.warning("Nenhum laboratory encontrado")

def extrair_representatives():
    """Extrai representatives com merge incremental."""
    logger.info("Iniciando extração de representatives...")
    
    db = connect_mongodb()
    if db is None:
        return
    
    collections = get_collections(db)
    
    # Buscar todos representatives
    representatives = list(collections["representatives"].find({}))
    
    logger.info(f"Encontrados {len(representatives)} representatives")
    
    if representatives:
        # Converter para DataFrame
        df_representatives = pd.DataFrame(representatives)
        
        # Atualizar CSV com merge incremental
        arquivo_path = os.path.join(OUTPUT_DIR, REPRESENTATIVES_FILE)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        atualizar_csv_incremental(arquivo_path, df_representatives, '_id')
    else:
        logger.warning("Nenhum representative encontrado")


def extrair_chainofcustodies():
    """Extrai chain of custodies com merge incremental."""
    logger.info("Iniciando extração de chain of custodies...")

    db = connect_mongodb()
    if db is None:
        return

    collections = get_collections(db)

    cursor = collections["chainofcustodies"].find({}, {
        "_id": 1,
        "createdAt": 1,
        "updatedAt": 1,
        "analysisStatus": 1
    })

    def _extract_recollection_status(analysis: Any) -> bool:
        if isinstance(analysis, dict):
            recol = analysis.get('recollection', {})
            if isinstance(recol, dict):
                status = recol.get('status')
                if isinstance(status, bool):
                    return status
                if isinstance(status, (int, float)):
                    return bool(status)
            status_flag = analysis.get('isRecollection')
            if isinstance(status_flag, bool):
                return status_flag
        return False

    chain_docs = []
    for doc in cursor:
        if doc is None:
            continue
        chain_docs.append({
            '_id': str(doc.get('_id')),
            'createdAt': doc.get('createdAt'),
            'updatedAt': doc.get('updatedAt'),
            'is_recollection': _extract_recollection_status(doc.get('analysisStatus'))
        })

    logger.info(f"Encontradas {len(chain_docs)} chain of custodies")

    if chain_docs:
        df_chain = pd.DataFrame(chain_docs)
        df_chain['_id'] = df_chain['_id'].astype(str)
        if 'createdAt' in df_chain.columns:
            df_chain['createdAt'] = pd.to_datetime(df_chain['createdAt'], errors='coerce', utc=True)
        if 'updatedAt' in df_chain.columns:
            df_chain['updatedAt'] = pd.to_datetime(df_chain['updatedAt'], errors='coerce', utc=True)
        df_chain['is_recollection'] = df_chain['is_recollection'].fillna(False).astype(bool)

        arquivo_path = os.path.join(OUTPUT_DIR, CHAIN_OF_CUSTODIES_FILE)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        atualizar_csv_incremental(arquivo_path, df_chain, '_id')
    else:
        logger.warning("Nenhuma chain of custody encontrada")

def extrair_prices():
    """Extrai preços por laboratório com merge incremental."""
    logger.info("Iniciando extração de prices...")

    db = connect_mongodb()
    if db is None:
        return

    collections = get_collections(db)

    cursor = collections["prices"].find({}, {
        "_id": 1,
        "_laboratory": 1,
        "active": 1,
        "voucherCommission": 1,
        "createdAt": 1,
        "updatedAt": 1,
        **{key: 1 for key in PRICE_CATEGORIES.keys()}
    })
    prices_docs = list(cursor)

    logger.info(f"Encontrados {len(prices_docs)} registros de prices")

    if prices_docs:
        df_prices = pd.DataFrame(prices_docs)
        df_prices['_id'] = df_prices['_id'].astype(str)
        if '_laboratory' in df_prices.columns:
            df_prices['_laboratory'] = df_prices['_laboratory'].astype(str)

        if 'active' in df_prices.columns:
            df_prices['active'] = df_prices['active'].apply(
                lambda x: str(x).strip().lower() in ('true', '1', 'yes') if pd.notna(x) else False
            )
        else:
            df_prices['active'] = False

        for col in ['createdAt', 'updatedAt']:
            if col in df_prices.columns:
                df_prices[col] = pd.to_datetime(df_prices[col], errors='coerce', utc=True)

        def _to_float_local(value: Any) -> float:
            if value is None or (isinstance(value, float) and np.isnan(value)):
                return np.nan
            try:
                return float(value)
            except (TypeError, ValueError):
                return np.nan

        def _price_total(value: Any) -> float:
            if isinstance(value, dict):
                return _to_float_local(value.get('price'))
            return np.nan

        def _price_gathering(value: Any) -> float:
            if isinstance(value, dict):
                fixed = value.get('fixed')
                if isinstance(fixed, dict):
                    return _to_float_local(fixed.get('gathering'))
            return np.nan

        def _price_exam(value: Any) -> float:
            if isinstance(value, dict):
                fixed = value.get('fixed')
                if isinstance(fixed, dict):
                    return _to_float_local(fixed.get('exam'))
            return np.nan

        for price_key, cfg in PRICE_CATEGORIES.items():
            if price_key in df_prices.columns:
                prefix = cfg['prefix']
                df_prices[f'Preco_{prefix}_Total'] = df_prices[price_key].apply(_price_total)
                df_prices[f'Preco_{prefix}_Coleta'] = df_prices[price_key].apply(_price_gathering)
                df_prices[f'Preco_{prefix}_Exame'] = df_prices[price_key].apply(_price_exam)

        # Converter voucher
        if 'voucherCommission' in df_prices.columns:
            df_prices['voucherCommission'] = pd.to_numeric(df_prices['voucherCommission'], errors='coerce')
        else:
            df_prices['voucherCommission'] = np.nan

        cols_to_drop = [key for key in PRICE_CATEGORIES.keys() if key in df_prices.columns]
        if cols_to_drop:
            df_prices = df_prices.drop(columns=cols_to_drop)

        arquivo_path = os.path.join(OUTPUT_DIR, PRICES_FILE)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        atualizar_csv_incremental(arquivo_path, df_prices, '_id')
    else:
        logger.warning("Nenhum price encontrado")

def carregar_dados_csv() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Carrega dados dos CSVs gerados."""
    try:
        # Carregar gatherings 2024
        arquivo_2024 = os.path.join(OUTPUT_DIR, GATHERINGS_2024_FILE)
        if os.path.exists(arquivo_2024):
            df_gatherings_2024 = pd.read_csv(arquivo_2024, encoding=ENCODING, low_memory=False)
            logger.info(f"Gatherings 2024 carregados: {len(df_gatherings_2024)} registros")
        else:
            df_gatherings_2024 = pd.DataFrame()
            logger.warning("Arquivo gatherings 2024 não encontrado")
        
        # Carregar gatherings 2025
        arquivo_2025 = os.path.join(OUTPUT_DIR, GATHERINGS_2025_FILE)
        if os.path.exists(arquivo_2025):
            df_gatherings_2025 = pd.read_csv(arquivo_2025, encoding=ENCODING, low_memory=False)
            logger.info(f"Gatherings 2025 carregados: {len(df_gatherings_2025)} registros")
        else:
            df_gatherings_2025 = pd.DataFrame()
            logger.warning("Arquivo gatherings 2025 não encontrado")
        
        # Carregar laboratories
        arquivo_labs = os.path.join(OUTPUT_DIR, LABORATORIES_FILE)
        if os.path.exists(arquivo_labs):
            df_laboratories = pd.read_csv(arquivo_labs, encoding=ENCODING, low_memory=False)
            logger.info(f"Laboratories carregados: {len(df_laboratories)} registros")
        else:
            df_laboratories = pd.DataFrame()
            logger.warning("Arquivo laboratories não encontrado")
        
        # Carregar representatives
        arquivo_reps = os.path.join(OUTPUT_DIR, REPRESENTATIVES_FILE)
        if os.path.exists(arquivo_reps):
            df_representatives = pd.read_csv(arquivo_reps, encoding=ENCODING, low_memory=False)
            logger.info(f"Representatives carregados: {len(df_representatives)} registros")
        else:
            df_representatives = pd.DataFrame()
            logger.warning("Arquivo representatives não encontrado")

        # Carregar chain of custodies
        arquivo_chain = os.path.join(OUTPUT_DIR, CHAIN_OF_CUSTODIES_FILE)
        if os.path.exists(arquivo_chain):
            df_chain = pd.read_csv(arquivo_chain, encoding=ENCODING, low_memory=False)
            logger.info(f"Chain of custodies carregadas: {len(df_chain)} registros")
        else:
            df_chain = pd.DataFrame()
            logger.warning("Arquivo chain of custodies não encontrado")

        # Carregar prices
        arquivo_prices = os.path.join(OUTPUT_DIR, PRICES_FILE)
        if os.path.exists(arquivo_prices):
            df_prices = pd.read_csv(arquivo_prices, encoding=ENCODING, low_memory=False)
            logger.info(f"Prices carregados: {len(df_prices)} registros")
        else:
            df_prices = pd.DataFrame()
            logger.warning("Arquivo prices não encontrado")
        
        return (
            df_gatherings_2024,
            df_gatherings_2025,
            df_laboratories,
            df_representatives,
            df_chain,
            df_prices
        )
        
    except Exception as e:
        logger.error(f"Erro ao carregar dados CSV: {e}")
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame()
        )

# ========================================
# FUNÇÕES DO SISTEMA V2
# ========================================

def calcular_baseline_mensal_robusta(base_df: pd.DataFrame, meses_nomes: List[str], top_n: int = BASELINE_TOP_N) -> pd.Series:
    """
    Calcula baseline mensal robusta como média dos top N meses de 2024 E 2025.
    
    Args:
        base_df: DataFrame com dados dos laboratórios
        meses_nomes: Lista com nomes dos meses
        top_n: Número de maiores meses a considerar (padrão: 3)
        
    Returns:
        Série com baseline mensal para cada laboratório
    """
    logger.info(f"Calculando baseline mensal robusta (top-{top_n} meses de 2024 e 2025)")
    
    # Colunas de coletas de 2024
    colunas_2024 = [f'N_Coletas_{m}_24' for m in meses_nomes]
    colunas_2024_existentes = [col for col in colunas_2024 if col in base_df.columns]
    
    # Colunas de coletas de 2025 (até mês atual)
    mes_atual = datetime.now().month
    meses_2025_disponiveis = meses_nomes[:mes_atual]
    colunas_2025 = [f'N_Coletas_{m}_25' for m in meses_2025_disponiveis]
    colunas_2025_existentes = [col for col in colunas_2025 if col in base_df.columns]
    
    # Combinar todas as colunas disponíveis
    todas_colunas = colunas_2024_existentes + colunas_2025_existentes
    
    if not todas_colunas:
        logger.warning("Nenhuma coluna de coletas encontrada. Baseline será 0.")
        return pd.Series(0, index=base_df.index)
    
    # Calcular média dos top N meses de ambos os anos combinados
    baseline = base_df[todas_colunas].apply(
        lambda row: row.nlargest(min(top_n, len(row))).mean() if row.sum() > 0 else 0,
        axis=1
    )
    
    logger.info(f"Baseline calculada (2024+2025): média={baseline.mean():.2f}, mediana={baseline.median():.2f}")
    return baseline


def extrair_componentes_baseline(base_df: pd.DataFrame,
                                 meses_nomes: List[str],
                                 top_n: int = BASELINE_TOP_N) -> pd.Series:
    """
    Retorna, para cada laboratório, os meses que compõem a baseline robusta.
    """
    colunas_2024 = [f'N_Coletas_{m}_24' for m in meses_nomes]
    mes_atual = datetime.now().month
    colunas_2025 = [f'N_Coletas_{m}_25' for m in meses_nomes[:mes_atual]]
    todas_colunas = [col for col in colunas_2024 + colunas_2025 if col in base_df.columns]

    if not todas_colunas:
        return pd.Series(['[]'] * len(base_df), index=base_df.index, dtype=object)

    def _label_coluna(col: str) -> str:
        partes = col.split('_')
        if len(partes) == 4:
            mes = partes[2]
            ano = partes[3]
            ano_completo = f"20{ano}"
            return f"{mes}/{ano_completo}"
        return col

    coluna_rotulo = {col: _label_coluna(col) for col in todas_colunas}

    def _componentes(row: pd.Series) -> str:
        itens = []
        for col in todas_colunas:
            valor = row.get(col, 0)
            if pd.notna(valor) and float(valor) > 0:
                itens.append({"mes": coluna_rotulo[col], "volume": float(valor)})
        itens.sort(key=lambda x: x['volume'], reverse=True)
        selecionados = [{"mes": item["mes"], "volume": int(round(item["volume"]))} for item in itens[:top_n]]
        return json.dumps(selecionados, ensure_ascii=False)

    return base_df.apply(_componentes, axis=1)


def calcular_wow_iso(base_df: pd.DataFrame, df_gatherings_2025: pd.DataFrame, uf: Optional[str] = None) -> pd.DataFrame:
    """
    Calcula variação Week over Week (WoW) usando semanas ISO com apenas dias úteis.
    
    Args:
        base_df: DataFrame com dados dos laboratórios
        df_gatherings_2025: DataFrame com coletas de 2025
        uf: UF para considerar feriados estaduais (opcional)
        
    Returns:
        DataFrame com colunas WoW_Semana_Atual, WoW_Semana_Anterior, WoW_Percentual
    """
    logger.info(f"Calculando WoW (Week over Week) com semanas ISO e dias úteis{f' para UF={uf}' if uf else ''}")
    
    if df_gatherings_2025.empty:
        logger.warning("Sem dados de 2025 para calcular WoW")
        return pd.DataFrame({
            'WoW_Semana_Atual': 0,
            'WoW_Semana_Anterior': 0,
            'WoW_Percentual': 0
        }, index=base_df.index)
    
    # Preparar dados
    df_wow = df_gatherings_2025.copy()
    if '_laboratory' not in df_wow.columns or 'createdAt' not in df_wow.columns:
        logger.error("Colunas necessárias não encontradas para WoW")
        return pd.DataFrame({
            'WoW_Semana_Atual': 0,
            'WoW_Semana_Anterior': 0,
            'WoW_Percentual': 0
        }, index=base_df.index)
    
    df_wow['createdAt'] = pd.to_datetime(df_wow['createdAt'], errors='coerce')
    df_wow = df_wow.dropna(subset=['createdAt'])
    
    # Obter semana ISO e ano
    df_wow['iso_year'] = df_wow['createdAt'].dt.isocalendar().year
    df_wow['iso_week'] = df_wow['createdAt'].dt.isocalendar().week
    df_wow['data_apenas'] = df_wow['createdAt'].dt.date
    
    # Filtrar apenas dias úteis se módulo disponível
    if MODULOS_V2_DISPONIVEIS:
        df_wow['is_util'] = df_wow['data_apenas'].apply(lambda d: is_dia_util(d, uf))
        df_wow = df_wow[df_wow['is_util']].copy()
    
    # Identificar semana ISO atual
    hoje = datetime.now()
    semana_atual = hoje.isocalendar().week
    ano_atual = hoje.isocalendar().year
    
    # Semana anterior
    data_semana_anterior = hoje - timedelta(days=7)
    semana_anterior = data_semana_anterior.isocalendar().week
    ano_anterior = data_semana_anterior.isocalendar().year
    
    # Agregar por laboratório e semana
    df_atual = df_wow[(df_wow['iso_year'] == ano_atual) & (df_wow['iso_week'] == semana_atual)]
    df_anterior = df_wow[(df_wow['iso_year'] == ano_anterior) & (df_wow['iso_week'] == semana_anterior)]
    
    vol_atual = df_atual.groupby('_laboratory').size().to_dict()
    vol_anterior = df_anterior.groupby('_laboratory').size().to_dict()
    
    # Calcular para cada laboratório
    wow_data = []
    for lab_id in base_df.index:
        v_atual = vol_atual.get(lab_id, 0)
        v_anterior = vol_anterior.get(lab_id, 0)
        
        if v_anterior > 0:
            wow_pct = ((v_atual - v_anterior) / v_anterior) * 100
        else:
            wow_pct = 0.0 if v_atual == 0 else 100.0
        
        wow_data.append({
            '_id': lab_id,
            'WoW_Semana_Atual': v_atual,
            'WoW_Semana_Anterior': v_anterior,
            'WoW_Percentual': round(wow_pct, 2)
        })
    
    df_wow_result = pd.DataFrame(wow_data).set_index('_id')
    logger.info(f"WoW calculado: {len(df_wow_result)} laboratórios")
    
    return df_wow_result.reindex(base_df.index, fill_value=0)


def integrar_dados_gralab(base_df: pd.DataFrame) -> pd.DataFrame:
    """
    Integra dados de concorrência do Gralab (últimos 7-14 dias).
    
    Args:
        base_df: DataFrame com dados dos laboratórios
        
    Returns:
        DataFrame com colunas Apareceu_Gralab, Gralab_Data, Gralab_Tipo
    """
    logger.info("Integrando dados de concorrência do Gralab")
    
    # Inicializar colunas
    base_df = base_df.copy()
    base_df['Apareceu_Gralab'] = False
    base_df['Gralab_Data'] = pd.NaT
    base_df['Gralab_Tipo'] = ''
    
    # Verificar se arquivo existe
    gralab_excel = os.path.join(OUTPUT_DIR, "Automations", "cunha", "relatorio_completo_laboratorios_gralab.xlsx")
    
    if not os.path.exists(gralab_excel):
        logger.warning(f"Arquivo Gralab não encontrado: {gralab_excel}")
        return base_df
    
    try:
        # Ler aba EntradaSaida
        df_entrada_saida = pd.read_excel(gralab_excel, sheet_name='EntradaSaida', engine='openpyxl')
        logger.info(f"Dados Gralab carregados: {len(df_entrada_saida)} registros")
        
        # Verificar colunas necessárias
        if 'CNPJ' not in df_entrada_saida.columns or 'Data' not in df_entrada_saida.columns:
            logger.error("Colunas esperadas não encontradas no arquivo Gralab")
            return base_df
        
        # Filtrar últimos N dias
        df_entrada_saida['Data'] = pd.to_datetime(df_entrada_saida['Data'], errors='coerce')
        hoje = datetime.now()
        janela_dias = GRALAB_JANELA_DIAS if 'GRALAB_JANELA_DIAS' in globals() else 14
        
        df_recente = df_entrada_saida[
            (df_entrada_saida['Data'].notna()) &
            ((hoje - df_entrada_saida['Data']).dt.days <= janela_dias)
        ].copy()
        
        logger.info(f"Registros Gralab recentes (últimos {janela_dias} dias): {len(df_recente)}")
        
        if df_recente.empty:
            return base_df
        
        # Normalizar CNPJ
        def normalizar_cnpj(cnpj):
            if pd.isna(cnpj):
                return ''
            cnpj_str = str(cnpj).strip()
            # Remover caracteres não numéricos e garantir 14 dígitos
            cnpj_limpo = ''.join(filter(str.isdigit, cnpj_str))
            if len(cnpj_limpo) == 0:
                return ''
            # Garantir 14 dígitos (preencher com zeros à esquerda se necessário)
            return cnpj_limpo.zfill(14)[:14]
        
        # Normalizar CNPJs em ambos os DataFrames
        df_recente['CNPJ_Normalizado'] = df_recente['CNPJ'].apply(normalizar_cnpj)
        # Verificar se CNPJ_PCL existe, caso contrário tentar outras colunas
        if 'CNPJ_PCL' in base_df.columns:
            base_df['CNPJ_Normalizado'] = base_df['CNPJ_PCL'].apply(normalizar_cnpj)
        elif 'cnpj' in base_df.columns:
            base_df['CNPJ_Normalizado'] = base_df['cnpj'].apply(normalizar_cnpj)
        else:
            logger.warning("Coluna CNPJ não encontrada no base_df. Tentando colunas disponíveis...")
            logger.warning(f"Colunas disponíveis: {list(base_df.columns)[:10]}")
            return base_df
        
        # Remover CNPJs vazios ou inválidos
        df_recente = df_recente[df_recente['CNPJ_Normalizado'] != ''].copy()
        
        logger.info(f"CNPJs normalizados - Gralab: {len(df_recente)}, Base: {base_df['CNPJ_Normalizado'].notna().sum()}")
        
        # Pegar registro mais recente por CNPJ
        df_recente = df_recente.sort_values('Data', ascending=False)
        df_recente_unique = df_recente.drop_duplicates(subset=['CNPJ_Normalizado'], keep='first')
        
        logger.info(f"CNPJs únicos no Gralab (últimos {janela_dias} dias): {len(df_recente_unique)}")
        
        # Merge usando merge do pandas para melhor performance
        base_df_merged = base_df.merge(
            df_recente_unique[['CNPJ_Normalizado', 'Data', 'Tipo']].rename(columns={'Data': 'Gralab_Data', 'Tipo': 'Gralab_Tipo'}),
            on='CNPJ_Normalizado',
            how='left'
        )
        
        # Atualizar flags
        base_df_merged['Apareceu_Gralab'] = base_df_merged['Gralab_Data'].notna()
        
        # Se Gralab_Tipo não existir na merge, criar coluna vazia
        if 'Gralab_Tipo' not in base_df_merged.columns:
            base_df_merged['Gralab_Tipo'] = ''
        else:
            base_df_merged['Gralab_Tipo'] = base_df_merged['Gralab_Tipo'].fillna('')
        
        qtd_com_gralab = base_df_merged['Apareceu_Gralab'].sum()
        logger.info(f"Integração Gralab concluída: {qtd_com_gralab} laboratórios com sinal de concorrência")
        
        # Log de exemplo para debug
        if qtd_com_gralab > 0:
            exemplo = base_df_merged[base_df_merged['Apareceu_Gralab']].head(1)
            if not exemplo.empty:
                logger.info(f"Exemplo de match: CNPJ={exemplo.iloc[0].get('CNPJ_PCL', 'N/A')}, Data={exemplo.iloc[0].get('Gralab_Data', 'N/A')}")
        
        return base_df_merged
        
    except Exception as e:
        logger.error(f"Erro ao integrar dados Gralab: {e}")
    
    return base_df


def classificar_risco_v2(row: pd.Series) -> Tuple[str, str]:
    """
    Classifica o status de risco conforme regras atualizadas (queda vs baseline/WoW e perda por dias).
    Retorna (Status, Motivo).
    """
    total_coletas_2025 = row.get('Total_Coletas_2025', 0) or 0
    coletas_mes_atual = row.get('Coletas_Mes_Atual', 0) or 0
    porte = row.get('Porte', 'Pequeno')
    dias_corridos = row.get('Dias_Sem_Coleta', 0) or 0

    if total_coletas_2025 == 0:
        return 'Normal', 'Sem coletas em 2025 - não considerado risco'

    # 1. Verificar Perda (Recente ou Antiga)
    # Se já está classificado como Perda, mantemos esse status específico
    # mas NÃO marcamos como 'Perda (Risco Alto)' para não misturar nos alertas de risco ativo
    perda_tipo = row.get('Classificacao_Perda_V2')
    if perda_tipo and perda_tipo != 'Sem Perda':
        return perda_tipo, f"Sem coletas há {int(dias_corridos)} dias (porte {porte})"

    # 2. Verificar Risco Ativo (Baseline, WoW, Dias Risco)
    motivos = []

    baseline = row.get('Baseline_Mensal', 0)
    coletas_atual = row.get('Coletas_Mes_Atual', 0)
    if baseline > 0:
        queda_baseline_pct = ((baseline - coletas_atual) / baseline) * 100
        if queda_baseline_pct > (REDUCAO_BASELINE_RISCO_ALTO * 100):
            motivos.append(f"Queda de {queda_baseline_pct:.1f}% vs baseline mensal")

    wow_pct = row.get('WoW_Percentual', 0)
    if wow_pct < -(REDUCAO_WOW_RISCO_ALTO * 100):
        motivos.append(f"Queda WoW de {abs(wow_pct):.1f}%")

    if row.get('Risco_Por_Dias_Sem_Coleta', False):
        motivos.append(f"{int(dias_corridos)} dia(s) sem coleta impactando o porte {porte}")

    if motivos:
        return 'Perda (Risco Alto)', '; '.join(motivos)

    return 'Normal', 'Volume dentro do esperado'


def calcular_metricas_churn():
    """Calcula métricas de churn com agregações vetorizadas (rápidas)."""
    logger.info("Iniciando cálculo de métricas de churn...")
    
    (
        df_gatherings_2024,
        df_gatherings_2025,
        df_laboratories,
        df_representatives,
        df_chainofcustodies,
        df_prices
    ) = carregar_dados_csv()
    
    if df_laboratories.empty:
        logger.warning("Nenhum laboratory encontrado para análise")
        return
    
    # Padronizar tipos de IDs
    def to_str_series(s: pd.Series) -> pd.Series:
        return s.astype(str).fillna("") if s is not None and len(s) else pd.Series(dtype=str)

    def parse_json_safe(value: Any) -> Any:
        if isinstance(value, (dict, list)):
            return value
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return {}
        if isinstance(value, str):
            txt = value.strip()
            if not txt or txt.lower() == 'nan':
                return {}
            try:
                return json.loads(txt)
            except json.JSONDecodeError:
                try:
                    txt_norm = txt.replace("'", '"')
                    return json.loads(txt_norm)
                except Exception:
                    logger.debug(f"Falha ao converter JSON: {txt[:120]}")
                    return {}
        return {}

    def to_float_safe(value: Any) -> float:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return np.nan
        try:
            return float(value)
        except (TypeError, ValueError):
            return np.nan

    if '_id' in df_laboratories.columns:
        df_laboratories['_id'] = to_str_series(df_laboratories['_id'])
    if '_representative' in df_laboratories.columns:
        df_laboratories['_representative'] = to_str_series(df_laboratories['_representative'])

    if not df_representatives.empty and '_id' in df_representatives.columns:
        df_representatives['_id'] = to_str_series(df_representatives['_id'])

    # Mapear recoletas por chain of custody
    chain_recollection_map: Dict[str, bool] = {}
    if not df_chainofcustodies.empty and '_id' in df_chainofcustodies.columns:
        df_chain = df_chainofcustodies.copy()
        df_chain['_id'] = to_str_series(df_chain['_id'])
        if 'is_recollection' in df_chain.columns:
            df_chain['is_recollection'] = df_chain['is_recollection'].fillna(False).astype(bool)
        elif 'isRecollection' in df_chain.columns:
            df_chain['is_recollection'] = df_chain['isRecollection'].fillna(False).astype(bool)
        else:
            if 'analysisStatus' in df_chain.columns:
                df_chain['analysisStatus'] = df_chain['analysisStatus'].apply(parse_json_safe)
            else:
                df_chain['analysisStatus'] = [{} for _ in range(len(df_chain))]

            def _extract_recollection_status(analysis: Any) -> bool:
                if isinstance(analysis, dict):
                    recol = analysis.get('recollection', {})
                    if isinstance(recol, dict):
                        status = recol.get('status')
                        if isinstance(status, bool):
                            return status
                        if isinstance(status, (int, float)):
                            return bool(status)
                    status_flag = analysis.get('isRecollection')
                    if isinstance(status_flag, bool):
                        return status_flag
                return False

            df_chain['is_recollection'] = df_chain['analysisStatus'].apply(_extract_recollection_status)

        df_chain['is_recollection'] = df_chain['is_recollection'].fillna(False).astype(bool)
        chain_recollection_map = df_chain.set_index('_id')['is_recollection'].to_dict()

    # Preparar gatherings 2024
    meses_nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    mes_limite_2025 = min(datetime.now().month, 12)

    df_gatherings_2024_valid = pd.DataFrame()
    df_gatherings_2024_recoleta = pd.DataFrame()
    if not df_gatherings_2024.empty:
        df_gatherings_2024 = df_gatherings_2024.copy()
        if '_laboratory' in df_gatherings_2024.columns:
            df_gatherings_2024['_laboratory'] = to_str_series(df_gatherings_2024['_laboratory'])
        if '_chainOfCustody' in df_gatherings_2024.columns:
            df_gatherings_2024['_chainOfCustody'] = to_str_series(df_gatherings_2024['_chainOfCustody'])
        else:
            df_gatherings_2024['_chainOfCustody'] = ''
        df_gatherings_2024['createdAt'] = pd.to_datetime(df_gatherings_2024.get('createdAt'), errors='coerce', utc=True)
        df_gatherings_2024['mes'] = df_gatherings_2024['createdAt'].dt.month
        df_gatherings_2024['is_recollection'] = df_gatherings_2024['_chainOfCustody'].map(chain_recollection_map).fillna(False).astype(bool)

        df_gatherings_2024_valid = df_gatherings_2024[~df_gatherings_2024['is_recollection']].copy()
        df_gatherings_2024_recoleta = df_gatherings_2024[df_gatherings_2024['is_recollection']].copy()

        total_2024 = df_gatherings_2024_valid.groupby('_laboratory').size().rename('Total_Coletas_2024')
        m2024 = df_gatherings_2024_valid.groupby(['_laboratory', 'mes']).size().unstack(fill_value=0)
        total_recoletas_2024 = df_gatherings_2024_recoleta.groupby('_laboratory').size().rename('Total_Recoletas_2024')
        m2024_recoleta = df_gatherings_2024_recoleta.groupby(['_laboratory', 'mes']).size().unstack(fill_value=0)
    else:
        total_2024 = pd.Series(dtype=int)
        m2024 = pd.DataFrame()
        total_recoletas_2024 = pd.Series(dtype=int)
        m2024_recoleta = pd.DataFrame()

    # Preparar gatherings 2025
    df_gatherings_2025_valid = pd.DataFrame()
    df_gatherings_2025_recoleta = pd.DataFrame()
    if not df_gatherings_2025.empty:
        df_gatherings_2025 = df_gatherings_2025.copy()
        if '_laboratory' in df_gatherings_2025.columns:
            df_gatherings_2025['_laboratory'] = to_str_series(df_gatherings_2025['_laboratory'])
        if '_chainOfCustody' in df_gatherings_2025.columns:
            df_gatherings_2025['_chainOfCustody'] = to_str_series(df_gatherings_2025['_chainOfCustody'])
        else:
            df_gatherings_2025['_chainOfCustody'] = ''
        df_gatherings_2025['createdAt'] = pd.to_datetime(df_gatherings_2025.get('createdAt'), errors='coerce', utc=True)
        df_gatherings_2025['mes'] = df_gatherings_2025['createdAt'].dt.month
        df_gatherings_2025['is_recollection'] = df_gatherings_2025['_chainOfCustody'].map(chain_recollection_map).fillna(False).astype(bool)

        df_gatherings_2025_valid = df_gatherings_2025[~df_gatherings_2025['is_recollection']].copy()
        df_gatherings_2025_recoleta = df_gatherings_2025[df_gatherings_2025['is_recollection']].copy()

        total_2025 = df_gatherings_2025_valid.groupby('_laboratory').size().rename('Total_Coletas_2025')
        ultima_2025 = df_gatherings_2025_valid.groupby('_laboratory')['createdAt'].max().rename('Data_Ultima_Coleta')
        m2025 = df_gatherings_2025_valid.groupby(['_laboratory', 'mes']).size().unstack(fill_value=0)
        total_recoletas_2025 = df_gatherings_2025_recoleta.groupby('_laboratory').size().rename('Total_Recoletas_2025')
        m2025_recoleta = df_gatherings_2025_recoleta.groupby(['_laboratory', 'mes']).size().unstack(fill_value=0)
    else:
        total_2025 = pd.Series(dtype=int)
        ultima_2025 = pd.Series(dtype='datetime64[ns]')
        m2025 = pd.DataFrame()
        total_recoletas_2025 = pd.Series(dtype=int)
        m2025_recoleta = pd.DataFrame()

    # Base: um por laboratório
    base = df_laboratories[['_id', 'cnpj', 'legalName', 'fantasyName']].copy() if all(k in df_laboratories.columns for k in ['_id','cnpj','legalName','fantasyName']) else df_laboratories.copy()
    base = base.rename(columns={'_id': '_id'})
    base['_id'] = to_str_series(base['_id'])
    base = base.drop_duplicates(subset=['_id'])
    base = base.set_index('_id')

    # Meses 2024 (fixos)
    for mes in range(1, 13):
        col = f'N_Coletas_{meses_nomes[mes-1]}_24'
        base[col] = m2024.get(mes, pd.Series(0, index=base.index)).reindex(base.index).fillna(0).astype(int)
        col_reco = f'Recoletas_{meses_nomes[mes-1]}_24'
        base[col_reco] = m2024_recoleta.get(mes, pd.Series(0, index=base.index)).reindex(base.index).fillna(0).astype(int)

    # Meses 2025 (até mês atual)
    for mes in range(1, mes_limite_2025 + 1):
        col = f'N_Coletas_{meses_nomes[mes-1]}_25'
        base[col] = m2025.get(mes, pd.Series(0, index=base.index)).reindex(base.index).fillna(0).astype(int)
        col_reco = f'Recoletas_{meses_nomes[mes-1]}_25'
        base[col_reco] = m2025_recoleta.get(mes, pd.Series(0, index=base.index)).reindex(base.index).fillna(0).astype(int)

    # Totais e últimas datas
    base['Total_Coletas_2024'] = total_2024.reindex(base.index).fillna(0).astype(int)
    base['Total_Coletas_2025'] = total_2025.reindex(base.index).fillna(0).astype(int)
    base['Total_Recoletas_2024'] = total_recoletas_2024.reindex(base.index).fillna(0).astype(int)
    base['Total_Recoletas_2025'] = total_recoletas_2025.reindex(base.index).fillna(0).astype(int)
    base['Data_Ultima_Coleta'] = ultima_2025.reindex(base.index)
    
    # Coletas do mês atual e flag de análise diária (requisito Gabi: 50+ coletas/mês)
    mes_atual = datetime.now().month
    if mes_atual <= mes_limite_2025 and mes_atual >= 1:
        # Pegar coletas do mês atual (último mês disponível em 2025)
        col_mes_atual = f'N_Coletas_{meses_nomes[mes_atual-1]}_25'
        if col_mes_atual in base.columns:
            base['Coletas_Mes_Atual'] = base[col_mes_atual]
        else:
            base['Coletas_Mes_Atual'] = 0
    else:
        base['Coletas_Mes_Atual'] = 0
    
    # Flag de análise diária: True se >= 50 coletas no mês, False caso contrário
    base['Analise_Diaria'] = (base['Coletas_Mes_Atual'] >= 50).astype(bool)

    # Preços por laboratório
    price_update_series = pd.Series(dtype='datetime64[ns]')
    voucher_series = pd.Series(dtype=float)
    if not df_prices.empty:
        df_prices_proc = df_prices.copy()
        if '_laboratory' in df_prices_proc.columns:
            df_prices_proc['_laboratory'] = to_str_series(df_prices_proc['_laboratory'])
        else:
            df_prices_proc['_laboratory'] = ''

        if 'active' in df_prices_proc.columns:
            df_prices_proc['active'] = df_prices_proc['active'].apply(
                lambda x: str(x).strip().lower() in ('true', '1', 'yes') if pd.notna(x) else False
            )
        else:
            df_prices_proc['active'] = False

        for col in ['createdAt', 'updatedAt']:
            if col in df_prices_proc.columns:
                df_prices_proc[col] = pd.to_datetime(df_prices_proc[col], errors='coerce', utc=True)
            else:
                df_prices_proc[col] = pd.NaT

        df_prices_proc['sort_date'] = df_prices_proc['updatedAt'].combine_first(df_prices_proc['createdAt'])
        df_prices_proc = df_prices_proc.sort_values(
            by=['_laboratory', 'active', 'sort_date'],
            ascending=[True, False, False]
        )
        df_prices_latest = df_prices_proc.drop_duplicates(subset=['_laboratory'], keep='first')

        price_records = []
        for _, row in df_prices_latest.iterrows():
            lab_id = row['_laboratory']
            if not lab_id:
                continue

            record = {
                '_id': lab_id,
                'Voucher_Commission': to_float_safe(row.get('voucherCommission')),
                'Data_Preco_Atualizacao': row.get('sort_date')
            }

            for price_key, cfg in PRICE_CATEGORIES.items():
                prefix = cfg['prefix']
                total_col = f'Preco_{prefix}_Total'
                coleta_col = f'Preco_{prefix}_Coleta'
                exame_col = f'Preco_{prefix}_Exame'

                if total_col in row.index or coleta_col in row.index or exame_col in row.index:
                    total_price = to_float_safe(row.get(total_col))
                    gathering_price = to_float_safe(row.get(coleta_col))
                    exam_price = to_float_safe(row.get(exame_col))
                else:
                    cat_data = parse_json_safe(row.get(price_key))
                    fixed_data = cat_data.get('fixed') if isinstance(cat_data, dict) else {}
                    total_price = to_float_safe(cat_data.get('price')) if isinstance(cat_data, dict) else np.nan
                    gathering_price = to_float_safe(fixed_data.get('gathering')) if isinstance(fixed_data, dict) else np.nan
                    exam_price = to_float_safe(fixed_data.get('exam')) if isinstance(fixed_data, dict) else np.nan

                record[f'Preco_{prefix}_Total'] = total_price
                record[f'Preco_{prefix}_Coleta'] = gathering_price
                record[f'Preco_{prefix}_Exame'] = exam_price

            price_records.append(record)

        if price_records:
            df_price_flat = pd.DataFrame(price_records).set_index('_id')
            price_update_series = df_price_flat.get('Data_Preco_Atualizacao', pd.Series(dtype='datetime64[ns]'))
            voucher_series = df_price_flat.get('Voucher_Commission', pd.Series(dtype=float))
            for price_key, cfg in PRICE_CATEGORIES.items():
                prefix = cfg['prefix']
                for suffix in ['Total', 'Coleta', 'Exame']:
                    col_name = f'Preco_{prefix}_{suffix}'
                    base[col_name] = df_price_flat.get(col_name, pd.Series(dtype=float)).reindex(base.index)
        else:
            for price_key, cfg in PRICE_CATEGORIES.items():
                prefix = cfg['prefix']
                for suffix in ['Total', 'Coleta', 'Exame']:
                    col_name = f'Preco_{prefix}_{suffix}'
                    base[col_name] = np.nan
    else:
        for price_key, cfg in PRICE_CATEGORIES.items():
            prefix = cfg['prefix']
            for suffix in ['Total', 'Coleta', 'Exame']:
                col_name = f'Preco_{prefix}_{suffix}'
                base[col_name] = np.nan

    if not price_update_series.empty:
        base['Data_Preco_Atualizacao'] = price_update_series.reindex(base.index)
    else:
        base['Data_Preco_Atualizacao'] = pd.NaT

    if not voucher_series.empty:
        base['Voucher_Commission'] = voucher_series.reindex(base.index)
    else:
        base['Voucher_Commission'] = np.nan

    # Agregação de dados diários para 2025 (para gráficos detalhados)
    def agregar_dados_diarios_2025(df_gatherings_2025, base_index):
        """Agrega dados de coletas por dia para cada laboratório em 2025."""
        if df_gatherings_2025.empty:
            return pd.Series(['{}'] * len(base_index), index=base_index)
        
        # Converter createdAt para datetime se não estiver
        df_gatherings_2025 = df_gatherings_2025.copy()
        df_gatherings_2025['createdAt'] = pd.to_datetime(df_gatherings_2025['createdAt'], errors='coerce', utc=True)
        
        # Extrair ano, mês e dia
        df_gatherings_2025['ano'] = df_gatherings_2025['createdAt'].dt.year
        df_gatherings_2025['mes'] = df_gatherings_2025['createdAt'].dt.month
        df_gatherings_2025['dia'] = df_gatherings_2025['createdAt'].dt.day
        
        # Filtrar apenas 2025
        df_2025 = df_gatherings_2025[df_gatherings_2025['ano'] == 2025].copy()
        
        if df_2025.empty:
            return pd.Series(['{}'] * len(base_index), index=base_index)
        
        # Agrupar por laboratório, mês e dia
        dados_diarios = df_2025.groupby(['_laboratory', 'mes', 'dia']).size().reset_index()
        dados_diarios.columns = ['_laboratory', 'mes', 'dia', 'coletas']
        
        # Converter para estrutura JSON por laboratório
        def criar_json_lab(lab_id):
            lab_data = dados_diarios[dados_diarios['_laboratory'] == lab_id]
            if lab_data.empty:
                return '{}'
            
            # Criar estrutura: {"2025-01": {"1": 2, "8": 1}, "2025-10": {"1": 1, "8": 1}}
            json_data = {}
            for _, row in lab_data.iterrows():
                # Verificar se mes e dia são válidos (não NaN)
                if pd.notna(row['mes']) and pd.notna(row['dia']):
                    mes_key = f"2025-{int(row['mes']):02d}"
                    if mes_key not in json_data:
                        json_data[mes_key] = {}
                    json_data[mes_key][str(int(row['dia']))] = int(row['coletas'])
            
            return json.dumps(json_data, ensure_ascii=False)
        
        # Aplicar para todos os laboratórios
        resultado = base_index.to_series().apply(criar_json_lab)
        return resultado

    # Adicionar coluna com dados diários de 2025
    base['Dados_Diarios_2025'] = agregar_dados_diarios_2025(df_gatherings_2025_valid, base.index)

    # Agregação de dados por dia da semana para 2025 (para gráfico semanal)
    def agregar_dados_semanais_2025(df_gatherings_2025, base_index):
        """Agrega dados de coletas por dia da semana para cada laboratório em 2025."""
        if df_gatherings_2025.empty:
            return pd.Series(['{}'] * len(base_index), index=base_index)
        
        # Converter createdAt para datetime se não estiver
        df_gatherings_2025 = df_gatherings_2025.copy()
        df_gatherings_2025['createdAt'] = pd.to_datetime(df_gatherings_2025['createdAt'], errors='coerce', utc=True)
        
        # Extrair ano e dia da semana (0=segunda, 6=domingo)
        df_gatherings_2025['ano'] = df_gatherings_2025['createdAt'].dt.year
        df_gatherings_2025['dia_semana'] = df_gatherings_2025['createdAt'].dt.dayofweek
        
        # Filtrar apenas 2025
        df_2025 = df_gatherings_2025[df_gatherings_2025['ano'] == 2025].copy()
        
        if df_2025.empty:
            return pd.Series(['{}'] * len(base_index), index=base_index)
        
        # Mapear números para nomes dos dias (apenas dias úteis)
        dias_semana_map = {0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta'}
        # Filtrar apenas dias úteis (segunda=0 a sexta=4)
        df_2025 = df_2025[df_2025['dia_semana'].isin([0, 1, 2, 3, 4])].copy()
        df_2025['dia_semana_nome'] = df_2025['dia_semana'].map(dias_semana_map)
        
        # Agrupar por laboratório e dia da semana
        dados_semanais = df_2025.groupby(['_laboratory', 'dia_semana_nome']).size().reset_index()
        dados_semanais.columns = ['_laboratory', 'dia_semana', 'coletas']
        
        # Converter para estrutura JSON por laboratório
        def criar_json_semanal_lab(lab_id):
            lab_data = dados_semanais[dados_semanais['_laboratory'] == lab_id]
            if lab_data.empty:
                return '{}'
            
            # Criar estrutura: {"Segunda": 2, "Terça": 1, "Quarta": 1, ...}
            json_data = {}
            for _, row in lab_data.iterrows():
                # Verificar se dia_semana é válido (não NaN)
                if pd.notna(row['dia_semana']):
                    json_data[row['dia_semana']] = int(row['coletas'])
            
            return json.dumps(json_data, ensure_ascii=False)
        
        # Aplicar para todos os laboratórios
        resultado = base_index.to_series().apply(criar_json_semanal_lab)
        return resultado

    # Adicionar coluna com dados semanais de 2025
    base['Dados_Semanais_2025'] = agregar_dados_semanais_2025(df_gatherings_2025_valid, base.index)

    # Maior mês 2024 e 2025
    if not m2024.empty:
        m24_vals = m2024.reindex(base.index).fillna(0)
        base['Maior_N_Coletas_Mes_2024'] = m24_vals.max(axis=1).astype(int)
        idx_max_24 = m24_vals.idxmax(axis=1)
        base['Mes_Historico'] = idx_max_24.apply(lambda m: f"{meses_nomes[int(m)-1]}/2024" if pd.notna(m) and m in range(1,13) else "")
    else:
        base['Maior_N_Coletas_Mes_2024'] = 0
        base['Mes_Historico'] = ""

    if not m2025.empty:
        m25_vals = m2025.reindex(base.index).fillna(0)
        base['Maior_N_Coletas_Mes_2025'] = m25_vals.max(axis=1).astype(int)
        idx_max_25 = m25_vals.idxmax(axis=1)
        base['Mes_Maior_Coleta_2025'] = idx_max_25.apply(lambda m: f"{meses_nomes[int(m)-1]}/2025" if pd.notna(m) and m in range(1,13) else "")
    else:
        base['Maior_N_Coletas_Mes_2025'] = 0
        base['Mes_Maior_Coleta_2025'] = ""

    # Dias sem coleta
    # Normalizar timezone: manter tudo em UTC tz-aware para cálculo
    base['Data_Ultima_Coleta'] = pd.to_datetime(base['Data_Ultima_Coleta'], errors='coerce', utc=True)
    now_dt = pd.Timestamp.now(tz='UTC')
    base['Dias_Sem_Coleta'] = (now_dt - base['Data_Ultima_Coleta']).dt.days
    base.loc[base['Data_Ultima_Coleta'].isna(), 'Dias_Sem_Coleta'] = 0
    base['Dias_Sem_Coleta'] = base['Dias_Sem_Coleta'].astype(int)
    base['Dias_Sem_Coleta_Uteis'] = base.apply(
        lambda row: calcular_dias_sem_coleta_uteis(
            row.get('Data_Ultima_Coleta'),
            row.get('Estado')
        ),
        axis=1
    ).astype(int)

    # Médias e variação
    meses_ate_agora_2025 = mes_limite_2025 if mes_limite_2025 > 0 else 1
    base['Media_Coletas_Mensal_2024'] = (base['Total_Coletas_2024'] / 12).fillna(0)
    base['Media_Coletas_Mensal_2025'] = (base['Total_Coletas_2025'] / meses_ate_agora_2025).fillna(0)
    base['Variacao_Percentual'] = np.where(
        base['Media_Coletas_Mensal_2024'] > 0,
        (base['Media_Coletas_Mensal_2025'] - base['Media_Coletas_Mensal_2024']) / base['Media_Coletas_Mensal_2024'] * 100,
        0
    )

    # Tendência
    base['Tendencia'] = np.where(base['Variacao_Percentual'] > 10, 'Crescimento',
                          np.where(base['Variacao_Percentual'] < -10, 'Declínio', 'Estável'))

    # Status de risco e motivo
    base['Status_Risco'] = 'Baixo'
    base['Motivo_Risco'] = 'Volume estável'

    base.loc[base['Dias_Sem_Coleta'] >= DIAS_INATIVO, 'Status_Risco'] = 'Inativo'
    # Aplicar lógica de risco alto apenas para registros que não são inativos
    mask_risco_alto = (base['Dias_Sem_Coleta'] >= DIAS_RISCO_ALTO) & (base['Dias_Sem_Coleta'] < DIAS_INATIVO)
    base.loc[mask_risco_alto, 'Status_Risco'] = 'Alto'
    base.loc[(base['Dias_Sem_Coleta'] >= DIAS_RISCO_MEDIO) & (base['Dias_Sem_Coleta'] < DIAS_RISCO_ALTO), 'Status_Risco'] = 'Médio'

    base.loc[base['Status_Risco'] == 'Inativo', 'Motivo_Risco'] = base['Dias_Sem_Coleta'].apply(lambda d: f"Sem coletas há {int(d)} dias")
    base.loc[base['Status_Risco'] == 'Alto', 'Motivo_Risco'] = base['Dias_Sem_Coleta'].apply(lambda d: f"Sem coletas há {int(d)} dias")
    base.loc[(base['Status_Risco'] == 'Médio') & (base['Dias_Sem_Coleta'] > 0), 'Motivo_Risco'] = base['Dias_Sem_Coleta'].apply(lambda d: f"Sem coletas há {int(d)} dias")
    base.loc[(base['Status_Risco'] == 'Baixo') & (base['Variacao_Percentual'] <= -REDUCAO_ALTO_RISCO * 100), 'Status_Risco'] = 'Alto'
    base.loc[(base['Status_Risco'] == 'Baixo') & (base['Variacao_Percentual'] <= -REDUCAO_MEDIO_RISCO * 100) & (base['Variacao_Percentual'] > -REDUCAO_ALTO_RISCO * 100), 'Status_Risco'] = 'Médio'
    base.loc[base['Status_Risco'].isin(['Alto','Médio']) & (base['Dias_Sem_Coleta'] == 0), 'Motivo_Risco'] = base['Variacao_Percentual'].apply(lambda v: f"Redução de {abs(v):.1f}% vs 2024")

    # Representante
    if not df_representatives.empty and '_id' in df_representatives.columns:
        reps = df_representatives[['_id','name']].copy() if all(k in df_representatives.columns for k in ['_id','name']) else df_representatives.copy()
        reps = reps.rename(columns={'_id': '_rep_id', 'name': 'Representante_Nome'})
        reps['_rep_id'] = to_str_series(reps['_rep_id'])
        labs_rep = df_laboratories[['_id','_representative']].copy() if all(k in df_laboratories.columns for k in ['_id','_representative']) else df_laboratories.copy()
        labs_rep = labs_rep.rename(columns={'_id': '_id', '_representative': 'Representante_ID'})
        labs_rep['_id'] = to_str_series(labs_rep['_id'])
        labs_rep['Representante_ID'] = to_str_series(labs_rep['Representante_ID'])
        merged = labs_rep.merge(reps, left_on='Representante_ID', right_on='_rep_id', how='left')
        merged = merged.set_index('_id')
        base['Representante_ID'] = merged['Representante_ID']
        base['Representante_Nome'] = merged['Representante_Nome']
    else:
        base['Representante_ID'] = ''
        base['Representante_Nome'] = ''

    # Campos de identificação/descrição
    # Campos de identificação/descrição
    base['CNPJ_PCL'] = df_laboratories.set_index('_id').reindex(base.index).get('cnpj') if 'cnpj' in df_laboratories.columns else ''
    base['Razao_Social_PCL'] = df_laboratories.set_index('_id').reindex(base.index).get('legalName') if 'legalName' in df_laboratories.columns else ''
    base['Nome_Fantasia_PCL'] = df_laboratories.set_index('_id').reindex(base.index).get('fantasyName') if 'fantasyName' in df_laboratories.columns else ''

    # Debug: verificar colunas de endereço disponíveis
    logger.info(f"Colunas disponíveis em df_laboratories: {list(df_laboratories.columns)}")

    # Estado e Cidade - extrair da coluna 'address' que contém dados JSON
    import re

    def extrair_estado_cidade_json(address_str):
        """Extrai estado e cidade da string JSON de endereço."""
        if pd.isna(address_str) or address_str == '':
            return '', ''

        try:
            # Primeiro, tentar substituir ObjectId por null para facilitar o parse JSON
            address_clean = re.sub(r'ObjectId\([^)]+\)', 'null', address_str)
            # Converter aspas simples para duplas para JSON válido
            address_clean = address_clean.replace("'", '"')

            # Fazer parse do JSON
            address_dict = json.loads(address_clean)

            # Extrair estado e cidade
            estado = ''
            cidade = ''

            if 'state' in address_dict:
                state_data = address_dict['state']
                if isinstance(state_data, dict) and 'code' in state_data:
                    estado = state_data['code']
                elif isinstance(state_data, str):
                    estado = state_data

            if 'city' in address_dict:
                cidade = address_dict['city']

            return str(estado).strip(), str(cidade).strip()

        except Exception as e:
            # Fallback: tentar extrair com regex se JSON falhar
            try:
                # Procurar por '"code": "XX"' no estado
                state_match = re.search(r'"code":\s*"([^"]+)"', address_str)
                estado = state_match.group(1) if state_match else ''

                # Procurar por '"city": "Nome"' na cidade
                city_match = re.search(r'"city":\s*"([^"]+)"', address_str)
                cidade = city_match.group(1) if city_match else ''

                return str(estado).strip(), str(cidade).strip()
            except:
                logger.warning(f"Erro ao extrair endereço: {e}, valor: {address_str}")
                return '', ''

    # Aplicar extração para todas as linhas
    labs_address = df_laboratories.set_index('_id').reindex(base.index)['address']
    enderecos_extraidos = labs_address.apply(extrair_estado_cidade_json)

    base['Estado'] = enderecos_extraidos.apply(lambda x: x[0])
    base['Cidade'] = enderecos_extraidos.apply(lambda x: x[1])

    # Debug: mostrar alguns exemplos
    logger.info(f"Exemplos de endereços processados:")
    for i, (estado, cidade) in enumerate(enderecos_extraidos.head(3)):
        logger.info(f"  Lab {i+1}: Estado='{estado}', Cidade='{cidade}'")

    # Garantir que não há valores None
    base['Estado'] = base['Estado'].fillna('')
    base['Cidade'] = base['Cidade'].fillna('')

    # ================================
    # Séries de controle em dias úteis
    # ================================
    def _preparar_serie_business_day(serie: pd.Series, ultimo_bday: pd.Timestamp) -> pd.Series:
        """Reindexa para dias úteis e aplica forward-fill antes do rolling."""
        serie = serie.sort_index()
        if serie.empty:
            return serie.astype(float)
        end_date = max(serie.index.max(), ultimo_bday)
        idx = pd.date_range(serie.index.min(), end_date, freq='B')
        serie = serie.reindex(idx)
        serie = serie.ffill()
        serie = serie.fillna(0)
        return serie.astype(float)

    def _calcular_mm_series(serie: pd.Series, ultimo_bday: pd.Timestamp) -> Tuple[float, float]:
        """Calcula MM7/MM30 considerando apenas dias úteis."""
        serie_bd = _preparar_serie_business_day(serie, ultimo_bday)
        if serie_bd.empty:
            return np.nan, np.nan
        mm7 = serie_bd.rolling(window=7, min_periods=1).mean().iloc[-1]
        mm30 = serie_bd.rolling(window=30, min_periods=1).mean().iloc[-1]
        return float(mm7), float(mm30)

    frames_gatherings = []
    for df_src in (df_gatherings_2024_valid, df_gatherings_2025_valid):
        if not df_src.empty and all(col in df_src.columns for col in ['_laboratory', 'createdAt']):
            frames_gatherings.append(df_src[['_laboratory', 'createdAt']].copy())

    mm7_br = np.nan
    mm30_br = np.nan
    mm7_por_uf: Dict[str, float] = {}
    mm30_por_uf: Dict[str, float] = {}
    mm7_por_cidade: Dict[Tuple[str, str], float] = {}
    mm30_por_cidade: Dict[Tuple[str, str], float] = {}

    if frames_gatherings:
        df_gatherings_total = pd.concat(frames_gatherings, ignore_index=True)
        df_gatherings_total['_laboratory'] = df_gatherings_total['_laboratory'].astype(str)
        df_gatherings_total['createdAt'] = pd.to_datetime(
            df_gatherings_total['createdAt'], errors='coerce', utc=True
        )
        df_gatherings_total = df_gatherings_total.dropna(subset=['createdAt'])
        df_gatherings_total['createdAt'] = df_gatherings_total['createdAt'].dt.tz_convert(timezone_br)
        df_gatherings_total['data_ref'] = pd.to_datetime(df_gatherings_total['createdAt'].dt.date)

        estado_map = base['Estado'].to_dict()
        cidade_map = base['Cidade'].to_dict()
        df_gatherings_total['Estado'] = df_gatherings_total['_laboratory'].map(estado_map).fillna('')
        df_gatherings_total['Cidade'] = df_gatherings_total['_laboratory'].map(cidade_map).fillna('')

        ultimo_bday = pd.bdate_range(
            end=pd.Timestamp.now(tz=timezone_br).normalize().tz_localize(None),
            periods=1
        )[0]

        serie_br = df_gatherings_total.groupby('data_ref').size()
        mm7_br, mm30_br = _calcular_mm_series(serie_br, ultimo_bday)

        df_uf = df_gatherings_total[df_gatherings_total['Estado'] != '']
        if not df_uf.empty:
            serie_uf = df_uf.groupby(['Estado', 'data_ref']).size()
            for estado, serie_estado in serie_uf.groupby(level=0):
                serie_estado = serie_estado.droplevel(0)
                mm7_val, mm30_val = _calcular_mm_series(serie_estado, ultimo_bday)
                mm7_por_uf[estado] = mm7_val
                mm30_por_uf[estado] = mm30_val

            df_cidade = df_uf[df_uf['Cidade'] != '']
            if not df_cidade.empty:
                serie_cidade = df_cidade.groupby(['Estado', 'Cidade', 'data_ref']).size()
                for (estado, cidade), serie_loc in serie_cidade.groupby(level=[0, 1]):
                    serie_loc = serie_loc.droplevel([0, 1])
                    mm7_val, mm30_val = _calcular_mm_series(serie_loc, ultimo_bday)
                    chave = (estado, cidade)
                    mm7_por_cidade[chave] = mm7_val
                    mm30_por_cidade[chave] = mm30_val

    base['MM7_BR'] = mm7_br
    base['MM30_BR'] = mm30_br
    base['MM7_UF'] = base['Estado'].map(mm7_por_uf)
    base['MM30_UF'] = base['Estado'].map(mm30_por_uf)
    base['MM7_CIDADE'] = pd.Series(
        [mm7_por_cidade.get((estado, cidade), np.nan) for estado, cidade in zip(base['Estado'], base['Cidade'])],
        index=base.index,
        dtype=float
    )
    base['MM30_CIDADE'] = pd.Series(
        [mm30_por_cidade.get((estado, cidade), np.nan) for estado, cidade in zip(base['Estado'], base['Cidade'])],
        index=base.index,
        dtype=float
    )

    # ================================
    # SISTEMA DE ALERTAS V2
    # ================================
    if MODULOS_V2_DISPONIVEIS:
        logger.info("Aplicando sistema de alertas v2...")
        
        try:
            # 1. Calcular baseline mensal robusta
            base['Baseline_Mensal'] = calcular_baseline_mensal_robusta(base, meses_nomes, BASELINE_TOP_N)
            base['Baseline_Componentes'] = extrair_componentes_baseline(base, meses_nomes, BASELINE_TOP_N)
            
            # 2. Calcular WoW (Week over Week)
            df_wow = calcular_wow_iso(base, df_gatherings_2025_valid, uf=None)
            base = base.join(df_wow)
            
            # Adicionar coluna de queda para cálculo de severidade
            base['Queda_Baseline_Pct'] = np.where(
                base['Baseline_Mensal'] > 0,
                ((base['Baseline_Mensal'] - base['Coletas_Mes_Atual']) / base['Baseline_Mensal']) * 100,
                0
            )
            
            # 3. Aplicar classificação de porte
            base = aplicar_porte_dataframe(
                base,
                coluna_volume='Media_Coletas_Mensal_2025',
                coluna_destino='Porte',
                limiar_grande=PORTE_GRANDE_MIN,
                limiar_medio=PORTE_MEDIO_MIN
            )
            base['Risco_Por_Dias_Sem_Coleta'] = base.apply(
                lambda row: avaliar_risco_por_dias_sem_coleta(
                    row.get('Dias_Sem_Coleta', 0),
                    row.get('Dias_Sem_Coleta_Uteis', 0),
                    row.get('Porte', 'Pequeno')
                ),
                axis=1
            )
            base['Classificacao_Perda_V2'] = base.apply(
                lambda row: classificar_perda_por_dias_sem_coleta(
                    row.get('Dias_Sem_Coleta', 0),
                    row.get('Dias_Sem_Coleta_Uteis', 0),
                    row.get('Porte', 'Pequeno')
                ) or 'Sem Perda',
                axis=1
            )
            
            # 4. Aplicar gatilho de dias sem coleta por porte
            base = aplicar_gatilho_dataframe(
                base,
                coluna_dias='Dias_Sem_Coleta',
                coluna_porte='Porte',
                coluna_destino='Gatilho_Dias_Sem_Coleta',
                coluna_dias_uteis='Dias_Sem_Coleta_Uteis'
            )
            
            # 5. Integrar dados de concorrência (Gralab)
            base = integrar_dados_gralab(base)
            
            # 6. Aplicar classificação de risco v2 (binária)
            risco_v2_results = base.apply(classificar_risco_v2, axis=1)
            base['Status_Risco_V2'] = risco_v2_results.apply(lambda x: x[0])
            base['Motivo_Risco_V2'] = risco_v2_results.apply(lambda x: x[1])
            
            # 7. Filtrar laboratórios sem coletas em 2025 antes de calcular severidade
            # Isso garante que labs como MARICONDI (sem coletas desde 2024) não apareçam nos alertas
            # Critérios rigorosos: deve ter coletas em 2025 E última coleta deve ser em 2025
            base['Total_Coletas_2025'] = base['Total_Coletas_2025'].fillna(0).astype(int)
            base['Coletas_Mes_Atual'] = base['Coletas_Mes_Atual'].fillna(0).astype(int)
            
            # Verificar se Data_Ultima_Coleta existe e é de 2025
            if 'Data_Ultima_Coleta' in base.columns:
                base['Data_Ultima_Coleta'] = pd.to_datetime(base['Data_Ultima_Coleta'], errors='coerce')
                # Filtrar: deve ter coletas em 2025 E última coleta deve ser de 2025 ou posterior
                mask_coletas_2025 = (
                    (base['Total_Coletas_2025'] > 0) & 
                    (base['Data_Ultima_Coleta'].notna()) &
                    (base['Data_Ultima_Coleta'].dt.year >= 2025)
                )
            else:
                # Fallback: apenas verificar Total_Coletas_2025
                mask_coletas_2025 = (base['Total_Coletas_2025'] > 0)
            
            base_com_coletas_2025 = base[mask_coletas_2025].copy()
            
            # Log detalhado para debug
            labs_filtrados = len(base) - len(base_com_coletas_2025)
            logger.info(f"Filtro de coletas 2025: {len(base)} labs → {len(base_com_coletas_2025)} labs com coletas em 2025 ({labs_filtrados} filtrados)")
            
            # Log de exemplo de labs filtrados (para debug)
            if labs_filtrados > 0:
                labs_sem_coleta = base[~mask_coletas_2025].head(5)
                for idx, lab in labs_sem_coleta.iterrows():
                    nome = lab.get('Nome_Fantasia_PCL', lab.get('Razao_Social_PCL', 'N/A'))
                    total_2025 = lab.get('Total_Coletas_2025', 0)
                    ultima_coleta = lab.get('Data_Ultima_Coleta', 'N/A')
                    logger.info(f"  Lab filtrado: {nome} - Total_2025={total_2025}, Ultima_Coleta={ultima_coleta}")
            
            # 8. Preparar alertas prioritários
            df_alto_risco = base_com_coletas_2025[base_com_coletas_2025['Status_Risco_V2'] == 'Perda (Risco Alto)'].copy()
            
            if not df_alto_risco.empty:
                # 9. Aplicar cap de alertas (global)
                df_alertas_cap = aplicar_cap_alertas(df_alto_risco, cap=ALERTA_CAP_DEFAULT)
                
                # 10. Processar por UF (usar base_com_coletas_2025 para garantir que apenas labs com coletas sejam considerados)
                alertas_por_uf = processar_alertas_por_uf(
                    base_com_coletas_2025,
                    cap_global=ALERTA_CAP_DEFAULT,
                    coluna_uf='Estado',
                    coluna_risco='Status_Risco_V2'
                )
                
                # 11. Gerar e salvar relatório
                relatorio = gerar_relatorio_alertas(df_alertas_cap)
                relatorio_texto = formatar_relatorio_texto(relatorio)
                logger.info(f"\n{relatorio_texto}")
                
                # Salvar alertas prioritários em arquivo separado
                arquivo_alertas = os.path.join(OUTPUT_DIR, "alertas_prioritarios.csv")
                df_alertas_cap.to_csv(arquivo_alertas, index=False, encoding=ENCODING)
                logger.info(f"Alertas prioritários salvos: {arquivo_alertas}")
                
                # Salvar alertas por UF
                for uf, df_uf_alertas in alertas_por_uf.items():
                    arquivo_uf = os.path.join(OUTPUT_DIR, f"alertas_uf_{uf}.csv")
                    df_uf_alertas.to_csv(arquivo_uf, index=False, encoding=ENCODING)
                
                logger.info(f"Sistema v2: {len(df_alto_risco)} alertas identificados, {len(df_alertas_cap)} após cap")
            else:
                logger.info("Sistema v2: Nenhum alerta de risco alto identificado")
            
        except Exception as e:
            logger.error(f"Erro ao aplicar sistema v2: {e}. Continuando com sistema legado.", exc_info=True)
    else:
        logger.warning("Módulos v2 não disponíveis. Usando sistema legado de alertas.")
        # Adicionar colunas vazias do sistema v2 para compatibilidade
        base['Baseline_Mensal'] = 0
        base['Baseline_Componentes'] = '[]'
        base['WoW_Semana_Atual'] = 0
        base['WoW_Semana_Anterior'] = 0
        base['WoW_Percentual'] = 0
        base['Queda_Baseline_Pct'] = 0
        base['Porte'] = 'Desconhecido'
        base['Gatilho_Dias_Sem_Coleta'] = False
        base['Risco_Por_Dias_Sem_Coleta'] = False
        base['Classificacao_Perda_V2'] = 'Sem Perda'
        base['Apareceu_Gralab'] = False
        base['Gralab_Data'] = pd.NaT
        base['Gralab_Tipo'] = ''
        base['Status_Risco_V2'] = base['Status_Risco']
        base['Motivo_Risco_V2'] = base['Motivo_Risco']

    # Resumos semanais/mensais
    semanas_json, semanas_meta = gerar_resumo_semanal_mes(base, df_gatherings_2025_valid)
    if semanas_json.empty:
        base['Semanas_Mes_Atual'] = '[]'
    else:
        base['Semanas_Mes_Atual'] = semanas_json.reindex(base.index).fillna('[]')
    meta_fechamento = semanas_meta or {}
    base['Semanas_Fechadas_Mes'] = meta_fechamento.get('semanas_fechadas', 0)

    semanas_correntes_ano = max(1, datetime.now(timezone_br).isocalendar()[1])
    media_semanal_2024 = float(base['Total_Coletas_2024'].sum() / 52) if len(base) else 0.0
    media_semanal_2025 = float(base['Total_Coletas_2025'].sum() / semanas_correntes_ano) if len(base) else 0.0
    base['Media_Semanal_BR_2024'] = media_semanal_2024
    base['Media_Semanal_BR_2025'] = media_semanal_2025
    media_uf = (
        base.groupby('Estado')['Total_Coletas_2025'].sum() / semanas_correntes_ano
        if len(base) else pd.Series(dtype=float)
    )
    media_uf_dict = media_uf.fillna(0).to_dict() if isinstance(media_uf, pd.Series) else {}
    base['Media_Semanal_UF_Atual'] = base['Estado'].map(media_uf_dict).fillna(0)

    meta_fechamento.update({
        "media_semanal_pais_2024": media_semanal_2024,
        "media_semanal_pais_2025": media_semanal_2025,
        "media_semanal_por_uf": media_uf_dict
    })

    try:
        meta_path = os.path.join(OUTPUT_DIR, "fechamentos_meta.json")
        with open(meta_path, 'w', encoding='utf-8') as fp:
            json.dump(meta_fechamento, fp, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        logger.warning(f"Não foi possível salvar metadados de fechamento: {e}")

    # CÁLCULO DA MÉDIA SEMANAL POR LABORATÓRIO (Para a aba Fechamento Semanal)
    # Semanas decorridas em 2025 (considerando a data atual)
    semana_atual_iso = datetime.now().isocalendar()[1]
    # Evitar divisão por zero no início do ano
    divisor_semanas = max(1, semana_atual_iso - 1) 
    
    # Calcular média semanal simples (Total / Semanas Decorridas)
    base['Media_Semanal_2025'] = (base['Total_Coletas_2025'] / divisor_semanas).fillna(0).round(1)

    # Metadados
    base['Data_Analise'] = datetime.now()

    # Reordenar colunas principais
    cols_inicio = [
        'CNPJ_PCL','Razao_Social_PCL','Nome_Fantasia_PCL','Estado','Cidade',
        'Representante_Nome','Representante_ID',
        'Maior_N_Coletas_Mes_Historico','Mes_Historico','Maior_N_Coletas_Mes_2024','Maior_N_Coletas_Mes_2025'
    ]
    cols_2024 = [f'N_Coletas_{m}_24' for m in meses_nomes]
    cols_2025 = [f'N_Coletas_{m}_25' for m in meses_nomes[:mes_limite_2025]]
    cols_recoletas_2024 = [f'Recoletas_{m}_24' for m in meses_nomes]
    cols_recoletas_2025 = [f'Recoletas_{m}_25' for m in meses_nomes[:mes_limite_2025]]
    cols_precos = []
    for price_key, cfg in PRICE_CATEGORIES.items():
        prefix = cfg['prefix']
        cols_precos.extend([
            f'Preco_{prefix}_Total',
            f'Preco_{prefix}_Coleta',
            f'Preco_{prefix}_Exame'
        ])

    cols_fim = [
        'MM7_BR','MM30_BR','MM7_UF','MM30_UF','MM7_CIDADE','MM30_CIDADE',
        'Data_Ultima_Coleta','Dias_Sem_Coleta','Media_Coletas_Mensal_2024','Media_Coletas_Mensal_2025',
        'Variacao_Percentual','Tendencia','Status_Risco','Motivo_Risco','Data_Analise',
        'Total_Coletas_2024','Total_Coletas_2025','Total_Recoletas_2024','Total_Recoletas_2025',
        'Coletas_Mes_Atual','Analise_Diaria',
        'Voucher_Commission','Data_Preco_Atualizacao','Dados_Diarios_2025','Dados_Semanais_2025',
        'Media_Semanal_2025',
        # Colunas do Sistema v2
        'Baseline_Mensal','Baseline_Componentes',
        'WoW_Semana_Atual','WoW_Semana_Anterior','WoW_Percentual',
        'Queda_Baseline_Pct','Porte','Gatilho_Dias_Sem_Coleta',
        'Dias_Sem_Coleta_Uteis','Risco_Por_Dias_Sem_Coleta','Classificacao_Perda_V2',
        'Semanas_Mes_Atual','Semanas_Fechadas_Mes',
        'Media_Semanal_BR_2024','Media_Semanal_BR_2025','Media_Semanal_UF_Atual',
        'Apareceu_Gralab','Gralab_Data','Gralab_Tipo',
        'Status_Risco_V2','Motivo_Risco_V2'
    ]

    # Garantir colunas existentes
    for c in cols_inicio + cols_2024 + cols_recoletas_2024 + cols_2025 + cols_recoletas_2025 + cols_precos + cols_fim:
        if c not in base.columns:
            base[c] = '' if c in ['CNPJ_PCL','Razao_Social_PCL','Nome_Fantasia_PCL','Estado','Cidade','Representante_Nome','Representante_ID','Mes_Historico','Tendencia','Status_Risco','Motivo_Risco'] else 0

    df_churn = base[
        cols_inicio +
        cols_2024 +
        cols_recoletas_2024 +
        cols_2025 +
        cols_recoletas_2025 +
        cols_precos +
        cols_fim
    ].reset_index(drop=False)
    logger.info(f"Análise de churn concluída: {len(df_churn)} laboratórios processados")
    
    if df_churn.empty:
        logger.warning("Nenhum dado de churn gerado")
        return

    # Salvar análise (parquet + CSV) e tentar upload opcional para SharePoint
        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
        arquivo_timestamp = os.path.join(OUTPUT_DIR, f"churn_analysis_{timestamp}.parquet")
        df_churn.to_parquet(arquivo_timestamp, engine='pyarrow', compression='snappy', index=False)
        
        arquivo_latest = os.path.join(OUTPUT_DIR, CHURN_ANALYSIS_FILE)
        df_churn.to_parquet(arquivo_latest, engine='pyarrow', compression='snappy', index=False)
        
        arquivo_csv = os.path.join(OUTPUT_DIR, "churn_analysis_latest.csv")
        df_churn.to_csv(arquivo_csv, index=False, encoding=ENCODING)
        logger.info(f"Análise de churn salva: {arquivo_latest}")
        
    # Tentar upload para SharePoint usando secrets locais (se disponível)
    try:
        if tomllib is not None and ChurnSPConnector is not None:
            base_dir = os.path.dirname(__file__)
            secrets_path = os.path.join(base_dir, '.streamlit', 'secrets.toml')
            if os.path.exists(secrets_path):
                with open(secrets_path, 'rb') as f:
                    secrets_cfg = tomllib.load(f)
                files_cfg = secrets_cfg.get('files', {})
                arquivo_remoto = files_cfg.get('arquivo')
                if arquivo_remoto:
                    connector = ChurnSPConnector(config={
                        'graph': secrets_cfg.get('graph', {}),
                        'onedrive': secrets_cfg.get('onedrive', {}),
                        'files': secrets_cfg.get('files', {}),
                        'output_dir': secrets_cfg.get('output_dir', OUTPUT_DIR)
                    })
                    connector.write_csv(df_churn, arquivo_remoto, overwrite=True)
                    logger.info("Arquivo de churn enviado ao SharePoint com sucesso.")
    except Exception as e:
        logger.warning(f"Falha ao enviar arquivo ao SharePoint (ignorado): {e}")

        # Estatísticas resumidas
    try:
        status_counts = df_churn['Status_Risco'].value_counts()
        logger.info(f"Distribuição de risco: {dict(status_counts)}")
        if 'Alto' in status_counts and status_counts['Alto'] >= ALERTA_THRESHOLD_ALTO:
            enviar_alerta_email(df_churn)
    except Exception:
        pass

def executar_extracoes():
    """Executa todas as extrações de dados."""
    logger.info("Iniciando extrações de dados...")
    
    # Extrair 2024 apenas se arquivo não existir
    extrair_gatherings_2024()
    
    # Extrair dados que precisam de retroalimentação
    extrair_gatherings_2025()
    extrair_laboratories()
    extrair_representatives()
    extrair_chainofcustodies()
    extrair_prices()
    
    # Calcular métricas de churn
    calcular_metricas_churn()
    
    logger.info("Extrações concluídas!")

def executar_gerador():
    """Executa o gerador em loop com agendamento."""
    logger.info(f"Iniciando gerador Churn - execução a cada 15 minutos.")
    
    # Executar primeira vez
    executar_extracoes()
    
    # Agendar execuções futuras
    schedule.every(15).minutes.do(executar_extracoes)
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Verificar a cada minuto
        except KeyboardInterrupt:
            logger.info("Interrompido pelo usuário.")
            break
        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")
            time.sleep(60)

# ==========================
# Função de alerta (segura)
# ==========================
def enviar_alerta_email(df_churn: pd.DataFrame) -> None:
    """Envia alerta por e-mail de forma segura (ou apenas loga se indisponível).

    - Usa credenciais do config_churn se disponíveis
    - Nunca lança exceção para não interromper o gerador
    """
    try:
        alto_risco = df_churn[df_churn.get('Status_Risco') == 'Alto']
        total_alto = len(alto_risco)
        mensagem = f"Alerta: {total_alto} laboratórios em ALTO RISCO."

        # Verificar se temos credenciais mínimas
        has_creds = all([
            'EMAIL_ALERTA' in globals() and EMAIL_ALERTA,
            'SMTP_SERVER' in globals() and SMTP_SERVER,
            'SMTP_PORT' in globals() and SMTP_PORT,
            'SMTP_USER' in globals() and SMTP_USER,
            'SMTP_PASSWORD' in globals() and SMTP_PASSWORD,
        ])

        if not has_creds:
            logger.info(f"[ALERTA-LOG] {mensagem} (e-mail desabilitado por falta de credenciais)")
            return

        import smtplib
        from email.mime.text import MIMEText

        body = "\n".join([
            mensagem,
            "",
            alto_risco.head(20)[['Nome_Fantasia_PCL','Estado','Cidade']].to_string(index=False) if not alto_risco.empty else "",
        ])
        msg = MIMEText(body, _charset='utf-8')
        msg['Subject'] = 'Alerta Churn - Labs em Alto Risco'
        msg['From'] = SMTP_USER
        msg['To'] = EMAIL_ALERTA

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [EMAIL_ALERTA], msg.as_string())
        logger.info("Alerta por e-mail enviado com sucesso.")
    except Exception as e:
        logger.warning(f"Falha ao enviar alerta por e-mail (ignorando): {e}")

if __name__ == "__main__":
    executar_gerador()
