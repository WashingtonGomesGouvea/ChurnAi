# ========================================
# MÓDULO DE FERIADOS BRASILEIROS
# Sistema de Alertas Churn v2
# ========================================

"""
Módulo para gerenciamento de feriados nacionais e estaduais do Brasil.
Utilizado para calcular dias úteis excluindo fins de semana e feriados.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple
import pandas as pd


# ========================================
# FERIADOS NACIONAIS FIXOS
# ========================================

FERIADOS_FIXOS = {
    # Formato: (mes, dia): "Nome do Feriado"
    (1, 1): "Ano Novo",
    (4, 21): "Tiradentes",
    (5, 1): "Dia do Trabalho",
    (9, 7): "Independência do Brasil",
    (10, 12): "Nossa Senhora Aparecida",
    (11, 2): "Finados",
    (11, 15): "Proclamação da República",
    (11, 20): "Dia da Consciência Negra",  # Federal desde 2024
    (12, 25): "Natal",
}


# ========================================
# FERIADOS MÓVEIS (Calculados)
# ========================================

def calcular_pascoa(ano: int) -> date:
    """
    Calcula a data da Páscoa usando o algoritmo de Meeus/Jones/Butcher.
    
    Args:
        ano: Ano para calcular a Páscoa
        
    Returns:
        Data da Páscoa
    """
    a = ano % 19
    b = ano // 100
    c = ano % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)


def calcular_feriados_moveis(ano: int) -> List[Tuple[date, str]]:
    """
    Calcula feriados móveis para um ano específico.
    
    Args:
        ano: Ano para calcular os feriados
        
    Returns:
        Lista de tuplas (data, nome_feriado)
    """
    pascoa = calcular_pascoa(ano)
    
    feriados = [
        # Carnaval (47 dias antes da Páscoa)
        (pascoa - timedelta(days=47), "Carnaval (Terça)"),
        # Carnaval Segunda
        (pascoa - timedelta(days=48), "Carnaval (Segunda)"),
        # Sexta-feira Santa (2 dias antes da Páscoa)
        (pascoa - timedelta(days=2), "Sexta-feira Santa"),
        # Páscoa
        (pascoa, "Páscoa"),
        # Corpus Christi (60 dias depois da Páscoa)
        (pascoa + timedelta(days=60), "Corpus Christi"),
    ]
    
    return feriados


# ========================================
# FERIADOS ESTADUAIS
# ========================================

FERIADOS_ESTADUAIS = {
    # Formato: 'UF': [(mes, dia, "Nome do Feriado"), ...]
    'AC': [(1, 23, "Dia do Evangélico"), (6, 15, "Aniversário do Acre"), (9, 5, "Dia da Amazônia")],
    'AL': [(6, 24, "São João"), (6, 29, "São Pedro"), (9, 16, "Emancipação Política"), (11, 20, "Morte de Zumbi dos Palmares")],
    'AP': [(3, 19, "Dia de São José"), (9, 13, "Criação do Território"), (11, 20, "Consciência Negra")],
    'AM': [(9, 5, "Elevação à categoria de Província"), (11, 20, "Consciência Negra"), (12, 8, "Nossa Senhora da Conceição")],
    'BA': [(7, 2, "Independência da Bahia")],
    'CE': [(3, 19, "São José"), (3, 25, "Abolição da Escravidão no Ceará")],
    'DF': [(4, 21, "Fundação de Brasília"), (11, 30, "Dia do Evangélico")],
    'ES': [(10, 28, "Dia do Servidor Público")],
    'GO': [(10, 28, "Dia do Servidor Público")],
    'MA': [(7, 28, "Adesão do Maranhão à Independência")],
    'MT': [(11, 20, "Consciência Negra")],
    'MS': [(10, 11, "Criação do Estado")],
    'MG': [(4, 21, "Tiradentes")],
    'PA': [(8, 15, "Adesão do Pará à Independência")],
    'PB': [(8, 5, "Fundação do Estado")],
    'PR': [(12, 19, "Emancipação Política")],
    'PE': [(3, 6, "Revolução Pernambucana"), (6, 24, "São João")],
    'PI': [(3, 13, "Dia da Batalha do Jenipapo"), (10, 19, "Dia de Nossa Senhora da Vitória")],
    'RJ': [(4, 23, "Dia de São Jorge"), (10, 28, "Dia do Funcionário Público"), (11, 20, "Zumbi dos Palmares")],
    'RN': [(10, 3, "Mártires de Cunhaú e Uruaçu")],
    'RS': [(9, 20, "Revolução Farroupilha")],
    'RO': [(1, 4, "Criação do Estado"), (6, 18, "Dia do Evangélico")],
    'RR': [(10, 5, "Criação do Estado")],
    'SC': [(8, 11, "Criação da Capitania")],
    'SP': [(7, 9, "Revolução Constitucionalista")],
    'SE': [(7, 8, "Emancipação Política")],
    'TO': [(10, 5, "Criação do Estado"), (9, 8, "Nossa Senhora da Natividade")],
}


# ========================================
# FUNÇÕES PRINCIPAIS
# ========================================

def obter_feriados_ano(ano: int, uf: Optional[str] = None) -> List[date]:
    """
    Retorna lista de todos os feriados de um ano (nacionais + estaduais se UF fornecida).
    
    Args:
        ano: Ano para buscar feriados
        uf: Sigla da UF (opcional). Se fornecida, inclui feriados estaduais
        
    Returns:
        Lista de datas dos feriados
    """
    feriados = []
    
    # Adicionar feriados fixos nacionais
    for (mes, dia), nome in FERIADOS_FIXOS.items():
        try:
            feriados.append(date(ano, mes, dia))
        except ValueError:
            # Ignora datas inválidas (ex: 29 de fevereiro em anos não bissextos)
            pass
    
    # Adicionar feriados móveis
    feriados_moveis = calcular_feriados_moveis(ano)
    feriados.extend([data for data, nome in feriados_moveis])
    
    # Adicionar feriados estaduais se UF fornecida
    if uf and uf.upper() in FERIADOS_ESTADUAIS:
        for mes, dia, nome in FERIADOS_ESTADUAIS[uf.upper()]:
            try:
                feriados.append(date(ano, mes, dia))
            except ValueError:
                pass
    
    # Remover duplicatas e ordenar
    feriados = sorted(list(set(feriados)))
    
    return feriados


def is_feriado(data: datetime | date, uf: Optional[str] = None) -> bool:
    """
    Verifica se uma data é feriado (nacional ou estadual).
    
    Args:
        data: Data a verificar (datetime ou date)
        uf: Sigla da UF (opcional). Se fornecida, considera feriados estaduais
        
    Returns:
        True se é feriado, False caso contrário
    """
    # Converter datetime para date se necessário
    if isinstance(data, datetime):
        data = data.date()
    
    # Obter feriados do ano
    feriados = obter_feriados_ano(data.year, uf)
    
    return data in feriados


def is_dia_util(data: datetime | date, uf: Optional[str] = None) -> bool:
    """
    Verifica se uma data é dia útil (não é fim de semana nem feriado).
    
    Args:
        data: Data a verificar (datetime ou date)
        uf: Sigla da UF (opcional). Se fornecida, considera feriados estaduais
        
    Returns:
        True se é dia útil, False caso contrário
    """
    # Converter datetime para date se necessário
    if isinstance(data, datetime):
        data = data.date()
    
    # Verificar se é fim de semana (5=sábado, 6=domingo)
    if data.weekday() >= 5:
        return False
    
    # Verificar se é feriado
    if is_feriado(data, uf):
        return False
    
    return True


def dias_uteis_entre(start: datetime | date, end: datetime | date, uf: Optional[str] = None) -> int:
    """
    Calcula o número de dias úteis entre duas datas (inclusive).
    
    Args:
        start: Data inicial
        end: Data final
        uf: Sigla da UF (opcional). Se fornecida, considera feriados estaduais
        
    Returns:
        Número de dias úteis entre as datas
    """
    # Converter datetime para date se necessário
    if isinstance(start, datetime):
        start = start.date()
    if isinstance(end, datetime):
        end = end.date()
    
    # Garantir que start <= end
    if start > end:
        start, end = end, start
    
    # Obter feriados dos anos envolvidos
    anos = set()
    current = start
    while current <= end:
        anos.add(current.year)
        current += timedelta(days=365)
    
    feriados = []
    for ano in anos:
        feriados.extend(obter_feriados_ano(ano, uf))
    feriados_set = set(feriados)
    
    # Contar dias úteis
    dias_uteis = 0
    current = start
    while current <= end:
        if current.weekday() < 5 and current not in feriados_set:
            dias_uteis += 1
        current += timedelta(days=1)
    
    return dias_uteis


def obter_dias_uteis_no_periodo(start: datetime | date, end: datetime | date, uf: Optional[str] = None) -> List[date]:
    """
    Retorna lista de datas que são dias úteis no período.
    
    Args:
        start: Data inicial
        end: Data final
        uf: Sigla da UF (opcional). Se fornecida, considera feriados estaduais
        
    Returns:
        Lista de datas que são dias úteis
    """
    # Converter datetime para date se necessário
    if isinstance(start, datetime):
        start = start.date()
    if isinstance(end, datetime):
        end = end.date()
    
    # Garantir que start <= end
    if start > end:
        start, end = end, start
    
    # Obter feriados
    anos = set()
    current = start
    while current <= end:
        anos.add(current.year)
        current += timedelta(days=365)
    
    feriados = []
    for ano in anos:
        feriados.extend(obter_feriados_ano(ano, uf))
    feriados_set = set(feriados)
    
    # Coletar dias úteis
    dias_uteis = []
    current = start
    while current <= end:
        if current.weekday() < 5 and current not in feriados_set:
            dias_uteis.append(current)
        current += timedelta(days=1)
    
    return dias_uteis


def proximo_dia_util(data: datetime | date, uf: Optional[str] = None) -> date:
    """
    Retorna o próximo dia útil a partir de uma data.
    
    Args:
        data: Data de referência
        uf: Sigla da UF (opcional)
        
    Returns:
        Próximo dia útil
    """
    # Converter datetime para date se necessário
    if isinstance(data, datetime):
        data = data.date()
    
    proximo = data + timedelta(days=1)
    while not is_dia_util(proximo, uf):
        proximo += timedelta(days=1)
    
    return proximo


def dia_util_anterior(data: datetime | date, uf: Optional[str] = None) -> date:
    """
    Retorna o dia útil anterior a uma data.
    
    Args:
        data: Data de referência
        uf: Sigla da UF (opcional)
        
    Returns:
        Dia útil anterior
    """
    # Converter datetime para date se necessário
    if isinstance(data, datetime):
        data = data.date()
    
    anterior = data - timedelta(days=1)
    while not is_dia_util(anterior, uf):
        anterior -= timedelta(days=1)
    
    return anterior


# ========================================
# FUNÇÕES AUXILIARES PARA DEBUGGING
# ========================================

def listar_feriados_ano(ano: int, uf: Optional[str] = None) -> pd.DataFrame:
    """
    Retorna DataFrame com todos os feriados de um ano.
    
    Args:
        ano: Ano para listar feriados
        uf: Sigla da UF (opcional)
        
    Returns:
        DataFrame com colunas: Data, Nome, Tipo, DiaSemana
    """
    feriados_info = []
    
    # Feriados fixos nacionais
    for (mes, dia), nome in FERIADOS_FIXOS.items():
        try:
            data = date(ano, mes, dia)
            feriados_info.append({
                'Data': data,
                'Nome': nome,
                'Tipo': 'Nacional - Fixo',
                'DiaSemana': ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'][data.weekday()]
            })
        except ValueError:
            pass
    
    # Feriados móveis
    feriados_moveis = calcular_feriados_moveis(ano)
    for data, nome in feriados_moveis:
        feriados_info.append({
            'Data': data,
            'Nome': nome,
            'Tipo': 'Nacional - Móvel',
            'DiaSemana': ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'][data.weekday()]
        })
    
    # Feriados estaduais
    if uf and uf.upper() in FERIADOS_ESTADUAIS:
        for mes, dia, nome in FERIADOS_ESTADUAIS[uf.upper()]:
            try:
                data = date(ano, mes, dia)
                feriados_info.append({
                    'Data': data,
                    'Nome': nome,
                    'Tipo': f'Estadual - {uf.upper()}',
                    'DiaSemana': ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'][data.weekday()]
                })
            except ValueError:
                pass
    
    df = pd.DataFrame(feriados_info)
    if not df.empty:
        df = df.sort_values('Data').reset_index(drop=True)
    
    return df


# ========================================
# TESTE DO MÓDULO
# ========================================

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DO MÓDULO DE FERIADOS")
    print("=" * 60)
    
    # Teste 1: Listar feriados de 2025
    print("\n1. Feriados Nacionais de 2025:")
    df_2025 = listar_feriados_ano(2025)
    print(df_2025.to_string(index=False))
    
    # Teste 2: Feriados de SP em 2025
    print("\n2. Feriados em São Paulo (SP) em 2025:")
    df_sp = listar_feriados_ano(2025, 'SP')
    print(df_sp[df_sp['Tipo'].str.contains('Estadual')].to_string(index=False))
    
    # Teste 3: Verificar se dia é útil
    print("\n3. Teste de Dias Úteis:")
    datas_teste = [
        date(2025, 1, 1),   # Ano Novo
        date(2025, 1, 2),   # Dia útil
        date(2025, 7, 9),   # Rev. Constitucionalista (SP)
        date(2025, 12, 25), # Natal
    ]
    
    for data in datas_teste:
        util_nacional = is_dia_util(data)
        util_sp = is_dia_util(data, 'SP')
        print(f"  {data.strftime('%d/%m/%Y')} - Nacional: {util_nacional}, SP: {util_sp}")
    
    # Teste 4: Contar dias úteis
    print("\n4. Dias Úteis em Janeiro/2025:")
    start = date(2025, 1, 1)
    end = date(2025, 1, 31)
    dias_nacional = dias_uteis_entre(start, end)
    dias_sp = dias_uteis_entre(start, end, 'SP')
    print(f"  Nacional: {dias_nacional} dias úteis")
    print(f"  SP: {dias_sp} dias úteis")
    
    print("\n" + "=" * 60)
    print("TESTES CONCLUÍDOS")
    print("=" * 60)

