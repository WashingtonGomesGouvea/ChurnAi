# ========================================
# GERENCIADOR DE ALERTAS
# Sistema de Alertas Churn v2
# ========================================

"""
Módulo para gerenciamento de alertas de churn com sistema de priorização
e cap de alertas diários baseado em critérios de risco (queda e dias sem coleta).
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import logging

# Importar configurações
from config_churn import (
    ALERTA_CAP_MIN,
    ALERTA_CAP_MAX,
    ALERTA_CAP_DEFAULT
)

# Configurar logger
logger = logging.getLogger(__name__)


# ========================================
# APLICAÇÃO DE CAP DE ALERTAS
# ========================================

def aplicar_cap_alertas(df_alertas: pd.DataFrame, 
                       cap: int = ALERTA_CAP_DEFAULT) -> pd.DataFrame:
    """
    Limita alertas aos top N mais críticos (alert budget) usando critérios de risco.
    
    Args:
        df_alertas: DataFrame com alertas
        cap: Número máximo de alertas a retornar
        coluna_severidade: Nome da coluna com severidade
        
    Returns:
        DataFrame filtrado com top N alertas mais severos
    """
    if df_alertas.empty:
        return df_alertas
    
    df_ord = df_alertas.copy()
    risco_series = df_ord['Risco_Por_Dias_Sem_Coleta'] if 'Risco_Por_Dias_Sem_Coleta' in df_ord.columns else pd.Series(False, index=df_ord.index)
    risco_series = risco_series.fillna(False).astype(bool)
    concorrencia_series = df_ord['Apareceu_Gralab'] if 'Apareceu_Gralab' in df_ord.columns else pd.Series(False, index=df_ord.index)
    concorrencia_series = concorrencia_series.fillna(False).astype(bool)
    df_ord['prioridade_score'] = (risco_series.astype(int) * 5) + (concorrencia_series.astype(int) * 3)
    df_ord['abs_queda_baseline'] = df_ord.get('Queda_Baseline_Pct', pd.Series(0, index=df_ord.index)).fillna(0).abs()
    df_ord['abs_wow'] = df_ord.get('WoW_Percentual', pd.Series(0, index=df_ord.index)).fillna(0).abs()
    df_ord['baseline_volume'] = df_ord.get('Baseline_Mensal', pd.Series(0, index=df_ord.index)).fillna(0)
    df_ord['dias_sem_coleta'] = df_ord.get('Dias_Sem_Coleta', pd.Series(0, index=df_ord.index)).fillna(0)
    
    df_ord = df_ord.sort_values(
        by=['prioridade_score', 'abs_queda_baseline', 'abs_wow', 'baseline_volume', 'dias_sem_coleta'],
        ascending=[False, False, False, False, False]
    )
    df_top = df_ord.head(cap).copy()
    
    # Adicionar rank de prioridade
    df_top['Rank_Prioridade'] = range(1, len(df_top) + 1)
    df_top = df_top.drop(columns=['prioridade_score', 'abs_queda_baseline', 'abs_wow', 'baseline_volume', 'dias_sem_coleta'], errors='ignore')
    
    logger.info(f"Cap de alertas aplicado: {len(df_ord)} → {len(df_top)} (cap={cap})")
    
    return df_top


def validar_cap(cap: int) -> int:
    """
    Valida e ajusta o cap de alertas dentro dos limites permitidos.
    
    Args:
        cap: Cap solicitado
        
    Returns:
        Cap validado (dentro de ALERTA_CAP_MIN e ALERTA_CAP_MAX)
    """
    if cap < ALERTA_CAP_MIN:
        logger.warning(f"Cap {cap} abaixo do mínimo ({ALERTA_CAP_MIN}). Ajustando.")
        return ALERTA_CAP_MIN
    
    if cap > ALERTA_CAP_MAX:
        logger.warning(f"Cap {cap} acima do máximo ({ALERTA_CAP_MAX}). Ajustando.")
        return ALERTA_CAP_MAX
    
    return cap


# ========================================
# PROCESSAMENTO POR UF
# ========================================

def processar_alertas_por_uf(df_churn: pd.DataFrame,
                             cap_global: int = ALERTA_CAP_DEFAULT,
                             coluna_uf: str = 'Estado',
                             coluna_risco: str = 'Status_Risco_V2') -> Dict[str, pd.DataFrame]:
    """
    Gera alertas segmentados por UF com cap proporcional.
    
    Args:
        df_churn: DataFrame com dados de churn
        cap_global: Cap global de alertas
        coluna_uf: Nome da coluna com UF
        coluna_risco: Nome da coluna com status de risco
        
    Returns:
        Dicionário com UF como chave e DataFrame de alertas como valor
    """
    if df_churn.empty:
        return {}
    
    if coluna_uf not in df_churn.columns:
        logger.error(f"Coluna '{coluna_uf}' não encontrada no DataFrame")
        return {}
    
    if coluna_risco not in df_churn.columns:
        logger.error(f"Coluna '{coluna_risco}' não encontrada no DataFrame")
        return {}
    
    alertas_por_uf = {}
    
    # Filtrar apenas alertas de risco alto
    df_alto_risco = df_churn[df_churn[coluna_risco] == 'Perda (Risco Alto)'].copy()
    
    if df_alto_risco.empty:
        logger.info("Nenhum alerta de risco alto encontrado")
        return {}
    
    # FILTRO ADICIONAL: Garantir que apenas labs com coletas recentes sejam processados
    # Excluir labs sem coletas em 2025 ou com muitos dias sem coleta
    if 'Total_Coletas_2025' in df_alto_risco.columns:
        df_alto_risco['Total_Coletas_2025'] = pd.to_numeric(
            df_alto_risco['Total_Coletas_2025'], errors='coerce'
        ).fillna(0).astype(int)
        df_alto_risco = df_alto_risco[df_alto_risco['Total_Coletas_2025'] > 0].copy()
    
    # Filtrar labs com muitos dias sem coleta (>90 dias)
    if 'Dias_Sem_Coleta' in df_alto_risco.columns:
        df_alto_risco['Dias_Sem_Coleta'] = pd.to_numeric(
            df_alto_risco['Dias_Sem_Coleta'], errors='coerce'
        ).fillna(0).astype(int)
        df_alto_risco = df_alto_risco[df_alto_risco['Dias_Sem_Coleta'] <= 90].copy()
    
    if df_alto_risco.empty:
        logger.info("Nenhum alerta de risco alto encontrado após filtros de coletas recentes")
        return {}
    
    total_alertas = len(df_alto_risco)
    
    # Processar cada UF
    for uf in df_alto_risco[coluna_uf].unique():
        if pd.isna(uf) or uf == '':
            continue
        
        df_uf = df_alto_risco[df_alto_risco[coluna_uf] == uf].copy()
        
        if df_uf.empty:
            continue
        
        # Calcular cap proporcional para a UF
        proporcao = len(df_uf) / total_alertas
        cap_uf = max(2, int(cap_global * proporcao))  # Mínimo 2 alertas por UF
        cap_uf = min(cap_uf, len(df_uf))  # Não pode exceder alertas disponíveis
        
        # Aplicar cap
        alertas_uf = aplicar_cap_alertas(df_uf, cap=cap_uf)
        alertas_por_uf[uf] = alertas_uf
        
        logger.info(f"UF {uf}: {len(df_uf)} alertas → {len(alertas_uf)} após cap")
    
    return alertas_por_uf


def consolidar_alertas_ufs(alertas_por_uf: Dict[str, pd.DataFrame],
                           cap_global: Optional[int] = None) -> pd.DataFrame:
    """
    Consolida alertas de todas as UFs em um único DataFrame.
    
    Args:
        alertas_por_uf: Dicionário com alertas por UF
        cap_global: Cap global opcional para aplicar após consolidação
        
    Returns:
        DataFrame consolidado com todos os alertas
    """
    if not alertas_por_uf:
        return pd.DataFrame()
    
    # Concatenar todos os DataFrames
    df_consolidado = pd.concat(alertas_por_uf.values(), ignore_index=True)
    
    # Aplicar cap global se fornecido
    if cap_global is not None:
        cap_validado = validar_cap(cap_global)
        df_consolidado = aplicar_cap_alertas(df_consolidado, cap=cap_validado)
    
    return df_consolidado


# ========================================
# RELATÓRIOS E ESTATÍSTICAS
# ========================================

def gerar_relatorio_alertas(df_alertas: pd.DataFrame) -> Dict[str, any]:
    """
    Gera relatório estatístico sobre os alertas.
    
    Args:
        df_alertas: DataFrame com alertas
        
    Returns:
        Dicionário com estatísticas
    """
    if df_alertas.empty:
        return {
            'total_alertas': 0,
            'com_concorrente': 0,
            'por_uf': {}
        }
    
    relatorio = {
        'total_alertas': len(df_alertas),
        'data_geracao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Alertas com sinal de concorrente
    if 'Apareceu_Gralab' in df_alertas.columns:
        relatorio['com_concorrente'] = int(df_alertas['Apareceu_Gralab'].sum())
        relatorio['pct_com_concorrente'] = round(
            relatorio['com_concorrente'] / len(df_alertas) * 100, 2
        )
    
    # Distribuição por UF
    if 'Estado' in df_alertas.columns:
        distribuicao_uf = df_alertas['Estado'].value_counts().to_dict()
        relatorio['por_uf'] = distribuicao_uf
        relatorio['ufs_afetadas'] = len(distribuicao_uf)
    
    # Distribuição por porte
    if 'Porte' in df_alertas.columns:
        distribuicao_porte = df_alertas['Porte'].value_counts().to_dict()
        relatorio['por_porte'] = distribuicao_porte
    
    # Motivos principais
    if 'Motivo_Risco_V2' in df_alertas.columns:
        top_motivos = df_alertas['Motivo_Risco_V2'].value_counts().head(5).to_dict()
        relatorio['top_motivos'] = top_motivos
    
    return relatorio


def formatar_relatorio_texto(relatorio: Dict) -> str:
    """
    Formata relatório de alertas em texto legível.
    
    Args:
        relatorio: Dicionário com estatísticas
        
    Returns:
        String formatada com o relatório
    """
    if relatorio['total_alertas'] == 0:
        return "Nenhum alerta de risco alto identificado."
    
    texto = []
    texto.append("=" * 60)
    texto.append("RELATÓRIO DE ALERTAS DE CHURN")
    texto.append("=" * 60)
    texto.append(f"\nData: {relatorio.get('data_geracao', 'N/A')}")
    texto.append(f"Total de Alertas: {relatorio['total_alertas']}")
    
    if 'com_concorrente' in relatorio:
        texto.append(f"\nSinal de Concorrência:")
        texto.append(f"  {relatorio['com_concorrente']} alertas "
                    f"({relatorio.get('pct_com_concorrente', 0)}%) "
                    f"com aparição no Gralab")
    
    if 'por_uf' in relatorio and relatorio['por_uf']:
        texto.append(f"\nDistribuição por UF ({relatorio.get('ufs_afetadas', 0)} UFs):")
        for uf, count in sorted(relatorio['por_uf'].items(), 
                               key=lambda x: x[1], reverse=True)[:10]:
            texto.append(f"  {uf}: {count} alertas")
    
    if 'por_porte' in relatorio and relatorio['por_porte']:
        texto.append(f"\nDistribuição por Porte:")
        for porte, count in relatorio['por_porte'].items():
            texto.append(f"  {porte}: {count} alertas")
    
    texto.append("\n" + "=" * 60)
    
    return "\n".join(texto)


# ========================================
# EXPORTAÇÃO DE ALERTAS
# ========================================

def exportar_alertas_csv(df_alertas: pd.DataFrame, 
                        arquivo: str,
                        incluir_timestamp: bool = True) -> str:
    """
    Exporta alertas para CSV.
    
    Args:
        df_alertas: DataFrame com alertas
        arquivo: Nome do arquivo (sem extensão)
        incluir_timestamp: Se deve incluir timestamp no nome
        
    Returns:
        Caminho do arquivo gerado
    """
    if incluir_timestamp:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        arquivo_final = f"{arquivo}_{timestamp}.csv"
    else:
        arquivo_final = f"{arquivo}.csv"
    
    df_alertas.to_csv(arquivo_final, index=False, encoding='utf-8-sig')
    logger.info(f"Alertas exportados para: {arquivo_final}")
    
    return arquivo_final


def exportar_alertas_por_uf(alertas_por_uf: Dict[str, pd.DataFrame],
                            diretorio: str = "alertas_uf",
                            timestamp: Optional[str] = None) -> List[str]:
    """
    Exporta alertas de cada UF para arquivos separados.
    
    Args:
        alertas_por_uf: Dicionário com alertas por UF
        diretorio: Diretório onde salvar os arquivos
        timestamp: Timestamp opcional para incluir nos nomes
        
    Returns:
        Lista de caminhos dos arquivos gerados
    """
    import os
    
    # Criar diretório se não existir
    os.makedirs(diretorio, exist_ok=True)
    
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    arquivos_gerados = []
    
    for uf, df_alertas in alertas_por_uf.items():
        if df_alertas.empty:
            continue
        
        arquivo = os.path.join(diretorio, f"alertas_{uf}_{timestamp}.csv")
        df_alertas.to_csv(arquivo, index=False, encoding='utf-8-sig')
        arquivos_gerados.append(arquivo)
        logger.info(f"Alertas de {uf} exportados para: {arquivo}")
    
    return arquivos_gerados


# ========================================
# TESTE DO MÓDULO
# ========================================

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DO MÓDULO DE ALERTAS")
    print("=" * 60)
    
    # Criar dados de teste
    np.random.seed(42)
    df_teste = pd.DataFrame({
        'Lab': [f'Lab_{i}' for i in range(1, 101)],
        'Estado': np.random.choice(['SP', 'RJ', 'MG', 'RS', 'BA'], 100),
        'Queda_Baseline_Pct': np.random.uniform(10, 90, 100),
        'WoW_Percentual': np.random.uniform(-80, -20, 100),
        'Baseline_Mensal': np.random.uniform(50, 300, 100),
        'Dias_Sem_Coleta': np.random.randint(0, 10, 100),
        'Apareceu_Gralab': np.random.choice([True, False], 100, p=[0.2, 0.8]),
        'Porte': np.random.choice(['Grande', 'Médio', 'Pequeno'], 100),
        'Status_Risco_V2': 'Perda (Risco Alto)'
    })
    
    # Teste 1: Aplicar cap
    print("\n1. Aplicação de Cap:")
    df_cap = aplicar_cap_alertas(df_teste, cap=30)
    print(f"Alertas após cap: {len(df_cap)}")
    
    # Teste 2: Processar por UF
    print("\n2. Processamento por UF:")
    alertas_uf = processar_alertas_por_uf(df_teste, cap_global=40)
    for uf, df_uf in alertas_uf.items():
        print(f"  {uf}: {len(df_uf)} alertas")
    
    # Teste 3: Relatório
    print("\n3. Relatório de Alertas:")
    relatorio = gerar_relatorio_alertas(df_cap)
    print(formatar_relatorio_texto(relatorio))
    
    print("\n" + "=" * 60)
    print("TESTES CONCLUÍDOS")
    print("=" * 60)

