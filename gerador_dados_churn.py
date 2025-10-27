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
        "representatives": db["representatives"]
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

def carregar_dados_csv() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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
        
        return df_gatherings_2024, df_gatherings_2025, df_laboratories, df_representatives
        
    except Exception as e:
        logger.error(f"Erro ao carregar dados CSV: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def calcular_metricas_churn():
    """Calcula métricas de churn com agregações vetorizadas (rápidas)."""
    logger.info("Iniciando cálculo de métricas de churn...")
    
    df_gatherings_2024, df_gatherings_2025, df_laboratories, df_representatives = carregar_dados_csv()
    
    if df_laboratories.empty:
        logger.warning("Nenhum laboratory encontrado para análise")
        return
    
    # Padronizar tipos de IDs
    def to_str_series(s: pd.Series) -> pd.Series:
        return s.astype(str).fillna("") if s is not None and len(s) else pd.Series(dtype=str)

    if '_id' in df_laboratories.columns:
        df_laboratories['_id'] = to_str_series(df_laboratories['_id'])
    if '_representative' in df_laboratories.columns:
        df_laboratories['_representative'] = to_str_series(df_laboratories['_representative'])

    if not df_representatives.empty and '_id' in df_representatives.columns:
        df_representatives['_id'] = to_str_series(df_representatives['_id'])

    # Preparar gatherings 2024
    meses_nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    mes_limite_2025 = min(datetime.now().month, 12)

    if not df_gatherings_2024.empty:
        df_gatherings_2024 = df_gatherings_2024.copy()
        if '_laboratory' in df_gatherings_2024.columns:
            df_gatherings_2024['_laboratory'] = to_str_series(df_gatherings_2024['_laboratory'])
        df_gatherings_2024['createdAt'] = pd.to_datetime(df_gatherings_2024.get('createdAt'), errors='coerce', utc=True)
        df_gatherings_2024['mes'] = df_gatherings_2024['createdAt'].dt.month

        total_2024 = df_gatherings_2024.groupby('_laboratory').size().rename('Total_Coletas_2024')
        m2024 = df_gatherings_2024.groupby(['_laboratory', 'mes']).size().unstack(fill_value=0)
    else:
        total_2024 = pd.Series(dtype=int)
        m2024 = pd.DataFrame()

    # Preparar gatherings 2025
    if not df_gatherings_2025.empty:
        df_gatherings_2025 = df_gatherings_2025.copy()
        if '_laboratory' in df_gatherings_2025.columns:
            df_gatherings_2025['_laboratory'] = to_str_series(df_gatherings_2025['_laboratory'])
        df_gatherings_2025['createdAt'] = pd.to_datetime(df_gatherings_2025.get('createdAt'), errors='coerce', utc=True)
        df_gatherings_2025['mes'] = df_gatherings_2025['createdAt'].dt.month

        total_2025 = df_gatherings_2025.groupby('_laboratory').size().rename('Total_Coletas_2025')
        ultima_2025 = df_gatherings_2025.groupby('_laboratory')['createdAt'].max().rename('Data_Ultima_Coleta')
        m2025 = df_gatherings_2025.groupby(['_laboratory', 'mes']).size().unstack(fill_value=0)
    else:
        total_2025 = pd.Series(dtype=int)
        ultima_2025 = pd.Series(dtype='datetime64[ns]')
        m2025 = pd.DataFrame()

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

    # Meses 2025 (até mês atual)
    for mes in range(1, mes_limite_2025 + 1):
        col = f'N_Coletas_{meses_nomes[mes-1]}_25'
        base[col] = m2025.get(mes, pd.Series(0, index=base.index)).reindex(base.index).fillna(0).astype(int)

    # Totais e últimas datas
    base['Total_Coletas_2024'] = total_2024.reindex(base.index).fillna(0).astype(int)
    base['Total_Coletas_2025'] = total_2025.reindex(base.index).fillna(0).astype(int)
    base['Data_Ultima_Coleta'] = ultima_2025.reindex(base.index)

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
    base['CNPJ_PCL'] = df_laboratories.set_index('_id').reindex(base.index).get('cnpj') if 'cnpj' in df_laboratories.columns else ''
    base['Razao_Social_PCL'] = df_laboratories.set_index('_id').reindex(base.index).get('legalName') if 'legalName' in df_laboratories.columns else ''
    base['Nome_Fantasia_PCL'] = df_laboratories.set_index('_id').reindex(base.index).get('fantasyName') if 'fantasyName' in df_laboratories.columns else ''
    base['Estado'] = df_laboratories.set_index('_id').reindex(base.index).get('address.state.code') if 'address.state.code' in df_laboratories.columns else ''
    base['Cidade'] = df_laboratories.set_index('_id').reindex(base.index).get('address.city') if 'address.city' in df_laboratories.columns else ''
            
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
    cols_fim = [
        'Data_Ultima_Coleta','Dias_Sem_Coleta','Media_Coletas_Mensal_2024','Media_Coletas_Mensal_2025',
        'Variacao_Percentual','Tendencia','Status_Risco','Motivo_Risco','Data_Analise',
        'Total_Coletas_2024','Total_Coletas_2025'
    ]

    # Garantir colunas existentes
    for c in cols_inicio + cols_2024 + cols_2025 + cols_fim:
        if c not in base.columns:
            base[c] = '' if c in ['CNPJ_PCL','Razao_Social_PCL','Nome_Fantasia_PCL','Estado','Cidade','Representante_Nome','Representante_ID','Mes_Historico','Tendencia','Status_Risco','Motivo_Risco'] else 0

    df_churn = base[cols_inicio + cols_2024 + cols_2025 + cols_fim].reset_index(drop=False)
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
