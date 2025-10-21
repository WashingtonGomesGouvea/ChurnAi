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
        "active": True,
        "test": False
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
        "active": True,
        "test": False
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
    """Extrai laboratories ativos com merge incremental."""
    logger.info("Iniciando extração de laboratories...")
    
    db = connect_mongodb()
    if db is None:
        return
    
    collections = get_collections(db)
    
    # Buscar laboratories ativos
    laboratories = list(collections["laboratories"].find({
        "active": True,
        "$or": [
            {"exclusionDate": {"$exists": False}},
            {"exclusionDate": None},
            {"exclusionDate": ""}
        ]
    }))
    
    logger.info(f"Encontrados {len(laboratories)} laboratories ativos")
    
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
    """Calcula métricas de churn para cada laboratório."""
    logger.info("Iniciando cálculo de métricas de churn...")
    
    # Carregar dados
    df_gatherings_2024, df_gatherings_2025, df_laboratories, df_representatives = carregar_dados_csv()
    
    if df_laboratories.empty:
        logger.warning("Nenhum laboratory encontrado para análise")
        return
    
    # Criar dicionários para relacionamentos
    representatives_dict = {row['_id']: row for _, row in df_representatives.iterrows()}
    
    # Processar cada laboratório
    dados_churn = []
    
    for _, lab in df_laboratories.iterrows():
        lab_id = lab['_id']
        
        # Buscar gatherings do laboratório
        gatherings_2024_lab = df_gatherings_2024[df_gatherings_2024['_laboratory'] == lab_id] if not df_gatherings_2024.empty else pd.DataFrame()
        gatherings_2025_lab = df_gatherings_2025[df_gatherings_2025['_laboratory'] == lab_id] if not df_gatherings_2025.empty else pd.DataFrame()
        
        # Calcular métricas básicas
        total_coletas_2024 = len(gatherings_2024_lab)
        total_coletas_2025 = len(gatherings_2025_lab)
        
        # Calcular coletas por mês 2025
        coletas_mensais_2025 = {}
        if not gatherings_2025_lab.empty:
            # Criar cópia para evitar SettingWithCopyWarning
            gatherings_2025_lab = gatherings_2025_lab.copy()
            
            # Converter createdAt para datetime com tratamento de erros
            try:
                gatherings_2025_lab['createdAt'] = pd.to_datetime(gatherings_2025_lab['createdAt'], errors='coerce')
            except Exception as e:
                logger.warning(f"Erro ao converter datas: {e}")
                gatherings_2025_lab['createdAt'] = pd.to_datetime(gatherings_2025_lab['createdAt'], format='mixed', errors='coerce')
            
            for mes in range(1, 11):  # Jan a Out
                mes_key = f'N_Coletas_{["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out"][mes-1]}_25'
                coletas_mes = len(gatherings_2025_lab[gatherings_2025_lab['createdAt'].dt.month == mes])
                coletas_mensais_2025[mes_key] = coletas_mes
        
        # Calcular maior mês histórico (2024)
        maior_mes_2024 = 0
        mes_historico = ""
        if not gatherings_2024_lab.empty:
            # Criar cópia para evitar SettingWithCopyWarning
            gatherings_2024_lab = gatherings_2024_lab.copy()
            
            # Converter createdAt para datetime com tratamento de erros
            try:
                gatherings_2024_lab['createdAt'] = pd.to_datetime(gatherings_2024_lab['createdAt'], errors='coerce')
            except Exception as e:
                logger.warning(f"Erro ao converter datas 2024: {e}")
                gatherings_2024_lab['createdAt'] = pd.to_datetime(gatherings_2024_lab['createdAt'], format='mixed', errors='coerce')
            
            coletas_por_mes_2024 = gatherings_2024_lab.groupby(gatherings_2024_lab['createdAt'].dt.month).size()
            if not coletas_por_mes_2024.empty:
                maior_mes_2024 = coletas_por_mes_2024.max()
                mes_idx = coletas_por_mes_2024.idxmax()
                meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
                mes_historico = f"{meses[mes_idx-1]}/2024"
        
        # Calcular maior mês 2025
        maior_mes_2025 = max(coletas_mensais_2025.values()) if coletas_mensais_2025 else 0
        
        # Calcular data da última coleta
        data_ultima_coleta = None
        if not gatherings_2025_lab.empty:
            # Usar a coluna createdAt já convertida
            data_ultima_coleta = gatherings_2025_lab['createdAt'].max()
        
        # Calcular dias sem coleta
        dias_sem_coleta = 0
        if data_ultima_coleta is not None and pd.notna(data_ultima_coleta):
            agora = datetime.now()
            if isinstance(data_ultima_coleta, str):
                data_ultima_coleta = pd.to_datetime(data_ultima_coleta, errors='coerce')
            if pd.notna(data_ultima_coleta):
                # Garantir que ambos os timestamps tenham o mesmo timezone
                if data_ultima_coleta.tzinfo is not None and agora.tzinfo is None:
                    agora = agora.replace(tzinfo=data_ultima_coleta.tzinfo)
                elif data_ultima_coleta.tzinfo is None and agora.tzinfo is not None:
                    data_ultima_coleta = data_ultima_coleta.replace(tzinfo=agora.tzinfo)
                elif data_ultima_coleta.tzinfo is None and agora.tzinfo is None:
                    # Ambos sem timezone, OK
                    pass
                else:
                    # Ambos com timezone, converter para o mesmo
                    if data_ultima_coleta.tzinfo != agora.tzinfo:
                        data_ultima_coleta = data_ultima_coleta.tz_convert(agora.tzinfo)
                
                dias_sem_coleta = (agora - data_ultima_coleta).days
        
        # Calcular médias mensais
        media_mensal_2024 = total_coletas_2024 / 12 if total_coletas_2024 > 0 else 0
        media_mensal_2025 = total_coletas_2025 / 10 if total_coletas_2025 > 0 else 0  # Jan a Out
        
        # Calcular variação percentual
        variacao_percentual = 0
        if media_mensal_2024 > 0:
            variacao_percentual = ((media_mensal_2025 - media_mensal_2024) / media_mensal_2024) * 100
        
        # Determinar tendência
        if variacao_percentual > 10:
            tendencia = "Crescimento"
        elif variacao_percentual < -10:
            tendencia = "Declínio"
        else:
            tendencia = "Estável"
        
        # Determinar status de risco
        status_risco = "Baixo"
        motivo_risco = "Volume estável"
        
        if dias_sem_coleta >= DIAS_INATIVO:
            status_risco = "Inativo"
            motivo_risco = f"Sem coletas há {dias_sem_coleta} dias"
        elif dias_sem_coleta >= DIAS_RISCO_ALTO:
            status_risco = "Alto"
            motivo_risco = f"Sem coletas há {dias_sem_coleta} dias"
        elif dias_sem_coleta >= DIAS_RISCO_MEDIO:
            status_risco = "Médio"
            motivo_risco = f"Sem coletas há {dias_sem_coleta} dias"
        elif variacao_percentual <= -REDUCAO_ALTO_RISCO * 100:
            status_risco = "Alto"
            motivo_risco = f"Redução de {abs(variacao_percentual):.1f}% vs 2024"
        elif variacao_percentual <= -REDUCAO_MEDIO_RISCO * 100:
            status_risco = "Médio"
            motivo_risco = f"Redução de {abs(variacao_percentual):.1f}% vs 2024"
        
        # Obter dados do representante
        rep_id = lab.get('_representative', '')
        rep_data = representatives_dict.get(rep_id, {})
        
        # Criar registro de churn
        registro_churn = {
            'CNPJ_PCL': lab.get('cnpj', ''),
            'Razao_Social_PCL': lab.get('legalName', ''),
            'Nome_Fantasia_PCL': lab.get('fantasyName', ''),
            'Estado': lab.get('address', {}).get('state', {}).get('code', '') if isinstance(lab.get('address'), dict) else '',
            'Cidade': lab.get('address', {}).get('city', '') if isinstance(lab.get('address'), dict) else '',
            'Representante_Nome': rep_data.get('name', ''),
            'Representante_ID': rep_id,
            
            # Métricas históricas
            'Maior_N_Coletas_Mes_Historico': maior_mes_2024,
            'Mes_Historico': mes_historico,
            'Maior_N_Coletas_Mes_2024': maior_mes_2024,
            'Maior_N_Coletas_Mes_2025': maior_mes_2025,
            
            # Coletas mensais 2025
            'N_Coletas_Jan_25': coletas_mensais_2025.get('N_Coletas_Jan_25', 0),
            'N_Coletas_Fev_25': coletas_mensais_2025.get('N_Coletas_Fev_25', 0),
            'N_Coletas_Mar_25': coletas_mensais_2025.get('N_Coletas_Mar_25', 0),
            'N_Coletas_Abr_25': coletas_mensais_2025.get('N_Coletas_Abr_25', 0),
            'N_Coletas_Mai_25': coletas_mensais_2025.get('N_Coletas_Mai_25', 0),
            'N_Coletas_Jun_25': coletas_mensais_2025.get('N_Coletas_Jun_25', 0),
            'N_Coletas_Jul_25': coletas_mensais_2025.get('N_Coletas_Jul_25', 0),
            'N_Coletas_Ago_25': coletas_mensais_2025.get('N_Coletas_Ago_25', 0),
            'N_Coletas_Set_25': coletas_mensais_2025.get('N_Coletas_Set_25', 0),
            'N_Coletas_Out_25': coletas_mensais_2025.get('N_Coletas_Out_25', 0),
            
            # Análise de churn
            'Data_Ultima_Coleta': data_ultima_coleta,
            'Dias_Sem_Coleta': dias_sem_coleta,
            'Media_Coletas_Mensal_2024': round(media_mensal_2024, 2),
            'Media_Coletas_Mensal_2025': round(media_mensal_2025, 2),
            'Variacao_Percentual': round(variacao_percentual, 2),
            'Tendencia': tendencia,
            
            # Status de risco
            'Status_Risco': status_risco,
            'Motivo_Risco': motivo_risco,
            
            # Metadados
            'Data_Analise': datetime.now(),
            'Total_Coletas_2024': total_coletas_2024,
            'Total_Coletas_2025': total_coletas_2025
        }
        
        dados_churn.append(registro_churn)
    
    # Criar DataFrame final
    df_churn = pd.DataFrame(dados_churn)
    logger.info(f"Análise de churn concluída: {len(df_churn)} laboratórios processados")
    
    # Salvar análise
    if not df_churn.empty:
        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
        
        # Salvar com timestamp
        arquivo_timestamp = os.path.join(OUTPUT_DIR, f"churn_analysis_{timestamp}.parquet")
        df_churn.to_parquet(arquivo_timestamp, engine='pyarrow', compression='snappy', index=False)
        
        # Salvar latest
        arquivo_latest = os.path.join(OUTPUT_DIR, CHURN_ANALYSIS_FILE)
        df_churn.to_parquet(arquivo_latest, engine='pyarrow', compression='snappy', index=False)
        
        # Salvar CSV backup
        arquivo_csv = os.path.join(OUTPUT_DIR, "churn_analysis_latest.csv")
        df_churn.to_csv(arquivo_csv, index=False, encoding=ENCODING)
        
        logger.info(f"Análise de churn salva: {arquivo_latest}")
        
        # Estatísticas resumidas
        status_counts = df_churn['Status_Risco'].value_counts()
        logger.info(f"Distribuição de risco: {dict(status_counts)}")
        # Enviar alerta se necessário
        if 'Alto' in status_counts and status_counts['Alto'] >= ALERTA_THRESHOLD_ALTO:
            enviar_alerta_email(df_churn)
    else:
        logger.warning("Nenhum dado de churn gerado")

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

if __name__ == "__main__":
    executar_gerador()
