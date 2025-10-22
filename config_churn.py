# ========================================
# CONFIGURAÇÕES DO SISTEMA CHURN PCLs
# ========================================

import os
import streamlit as st

def detectar_caminho_churn():
    """Detecta automaticamente o caminho do OneDrive para dados de churn."""
    caminhos_possiveis = [
        r"D:\OneDrive - Synvia Group\Data Analysis\Churn PCLs",
        r"C:\Users\washington.gouvea\OneDrive - Synvia Group\Data Analysis\Churn PCLs",
        r"C:\Users\%USERNAME%\OneDrive - Synvia Group\Data Analysis\Churn PCLs"
    ]
    
    # Expandir variável de ambiente %USERNAME% se presente
    for i, caminho in enumerate(caminhos_possiveis):
        if "%USERNAME%" in caminho:
            caminhos_possiveis[i] = caminho.replace("%USERNAME%", os.getenv('USERNAME', ''))
    
    # Verificar qual caminho existe
    for caminho in caminhos_possiveis:
        if os.path.exists(caminho):
            return caminho
    
    # Se nenhum caminho existir, usar o primeiro como padrão
    return caminhos_possiveis[0]

# Diretório de saída dos dados
if os.path.exists("/tmp/churn_data"):
    # Ambiente cloud
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', "/tmp/churn_data")
else:
    # Ambiente local - detectar OneDrive automaticamente
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', detectar_caminho_churn())

# Configurações do MongoDB (reutilizando do sistema CTOX)
# Tenta usar secrets do Streamlit primeiro, depois variáveis de ambiente, depois padrão
try:
    MONGODB_URI = st.secrets.get('mongodb_uri', os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
    MONGODB_DATABASE = st.secrets.get('mongodb_database', os.getenv('MONGODB_DATABASE', "database"))
except:
    # Fallback para quando não estiver no contexto do Streamlit
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', "database")

# Arquivos de saída
GATHERINGS_2024_FILE = "gatherings2024.csv"
GATHERINGS_2025_FILE = "gatherings2025.csv"
LABORATORIES_FILE = "laboratories.csv"
REPRESENTATIVES_FILE = "representatives.csv"
CHURN_ANALYSIS_FILE = "churn_analysis_latest.parquet"

# Critérios de churn
DIAS_INATIVO = int(os.getenv('DIAS_INATIVO', 90))  # Sem coletas = Inativo
DIAS_RISCO_ALTO = int(os.getenv('DIAS_RISCO_ALTO', 60))  # Alto risco
DIAS_RISCO_MEDIO = int(os.getenv('DIAS_RISCO_MEDIO', 15))  # Médio risco
REDUCAO_ALTO_RISCO = float(os.getenv('REDUCAO_ALTO_RISCO', 0.50))  # 50%
REDUCAO_MEDIO_RISCO = float(os.getenv('REDUCAO_MEDIO_RISCO', 0.30))  # 30%

# Configurações de tempo
INTERVALO_EXECUCAO = int(os.getenv('INTERVALO_EXECUCAO', 6))  # Horas entre execuções do gerador

# Configurações de log
LOG_FILE = os.getenv('LOG_FILE', "gerador_dados_churn.log")
LOG_LEVEL = os.getenv('LOG_LEVEL', "INFO")

# Configurações do Streamlit
STREAMLIT_PORT = int(os.getenv('STREAMLIT_PORT', 8502))  # Porta diferente do CTOX
STREAMLIT_HOST = os.getenv('STREAMLIT_HOST', "0.0.0.0")
CACHE_TTL = int(os.getenv('CACHE_TTL', 300))  # 5 minutos

# Configurações de arquivo
ENCODING = os.getenv('ENCODING', "utf-8-sig")
TIMESTAMP_FORMAT = os.getenv('TIMESTAMP_FORMAT', "%Y%m%d_%H%M%S")
DATETIME_FORMAT = os.getenv('DATETIME_FORMAT', "%d/%m/%Y %H:%M:%S")

# Fuso horário
TIMEZONE = os.getenv('TIMEZONE', "America/Sao_Paulo")

# Configurações de performance
BATCH_SIZE = int(os.getenv('BATCH_SIZE', 1000))  # Tamanho do lote para processamento
PROGRESS_INTERVAL = int(os.getenv('PROGRESS_INTERVAL', 10))  # Porcentagem para mostrar progresso

# Configurações de limpeza de arquivos antigos
DIAS_RETER_ARQUIVOS = int(os.getenv('DIAS_RETER_ARQUIVOS', 30))  # Dias para manter arquivos
MAX_ARQUIVOS_HISTORICO = int(os.getenv('MAX_ARQUIVOS_HISTORICO', 10))  # Máximo de arquivos por formato
FORMATOS_ARQUIVO = ['.parquet', '.csv', '.xlsx']  # Formatos de arquivo para limpeza
ARQUIVOS_PRESERVAR = ['churn_analysis_latest.parquet', 
                      'churn_analysis_latest.csv', 
                      'gatherings2024.csv',
                      'gatherings2025.csv',
                      'laboratories.csv',
                      'representatives.csv']  # Arquivos que nunca devem ser removidos

# ========================================
# DICIONÁRIO DE TRADUÇÕES PARA CHURN
# ========================================

# Traduções para status de risco
TRADUCOES_STATUS_RISCO = {
    'Alto': 'Alto Risco',
    'Médio': 'Médio Risco', 
    'Baixo': 'Baixo Risco',
    'Inativo': 'Inativo'
}

# Traduções para tendência
TRADUCOES_TENDENCIA = {
    'Crescimento': 'Crescimento',
    'Estável': 'Estável',
    'Declínio': 'Declínio'
}

# Categorias de risco para filtros
CATEGORIAS_RISCO = {
    'Alto Risco': ['Alto'],
    'Médio Risco': ['Médio'],
    'Baixo Risco': ['Baixo'],
    'Inativo': ['Inativo']
}

# Estados brasileiros para filtros
ESTADOS_BRASIL = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]

# Configurações de alertas
# Tenta usar secrets do Streamlit primeiro, depois variáveis de ambiente, depois padrão
try:
    EMAIL_ALERTA = st.secrets.get('email_alerta', os.getenv('EMAIL_ALERTA', 'seuemail@exemplo.com'))
    SMTP_SERVER = st.secrets.get('smtp_server', os.getenv('SMTP_SERVER', 'smtp.exemplo.com'))
    SMTP_PORT = int(st.secrets.get('smtp_port', os.getenv('SMTP_PORT', 587)))
    SMTP_USER = st.secrets.get('smtp_user', os.getenv('SMTP_USER', 'user'))
    SMTP_PASSWORD = st.secrets.get('smtp_password', os.getenv('SMTP_PASSWORD', 'pass'))
except:
    # Fallback para quando não estiver no contexto do Streamlit
    EMAIL_ALERTA = os.getenv('EMAIL_ALERTA', 'seuemail@exemplo.com')
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.exemplo.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER', 'user')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'pass')
ALERTA_THRESHOLD_ALTO = 5  # Número de labs em alto risco para enviar alerta

# Configurações para KPIs
DIAS_ATIVO_REcente_7 = 7
DIAS_ATIVO_REcente_30 = 30

# Configurações para dados VIP
VIP_EXCEL_FILE = "Matriz CS 2025 ATUAL.xlsx"
VIP_COLUMNS = ["CNPJ", "Ranking", "Ranking Rede", "Rede"]
VIP_CACHE_TTL = 300  # 5 minutos
