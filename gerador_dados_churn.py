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
    else:
        base['Maior_N_Coletas_Mes_2025'] = 0

    # Dias sem coleta
    # Normalizar timezone: manter tudo em UTC tz-aware para cálculo
    base['Data_Ultima_Coleta'] = pd.to_datetime(base['Data_Ultima_Coleta'], errors='coerce', utc=True)
    now_dt = pd.Timestamp.now(tz='UTC')
    base['Dias_Sem_Coleta'] = (now_dt - base['Data_Ultima_Coleta']).dt.days
    base.loc[base['Data_Ultima_Coleta'].isna(), 'Dias_Sem_Coleta'] = 0
    base['Dias_Sem_Coleta'] = base['Dias_Sem_Coleta'].astype(int)

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
        'Voucher_Commission','Data_Preco_Atualizacao','Dados_Diarios_2025','Dados_Semanais_2025'
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
