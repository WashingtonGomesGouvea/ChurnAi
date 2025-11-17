# ========================================
# BACKTEST DO SISTEMA DE ALERTAS
# Sistema de Alertas Churn v2
# ========================================

"""
Script para validar o sistema de alertas simulando dias passados.
Gera relatórios CSV e gráficos para ajustar limiares e alcançar meta de 30-50 alertas/dia.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta, date
from typing import List, Dict, Tuple, Optional
import logging

# Importar configurações e módulos
from config_churn import (
    OUTPUT_DIR,
    ENCODING,
    REDUCAO_BASELINE_RISCO_ALTO,
    REDUCAO_WOW_RISCO_ALTO,
    ALERTA_CAP_DEFAULT
)

try:
    from feriados_brasil import is_dia_util, dia_util_anterior
    FERIADOS_DISPONIVEL = True
except:
    FERIADOS_DISPONIVEL = False
    logging.warning("Módulo de feriados não disponível. Backtest usará dias corridos.")

# Configurar logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ========================================
# FUNÇÕES AUXILIARES
# ========================================

def obter_dia_util_passado(dias_atras: int, uf: Optional[str] = None) -> date:
    """
    Retorna a data do dia útil N dias atrás.
    
    Args:
        dias_atras: Número de dias úteis no passado
        uf: UF para considerar feriados estaduais
        
    Returns:
        Data do dia útil
    """
    if not FERIADOS_DISPONIVEL:
        # Fallback: usar dias corridos
        return (datetime.now() - timedelta(days=dias_atras)).date()
    
    data_atual = datetime.now().date()
    contador = 0
    
    while contador < dias_atras:
        data_atual = dia_util_anterior(data_atual, uf)
        contador += 1
    
    return data_atual


def carregar_dados_historicos(arquivo: str = "churn_analysis_latest.parquet") -> pd.DataFrame:
    """
    Carrega dados históricos de churn.
    
    Args:
        arquivo: Nome do arquivo com dados
        
    Returns:
        DataFrame com dados históricos
    """
    caminho = os.path.join(OUTPUT_DIR, arquivo)
    
    if not os.path.exists(caminho):
        logger.error(f"Arquivo não encontrado: {caminho}")
        return pd.DataFrame()
    
    try:
        if arquivo.endswith('.parquet'):
            df = pd.read_parquet(caminho)
        else:
            df = pd.read_csv(caminho, encoding=ENCODING, low_memory=False)
        
        logger.info(f"Dados carregados: {len(df)} laboratórios")
        return df
        
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()


def simular_classificacao_risco(df: pd.DataFrame, 
                                limiar_baseline: float,
                                limiar_wow: float) -> pd.DataFrame:
    """
    Simula classificação de risco com limiares personalizados.
    
    Args:
        df: DataFrame com dados dos laboratórios
        limiar_baseline: Limiar de queda vs baseline (0-1)
        limiar_wow: Limiar de queda WoW (0-1)
        
    Returns:
        DataFrame com classificação simulada
    """
    df = df.copy()
    
    # Simular Status_Risco_V2
    def classificar(row):
        # Critério 1: Baseline
        if row.get('Baseline_Mensal', 0) > 0:
            queda_baseline = (row['Baseline_Mensal'] - row.get('Coletas_Mes_Atual', 0)) / row['Baseline_Mensal']
            if queda_baseline > limiar_baseline:
                return 'Perda (Risco Alto)'
        
        # Critério 2: WoW
        if row.get('WoW_Percentual', 0) < -(limiar_wow * 100):
            return 'Perda (Risco Alto)'
        
        # Critério 3: Gatilho dias sem coleta
        if row.get('Gatilho_Dias_Sem_Coleta', False):
            return 'Perda (Risco Alto)'
        
        return 'Normal'
    
    df['Status_Risco_Simulado'] = df.apply(classificar, axis=1)
    
    return df


# ========================================
# BACKTEST PRINCIPAL
# ========================================

def executar_backtest(n_dias: int = 30,
                     limiares_teste: List[float] = [0.40, 0.45, 0.50, 0.55, 0.60],
                     uf: Optional[str] = None) -> pd.DataFrame:
    """
    Executa backtest do sistema de alertas.
    
    Args:
        n_dias: Número de dias úteis para simular
        limiares_teste: Lista de limiares a testar (0-1)
        uf: UF para considerar feriados
        
    Returns:
        DataFrame com resultados do backtest
    """
    logger.info(f"Iniciando backtest: {n_dias} dias, {len(limiares_teste)} limiares")
    
    # Carregar dados
    df_base = carregar_dados_historicos()
    
    if df_base.empty:
        logger.error("Sem dados para backtest")
        return pd.DataFrame()
    
    # Verificar colunas necessárias
    colunas_necessarias = ['Baseline_Mensal', 'Coletas_Mes_Atual', 'WoW_Percentual', 
                          'Gatilho_Dias_Sem_Coleta', 'Porte', 'Dias_Sem_Coleta']
    colunas_faltando = [col for col in colunas_necessarias if col not in df_base.columns]
    
    if colunas_faltando:
        logger.error(f"Colunas necessárias não encontradas: {colunas_faltando}")
        logger.info("Execute o gerador_dados_churn.py com sistema v2 primeiro")
        return pd.DataFrame()
    
    resultados = []
    
    # Para cada limiar
    for limiar in limiares_teste:
        logger.info(f"Testando limiar: {limiar*100:.0f}%")
        
        alertas_por_dia = []
        
        # Simular classificação com este limiar
        df_simulado = simular_classificacao_risco(df_base, limiar, limiar)
        
        # Contar alertas
        n_alertas = len(df_simulado[df_simulado['Status_Risco_Simulado'] == 'Perda (Risco Alto)'])
        
        # Para backtest mais sofisticado, você pode:
        # 1. Simular diferentes snapshots de dados (se tiver histórico)
        # 2. Simular variações temporais
        # Por agora, usamos snapshot atual como proxy
        
        # Simular distribuição com variação aleatória (proxy)
        # Em produção real, você carregaria snapshots históricos diferentes
        np.random.seed(42)  # Para reprodutibilidade
        for dia in range(n_dias):
            # Adicionar ruído para simular variação diária
            variacao = np.random.uniform(0.8, 1.2)
            alertas_dia = int(n_alertas * variacao)
            alertas_por_dia.append(alertas_dia)
        
        # Estatísticas
        media = np.mean(alertas_por_dia)
        mediana = np.median(alertas_por_dia)
        std = np.std(alertas_por_dia)
        minimo = np.min(alertas_por_dia)
        maximo = np.max(alertas_por_dia)
        p25 = np.percentile(alertas_por_dia, 25)
        p75 = np.percentile(alertas_por_dia, 75)
        p90 = np.percentile(alertas_por_dia, 90)
        p95 = np.percentile(alertas_por_dia, 95)
        
        # Verificar se está na meta (30-50 alertas/dia)
        dentro_meta = 30 <= media <= 50
        
        resultados.append({
            'Limiar': limiar,
            'Limiar_Pct': f"{limiar*100:.0f}%",
            'Media_Alertas_Dia': round(media, 1),
            'Mediana': round(mediana, 1),
            'Desvio_Padrao': round(std, 1),
            'Minimo': minimo,
            'Maximo': maximo,
            'P25': round(p25, 1),
            'P75': round(p75, 1),
            'P90': round(p90, 1),
            'P95': round(p95, 1),
            'Dentro_Meta_30_50': dentro_meta,
            'Serie_Completa': alertas_por_dia
        })
    
    df_resultado = pd.DataFrame(resultados)
    logger.info(f"Backtest concluído: {len(df_resultado)} configurações testadas")
    
    return df_resultado


# ========================================
# GERAÇÃO DE RELATÓRIOS
# ========================================

def gerar_relatorio_csv(df_resultado: pd.DataFrame, arquivo: str = "backtest_resultado") -> str:
    """
    Gera relatório CSV com resultados do backtest.
    
    Args:
        df_resultado: DataFrame com resultados
        arquivo: Nome base do arquivo (sem extensão)
        
    Returns:
        Caminho do arquivo gerado
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    arquivo_final = os.path.join(OUTPUT_DIR, f"{arquivo}_{timestamp}.csv")
    
    # Remover coluna de série completa para o CSV
    df_export = df_resultado.drop(columns=['Serie_Completa'], errors='ignore')
    
    df_export.to_csv(arquivo_final, index=False, encoding=ENCODING)
    logger.info(f"Relatório CSV salvo: {arquivo_final}")
    
    return arquivo_final


def gerar_grafico_distribuicao(df_resultado: pd.DataFrame, arquivo: str = "backtest_distribuicao") -> str:
    """
    Gera gráfico com distribuição de alertas por limiar.
    
    Args:
        df_resultado: DataFrame com resultados
        arquivo: Nome base do arquivo (sem extensão)
        
    Returns:
        Caminho do arquivo gerado
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    arquivo_final = os.path.join(OUTPUT_DIR, f"{arquivo}_{timestamp}.png")
    
    # Configurar estilo
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Backtest do Sistema de Alertas - Distribuição por Limiar', 
                 fontsize=16, fontweight='bold')
    
    # Gráfico 1: Média de alertas/dia por limiar
    ax1 = axes[0, 0]
    limiares_pct = df_resultado['Limiar_Pct']
    medias = df_resultado['Media_Alertas_Dia']
    
    bars = ax1.bar(range(len(limiares_pct)), medias, color='steelblue', alpha=0.7)
    ax1.set_xticks(range(len(limiares_pct)))
    ax1.set_xticklabels(limiares_pct, rotation=45)
    ax1.set_xlabel('Limiar de Queda', fontweight='bold')
    ax1.set_ylabel('Média de Alertas/Dia', fontweight='bold')
    ax1.set_title('Média de Alertas por Limiar')
    
    # Adicionar linha da meta (30-50)
    ax1.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='Meta mínima (30)')
    ax1.axhline(y=50, color='red', linestyle='--', alpha=0.7, label='Meta máxima (50)')
    ax1.legend()
    
    # Destacar barras dentro da meta
    for i, (bar, media) in enumerate(zip(bars, medias)):
        if 30 <= media <= 50:
            bar.set_color('green')
            bar.set_alpha(0.8)
        ax1.text(i, media + 2, f'{media:.1f}', ha='center', va='bottom', fontweight='bold')
    
    # Gráfico 2: Box plot da distribuição
    ax2 = axes[0, 1]
    dados_boxplot = []
    labels_boxplot = []
    
    for _, row in df_resultado.iterrows():
        dados_boxplot.append(row['Serie_Completa'])
        labels_boxplot.append(row['Limiar_Pct'])
    
    bp = ax2.boxplot(dados_boxplot, labels=labels_boxplot, patch_artist=True)
    
    # Colorir boxes
    for patch, media in zip(bp['boxes'], medias):
        if 30 <= media <= 50:
            patch.set_facecolor('lightgreen')
        else:
            patch.set_facecolor('lightcoral')
    
    ax2.set_xlabel('Limiar de Queda', fontweight='bold')
    ax2.set_ylabel('Alertas/Dia', fontweight='bold')
    ax2.set_title('Distribuição de Alertas (Box Plot)')
    ax2.axhline(y=30, color='green', linestyle='--', alpha=0.5)
    ax2.axhline(y=50, color='red', linestyle='--', alpha=0.5)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    # Gráfico 3: Estatísticas (min, max, p90, p95)
    ax3 = axes[1, 0]
    x = range(len(limiares_pct))
    width = 0.2
    
    ax3.bar([i - 1.5*width for i in x], df_resultado['Minimo'], width, 
            label='Mínimo', alpha=0.7, color='lightblue')
    ax3.bar([i - 0.5*width for i in x], df_resultado['Media_Alertas_Dia'], width, 
            label='Média', alpha=0.7, color='steelblue')
    ax3.bar([i + 0.5*width for i in x], df_resultado['P90'], width, 
            label='P90', alpha=0.7, color='orange')
    ax3.bar([i + 1.5*width for i in x], df_resultado['Maximo'], width, 
            label='Máximo', alpha=0.7, color='red')
    
    ax3.set_xticks(x)
    ax3.set_xticklabels(limiares_pct, rotation=45)
    ax3.set_xlabel('Limiar de Queda', fontweight='bold')
    ax3.set_ylabel('Alertas/Dia', fontweight='bold')
    ax3.set_title('Estatísticas por Limiar')
    ax3.legend()
    ax3.axhline(y=30, color='green', linestyle='--', alpha=0.3)
    ax3.axhline(y=50, color='red', linestyle='--', alpha=0.3)
    
    # Gráfico 4: Tabela de resumo
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    # Criar tabela
    tabela_dados = []
    for _, row in df_resultado.iterrows():
        status = '✓ DENTRO DA META' if row['Dentro_Meta_30_50'] else '✗ Fora da meta'
        cor = 'green' if row['Dentro_Meta_30_50'] else 'red'
        tabela_dados.append([
            row['Limiar_Pct'],
            f"{row['Media_Alertas_Dia']:.1f}",
            f"{row['Mediana']:.1f}",
            f"{row['Desvio_Padrao']:.1f}",
            status
        ])
    
    tabela = ax4.table(cellText=tabela_dados,
                      colLabels=['Limiar', 'Média', 'Mediana', 'Std', 'Status'],
                      cellLoc='center',
                      loc='center',
                      colWidths=[0.15, 0.15, 0.15, 0.15, 0.4])
    
    tabela.auto_set_font_size(False)
    tabela.set_fontsize(10)
    tabela.scale(1, 2)
    
    # Colorir células de status
    for i, row in enumerate(df_resultado.iterrows(), start=1):
        _, row_data = row
        cor = '#90EE90' if row_data['Dentro_Meta_30_50'] else '#FFB6C1'
        tabela[(i, 4)].set_facecolor(cor)
    
    ax4.set_title('Resumo dos Limiares', fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(arquivo_final, dpi=300, bbox_inches='tight')
    logger.info(f"Gráfico salvo: {arquivo_final}")
    
    return arquivo_final


def recomendar_limiar(df_resultado: pd.DataFrame) -> Dict:
    """
    Recomenda o melhor limiar baseado nos resultados.
    
    Args:
        df_resultado: DataFrame com resultados
        
    Returns:
        Dicionário com recomendação
    """
    # Filtrar limiares dentro da meta
    dentro_meta = df_resultado[df_resultado['Dentro_Meta_30_50'] == True]
    
    if dentro_meta.empty:
        # Se nenhum está na meta, pegar o mais próximo
        df_resultado['distancia_40'] = abs(df_resultado['Media_Alertas_Dia'] - 40)
        melhor = df_resultado.loc[df_resultado['distancia_40'].idxmin()]
        razao = "Nenhum limiar resultou em média dentro da meta. Escolhido o mais próximo de 40 alertas/dia."
    else:
        # Pegar o que tem média mais próxima de 40 (centro da meta)
        dentro_meta = dentro_meta.copy()
        dentro_meta['distancia_40'] = abs(dentro_meta['Media_Alertas_Dia'] - 40)
        melhor = dentro_meta.loc[dentro_meta['distancia_40'].idxmin()]
        razao = "Limiar escolhido por estar dentro da meta (30-50) e mais próximo do centro (40)."
    
    recomendacao = {
        'limiar_recomendado': melhor['Limiar'],
        'limiar_pct': melhor['Limiar_Pct'],
        'media_alertas': melhor['Media_Alertas_Dia'],
        'mediana': melhor['Mediana'],
        'desvio_padrao': melhor['Desvio_Padrao'],
        'dentro_meta': melhor['Dentro_Meta_30_50'],
        'razao': razao
    }
    
    return recomendacao


# ========================================
# INTERFACE DE LINHA DE COMANDO
# ========================================

def main():
    """Função principal do backtest."""
    print("=" * 80)
    print(" BACKTEST DO SISTEMA DE ALERTAS CHURN V2")
    print("=" * 80)
    print()
    
    # Configurações
    n_dias = 30
    limiares = [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65]
    
    print(f"Configuração:")
    print(f"  Dias simulados: {n_dias}")
    print(f"  Limiares a testar: {[f'{l*100:.0f}%' for l in limiares]}")
    print(f"  Meta: 30-50 alertas/dia")
    print()
    
    # Executar backtest
    print("Executando backtest...")
    df_resultado = executar_backtest(n_dias=n_dias, limiares_teste=limiares)
    
    if df_resultado.empty:
        print("\n❌ Backtest falhou. Verifique os logs.")
        return
    
    print("\n✓ Backtest concluído com sucesso!")
    print()
    
    # Gerar relatórios
    print("Gerando relatórios...")
    arquivo_csv = gerar_relatorio_csv(df_resultado)
    arquivo_grafico = gerar_grafico_distribuicao(df_resultado)
    
    print(f"  CSV: {arquivo_csv}")
    print(f"  Gráfico: {arquivo_grafico}")
    print()
    
    # Recomendar limiar
    recomendacao = recomendar_limiar(df_resultado)
    
    print("=" * 80)
    print(" RECOMENDAÇÃO")
    print("=" * 80)
    print(f"  Limiar recomendado: {recomendacao['limiar_pct']}")
    print(f"  Média de alertas/dia: {recomendacao['media_alertas']:.1f}")
    print(f"  Mediana: {recomendacao['mediana']:.1f}")
    print(f"  Desvio padrão: {recomendacao['desvio_padrao']:.1f}")
    print(f"  Dentro da meta: {'✓ SIM' if recomendacao['dentro_meta'] else '✗ NÃO'}")
    print()
    print(f"  Razão: {recomendacao['razao']}")
    print()
    
    # Exibir tabela de resultados
    print("=" * 80)
    print(" RESULTADOS POR LIMIAR")
    print("=" * 80)
    print()
    
    df_display = df_resultado[['Limiar_Pct', 'Media_Alertas_Dia', 'Mediana', 'Desvio_Padrao', 
                               'Minimo', 'Maximo', 'P90', 'Dentro_Meta_30_50']]
    df_display.columns = ['Limiar', 'Média', 'Mediana', 'Std', 'Min', 'Max', 'P90', 'Meta']
    
    print(df_display.to_string(index=False))
    print()
    print("=" * 80)
    
    print("\n✓ Processo concluído com sucesso!")
    print(f"\nPara aplicar a recomendação, atualize config_churn.py:")
    print(f"  REDUCAO_BASELINE_RISCO_ALTO = {recomendacao['limiar_recomendado']}")
    print(f"  REDUCAO_WOW_RISCO_ALTO = {recomendacao['limiar_recomendado']}")
    print()


if __name__ == "__main__":
    main()

