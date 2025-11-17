# ========================================
# MÓDULO DE CLASSIFICAÇÃO DE PORTE
# Sistema de Alertas Churn v2
# ========================================

"""
Módulo para classificação de porte de laboratórios baseado em volume médio mensal.
Utilizado para aplicar diferentes limiares de alerta conforme tamanho do laboratório.
"""

from typing import Union, Optional, Dict
import pandas as pd
import numpy as np


# ========================================
# CONFIGURAÇÕES PADRÃO
# ========================================

# Limiares padrão (podem ser sobrescritos via config_churn.py)
PORTE_PEQUENO_MAX = 40
PORTE_MEDIO_MAX = 80
PORTE_MEDIO_GRANDE_MAX = 150
PORTE_MEDIO_MIN = PORTE_PEQUENO_MAX + 1
PORTE_GRANDE_MIN = PORTE_MEDIO_GRANDE_MAX + 1
RISCO_DIAS_SEM_COLETA_RULES: Dict[str, Dict[str, Union[int, bool]]] = {
    'Pequeno': {'habilita': False},
    'Médio': {'habilita': True, 'min_dias_uteis': 2, 'max_dias_corridos': 15},
    'Médio/Grande': {'habilita': True, 'min_dias_uteis': 1, 'max_dias_corridos': 15},
    'Grande': {'habilita': True, 'min_dias_uteis': 1, 'max_dias_uteis': 5},
}
PERDA_RECENTE_RULES: Dict[str, Dict[str, Union[int, bool]]] = {
    'Pequeno': {'min_dias_corridos': 30, 'max_dias_corridos': 180},
    'Médio': {'min_dias_corridos': 15, 'max_dias_corridos': 180},
    'Médio/Grande': {'min_dias_corridos': 15, 'max_dias_corridos': 180},
    'Grande': {'min_dias_uteis': 5, 'max_dias_corridos': 180},
}
PERDA_ANTIGA_LIMITE_CORRIDOS = 180

try:
    from config_churn import (
        PORTE_PEQUENO_MAX as CFG_PORTE_PEQUENO_MAX,
        PORTE_MEDIO_MAX as CFG_PORTE_MEDIO_MAX,
        PORTE_MEDIO_GRANDE_MAX as CFG_PORTE_MEDIO_GRANDE_MAX,
        PORTE_MEDIO_MIN as CFG_PORTE_MEDIO_MIN,
        PORTE_GRANDE_MIN as CFG_PORTE_GRANDE_MIN,
        RISCO_DIAS_SEM_COLETA_RULES as CFG_RISCO_RULES,
        PERDA_RECENTE_RULES as CFG_PERDA_RULES,
        PERDA_ANTIGA_LIMITE_CORRIDOS as CFG_PERDA_ANTIGA_LIMITE
    )
    PORTE_PEQUENO_MAX = CFG_PORTE_PEQUENO_MAX
    PORTE_MEDIO_MAX = CFG_PORTE_MEDIO_MAX
    PORTE_MEDIO_GRANDE_MAX = CFG_PORTE_MEDIO_GRANDE_MAX
    PORTE_MEDIO_MIN = CFG_PORTE_MEDIO_MIN
    PORTE_GRANDE_MIN = CFG_PORTE_GRANDE_MIN
    RISCO_DIAS_SEM_COLETA_RULES = CFG_RISCO_RULES
    PERDA_RECENTE_RULES = CFG_PERDA_RULES
    PERDA_ANTIGA_LIMITE_CORRIDOS = CFG_PERDA_ANTIGA_LIMITE
except Exception:
    pass


# ========================================
# FUNÇÕES PRINCIPAIS
# ========================================

def calcular_porte(volume_medio_mensal: Union[float, int], 
                   limiar_grande: Optional[int] = None,
                   limiar_medio: Optional[int] = None,
                   limite_pequeno_max: Optional[int] = None,
                   limite_medio_max: Optional[int] = None,
                   limite_medio_grande_max: Optional[int] = None) -> str:
    """
    Classifica o porte de um laboratório baseado no volume médio mensal.
    
    Args:
        volume_medio_mensal: Volume médio de coletas por mês
        limiar_grande: Limiar mínimo para porte Grande (padrão: PORTE_GRANDE_MIN)
        limiar_medio: Limiar mínimo para porte Médio (padrão: PORTE_MEDIO_MIN)
        
    Returns:
        'Grande', 'Médio' ou 'Pequeno'
        
    Exemplos:
        >>> calcular_porte(150)
        'Grande'
        >>> calcular_porte(75)
        'Médio'
        >>> calcular_porte(25)
        'Pequeno'
    """
    # Usar valores padrão se não fornecidos
    if limiar_grande is None:
        limiar_grande = PORTE_GRANDE_MIN
    if limiar_medio is None:
        limiar_medio = PORTE_MEDIO_MIN
    if limite_pequeno_max is None:
        limite_pequeno_max = PORTE_PEQUENO_MAX
    if limite_medio_max is None:
        limite_medio_max = PORTE_MEDIO_MAX
    if limite_medio_grande_max is None:
        limite_medio_grande_max = PORTE_MEDIO_GRANDE_MAX
    
    # Tratar valores inválidos
    if pd.isna(volume_medio_mensal) or volume_medio_mensal is None:
        return 'Pequeno'  # Default para valores ausentes
    
    volume = float(volume_medio_mensal)
    
    # Classificar
    if volume >= limiar_grande:
        return 'Grande'
    if volume > limite_medio_grande_max:
        return 'Grande'
    if volume > limite_medio_max:
        return 'Médio/Grande'
    if volume >= limiar_medio:
        return 'Médio'
    if volume > limite_pequeno_max:
        return 'Médio'
    return 'Pequeno'


def aplicar_porte_dataframe(df: pd.DataFrame, 
                           coluna_volume: str = 'Media_Coletas_Mensal_2025',
                           coluna_destino: str = 'Porte',
                           limiar_grande: Optional[int] = None,
                           limiar_medio: Optional[int] = None) -> pd.DataFrame:
    """
    Aplica classificação de porte a um DataFrame.
    
    Args:
        df: DataFrame com dados dos laboratórios
        coluna_volume: Nome da coluna com volume médio mensal
        coluna_destino: Nome da coluna onde salvar o porte
        limiar_grande: Limiar mínimo para porte Grande
        limiar_medio: Limiar mínimo para porte Médio
        
    Returns:
        DataFrame com coluna de porte adicionada
    """
    df = df.copy()
    
    # Verificar se coluna existe
    if coluna_volume not in df.columns:
        raise ValueError(f"Coluna '{coluna_volume}' não encontrada no DataFrame")
    
    # Aplicar classificação
    df[coluna_destino] = df[coluna_volume].apply(
        lambda x: calcular_porte(
            x,
            limiar_grande=limiar_grande,
            limiar_medio=limiar_medio
        )
    )
    
    return df


def obter_regra_risco_por_porte(porte: str) -> Dict[str, Union[int, bool]]:
    return RISCO_DIAS_SEM_COLETA_RULES.get(porte, RISCO_DIAS_SEM_COLETA_RULES.get('Médio', {'habilita': False}))


def obter_regra_perda_por_porte(porte: str) -> Dict[str, Union[int, bool]]:
    return PERDA_RECENTE_RULES.get(porte, PERDA_RECENTE_RULES.get('Médio', {}))


def avaliar_risco_por_dias_sem_coleta(dias_corridos: int,
                                      dias_uteis: int,
                                      porte: str) -> bool:
    regra = obter_regra_risco_por_porte(porte)
    if not regra.get('habilita', False):
        return False
    if dias_corridos is None:
        dias_corridos = 0
    if dias_uteis is None:
        dias_uteis = 0

    min_uteis = regra.get('min_dias_uteis')
    min_corridos = regra.get('min_dias_corridos')
    max_uteis = regra.get('max_dias_uteis')
    max_corridos = regra.get('max_dias_corridos')

    if min_uteis is not None and dias_uteis < min_uteis:
        return False
    if min_corridos is not None and dias_corridos < min_corridos:
        return False
    if max_uteis is not None and dias_uteis > max_uteis:
        return False
    if max_corridos is not None and dias_corridos > max_corridos:
        return False
    return True


def classificar_perda_por_dias_sem_coleta(dias_corridos: int,
                                          dias_uteis: int,
                                          porte: str) -> Optional[str]:
    if dias_corridos is None:
        dias_corridos = 0
    if dias_uteis is None:
        dias_uteis = 0

    if dias_corridos > PERDA_ANTIGA_LIMITE_CORRIDOS:
        return 'Perda Antiga'

    regra_perda = obter_regra_perda_por_porte(porte)
    min_corridos = regra_perda.get('min_dias_corridos')
    min_uteis = regra_perda.get('min_dias_uteis')
    max_corridos = regra_perda.get('max_dias_corridos', PERDA_ANTIGA_LIMITE_CORRIDOS)

    cond_corridos = True
    cond_uteis = True

    if min_corridos is not None:
        cond_corridos = dias_corridos >= min_corridos
    if min_uteis is not None:
        cond_uteis = dias_uteis >= min_uteis

    if cond_corridos and cond_uteis and dias_corridos <= max_corridos:
        return 'Perda Recente'

    return None


def obter_limiar_dias_sem_coleta(porte: str,
                                  limiar_grande: int = 1,
                                  limiar_medio: int = 2,
                                  limiar_pequeno: int = 3) -> int:
    """
    Retorna o limiar de dias sem coleta baseado no porte do laboratório.
    
    Args:
        porte: Porte do laboratório ('Grande', 'Médio' ou 'Pequeno')
        limiar_grande: Dias sem coleta para acionar alerta em lab Grande
        limiar_medio: Dias sem coleta para acionar alerta em lab Médio
        limiar_pequeno: Dias sem coleta para acionar alerta em lab Pequeno
        
    Returns:
        Número de dias sem coleta que aciona alerta
        
    Exemplos:
        >>> obter_limiar_dias_sem_coleta('Grande')
        1
        >>> obter_limiar_dias_sem_coleta('Médio')
        2
        >>> obter_limiar_dias_sem_coleta('Pequeno')
        3
    """
    if porte == 'Grande':
        return limiar_grande
    elif porte == 'Médio':
        return limiar_medio
    else:  # Pequeno ou qualquer outro valor
        return limiar_pequeno


def verificar_gatilho_dias_sem_coleta(dias_sem_coleta: int,
                                      porte: str,
                                      limiar_grande: int = 1,
                                      limiar_medio: int = 2,
                                      limiar_pequeno: int = 3) -> bool:
    """
    Verifica se o número de dias sem coleta ultrapassa o limiar para o porte.
    
    Args:
        dias_sem_coleta: Número de dias consecutivos sem coleta
        porte: Porte do laboratório ('Grande', 'Médio' ou 'Pequeno')
        limiar_grande: Limiar para laboratórios Grandes
        limiar_medio: Limiar para laboratórios Médios
        limiar_pequeno: Limiar para laboratórios Pequenos
        
    Returns:
        True se ultrapassou o limiar (deve acionar alerta), False caso contrário
        
    Exemplos:
        >>> verificar_gatilho_dias_sem_coleta(1, 'Grande')
        True
        >>> verificar_gatilho_dias_sem_coleta(1, 'Médio')
        False
        >>> verificar_gatilho_dias_sem_coleta(3, 'Pequeno')
        True
    """
    limiar = obter_limiar_dias_sem_coleta(porte, limiar_grande, limiar_medio, limiar_pequeno)
    return dias_sem_coleta >= limiar


def aplicar_gatilho_dataframe(df: pd.DataFrame,
                              coluna_dias: str = 'Dias_Sem_Coleta',
                              coluna_porte: str = 'Porte',
                              coluna_destino: str = 'Gatilho_Dias_Sem_Coleta',
                              coluna_dias_uteis: str = 'Dias_Sem_Coleta_Uteis') -> pd.DataFrame:
    """
    Aplica verificação de gatilho de dias sem coleta a um DataFrame.
    
    Args:
        df: DataFrame com dados dos laboratórios
        coluna_dias: Nome da coluna com dias sem coleta
        coluna_porte: Nome da coluna com porte do laboratório
        coluna_destino: Nome da coluna onde salvar resultado do gatilho
        limiar_grande: Limiar para laboratórios Grandes
        limiar_medio: Limiar para laboratórios Médios
        limiar_pequeno: Limiar para laboratórios Pequenos
        
    Returns:
        DataFrame com coluna de gatilho adicionada
    """
    df = df.copy()
    
    # Verificar se colunas existem
    if coluna_dias not in df.columns:
        raise ValueError(f"Coluna '{coluna_dias}' não encontrada no DataFrame")
    if coluna_porte not in df.columns:
        raise ValueError(f"Coluna '{coluna_porte}' não encontrada no DataFrame")
    
    # Aplicar verificação
    def _avaliar(row):
        dias_corridos = row.get(coluna_dias, 0)
        dias_uteis = row.get(coluna_dias_uteis, dias_corridos)
        porte = row.get(coluna_porte, 'Pequeno')
        return avaliar_risco_por_dias_sem_coleta(dias_corridos, dias_uteis, porte)

    df[coluna_destino] = df.apply(_avaliar, axis=1)
    
    return df


def estatisticas_porte(df: pd.DataFrame, coluna_porte: str = 'Porte') -> pd.DataFrame:
    """
    Gera estatísticas sobre distribuição de porte no DataFrame.
    
    Args:
        df: DataFrame com dados dos laboratórios
        coluna_porte: Nome da coluna com porte
        
    Returns:
        DataFrame com estatísticas por porte
    """
    if coluna_porte not in df.columns:
        raise ValueError(f"Coluna '{coluna_porte}' não encontrada no DataFrame")
    
    stats = df[coluna_porte].value_counts().to_frame('Quantidade')
    stats['Percentual'] = (stats['Quantidade'] / len(df) * 100).round(2)
    stats = stats.sort_index()
    
    return stats


def obter_descricao_porte(porte: str) -> str:
    """
    Retorna descrição amigável do porte.
    
    Args:
        porte: Porte do laboratório
        
    Returns:
        Descrição textual do porte
    """
    descricoes = {
        'Grande': f'Laboratório Grande (≥ {PORTE_GRANDE_MIN} coletas/mês)',
        'Médio': f'Laboratório Médio ({PORTE_MEDIO_MIN}-{PORTE_GRANDE_MIN-1} coletas/mês)',
        'Pequeno': f'Laboratório Pequeno (< {PORTE_MEDIO_MIN} coletas/mês)'
    }
    
    return descricoes.get(porte, 'Porte não identificado')


def validar_limiares(limiar_grande: int, limiar_medio: int) -> bool:
    """
    Valida se os limiares fornecidos são consistentes.
    
    Args:
        limiar_grande: Limiar para porte Grande
        limiar_medio: Limiar para porte Médio
        
    Returns:
        True se válido, False caso contrário
    """
    if limiar_grande <= 0 or limiar_medio <= 0:
        return False
    
    if limiar_medio >= limiar_grande:
        return False
    
    return True


# ========================================
# FUNÇÕES AUXILIARES
# ========================================

def recomendar_limiares(df: pd.DataFrame, 
                       coluna_volume: str = 'Media_Coletas_Mensal_2025',
                       percentis: tuple = (33, 67)) -> dict:
    """
    Recomenda limiares baseados nos percentis dos dados.
    
    Args:
        df: DataFrame com dados dos laboratórios
        coluna_volume: Nome da coluna com volume médio
        percentis: Tupla com percentis para dividir em 3 grupos
        
    Returns:
        Dicionário com limiares recomendados
    """
    if coluna_volume not in df.columns:
        raise ValueError(f"Coluna '{coluna_volume}' não encontrada no DataFrame")
    
    volumes = df[coluna_volume].dropna()
    
    if len(volumes) == 0:
        return {
            'limiar_medio': PORTE_MEDIO_MIN,
            'limiar_grande': PORTE_GRANDE_MIN,
            'base': 'padrão (sem dados)'
        }
    
    p33 = volumes.quantile(percentis[0] / 100)
    p67 = volumes.quantile(percentis[1] / 100)
    
    return {
        'limiar_medio': int(np.ceil(p33)),
        'limiar_grande': int(np.ceil(p67)),
        'base': f'percentis {percentis[0]}% e {percentis[1]}%'
    }


# ========================================
# CLASSE PARA CONFIGURAÇÃO PERSONALIZADA
# ========================================

class ConfiguracaoPorte:
    """
    Classe para gerenciar configuração personalizada de porte.
    
    Permite definir limiares e dias sem coleta customizados.
    """
    
    def __init__(self,
                 limiar_grande: int = PORTE_GRANDE_MIN,
                 limiar_medio: int = PORTE_MEDIO_MIN,
                 dias_sem_coleta_grande: int = 1,
                 dias_sem_coleta_medio: int = 2,
                 dias_sem_coleta_pequeno: int = 3):
        """
        Inicializa configuração de porte.
        
        Args:
            limiar_grande: Volume mínimo para porte Grande
            limiar_medio: Volume mínimo para porte Médio
            dias_sem_coleta_grande: Dias sem coleta para alerta em Grande
            dias_sem_coleta_medio: Dias sem coleta para alerta em Médio
            dias_sem_coleta_pequeno: Dias sem coleta para alerta em Pequeno
        """
        if not validar_limiares(limiar_grande, limiar_medio):
            raise ValueError("Limiares inválidos: limiar_medio deve ser menor que limiar_grande")
        
        self.limiar_grande = limiar_grande
        self.limiar_medio = limiar_medio
        self.dias_sem_coleta_grande = dias_sem_coleta_grande
        self.dias_sem_coleta_medio = dias_sem_coleta_medio
        self.dias_sem_coleta_pequeno = dias_sem_coleta_pequeno
    
    def calcular_porte(self, volume_medio_mensal: Union[float, int]) -> str:
        """Calcula porte usando configuração atual."""
        return calcular_porte(volume_medio_mensal, self.limiar_grande, self.limiar_medio)
    
    def verificar_gatilho(self, dias_sem_coleta: int, porte: str) -> bool:
        """Verifica gatilho usando configuração atual."""
        return verificar_gatilho_dias_sem_coleta(
            dias_sem_coleta,
            porte,
            self.dias_sem_coleta_grande,
            self.dias_sem_coleta_medio,
            self.dias_sem_coleta_pequeno
        )
    
    def __repr__(self) -> str:
        return (f"ConfiguracaoPorte("
                f"Grande≥{self.limiar_grande}, "
                f"Médio≥{self.limiar_medio}, "
                f"Dias: G={self.dias_sem_coleta_grande}, "
                f"M={self.dias_sem_coleta_medio}, "
                f"P={self.dias_sem_coleta_pequeno})")


# ========================================
# TESTE DO MÓDULO
# ========================================

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DO MÓDULO DE PORTE")
    print("=" * 60)
    
    # Teste 1: Classificação individual
    print("\n1. Classificação de Porte Individual:")
    volumes_teste = [150, 75, 25, 100, 49, 0, None]
    for vol in volumes_teste:
        porte = calcular_porte(vol) if vol is not None else calcular_porte(vol)
        print(f"  Volume {vol}: {porte}")
    
    # Teste 2: DataFrame
    print("\n2. Teste com DataFrame:")
    df_teste = pd.DataFrame({
        'Lab': ['A', 'B', 'C', 'D', 'E'],
        'Media_Coletas_Mensal_2025': [200, 80, 30, 100, 45],
        'Dias_Sem_Coleta': [2, 1, 4, 0, 3]
    })
    
    df_teste = aplicar_porte_dataframe(df_teste)
    df_teste = aplicar_gatilho_dataframe(df_teste)
    
    print(df_teste.to_string(index=False))
    
    # Teste 3: Estatísticas
    print("\n3. Estatísticas de Porte:")
    stats = estatisticas_porte(df_teste)
    print(stats)
    
    # Teste 4: Descrições
    print("\n4. Descrições de Porte:")
    for porte in ['Grande', 'Médio', 'Pequeno']:
        print(f"  {porte}: {obter_descricao_porte(porte)}")
    
    # Teste 5: Configuração personalizada
    print("\n5. Configuração Personalizada:")
    config = ConfiguracaoPorte(limiar_grande=150, limiar_medio=75)
    print(f"  {config}")
    print(f"  Volume 100: {config.calcular_porte(100)}")
    print(f"  Gatilho (2 dias, Médio): {config.verificar_gatilho(2, 'Médio')}")
    
    print("\n" + "=" * 60)
    print("TESTES CONCLUÍDOS")
    print("=" * 60)

