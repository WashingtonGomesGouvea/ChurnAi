# 📘 Documentação Oficial - Sistema Churn AI (V2)

Esta documentação foi gerada com base nas **regras de negócio ativas no código-fonte** do sistema e reflete **apenas as métricas e funcionalidades realmente implementadas**.

---

## 1. Glossário de Termos 📚

Definições oficiais extraídas do código atual:

| Termo | Definição | Onde é Usado |
|-------|-----------|--------------|
| **Baseline Mensal** | Média dos **Top-N maiores meses** de coletas em 2024 e 2025 (padrão: Top-3). Representa o volume de referência robusto de cada laboratório. | Análise de risco, comparação mensal |
| **WoW (Week over Week)** | Variação percentual entre a semana ISO atual e a semana anterior (apenas dias úteis). | Fechamento Semanal, alertas de queda |
| **Porte** | Classificação do tamanho do laboratório baseada na **média mensal de 2025**. | Regras de risco e perda |
| **Sinal de Concorrência** | Indica que o CNPJ do laboratório apareceu no sistema do concorrente (Gralab). | Análise de Concorrente |

---

## 2. Regras de Negócio: Risco e Perda 🚦

As regras abaixo são extraídas diretamente do módulo [`porte_laboratorio.py`](file:///f:/Progamação/ChurnAi/porte_laboratorio.py).

### 2.1. Definição de Porte

O porte é calculado com base na **média de coletas mensal de 2025**.

| Porte | Volume Médio Mensal |
|-------|---------------------|
| **Pequeno** | Até 40 coletas |
| **Médio** | 41 a 80 coletas |
| **Médio/Grande** | 81 a 150 coletas |
| **Grande** | Acima de 150 coletas |

**Código**: Função `calcular_porte()` em [`porte_laboratorio.py:67-121`](file:///f:/Progamação/ChurnAi/porte_laboratorio.py#L67-L121)

---

### 2.2. Regras de Risco (Ausência de Coleta)

Define quando acender o alerta de **risco operacional** por falta de envio de amostras.

| Categoria / Porte | Volume | 🛑 Teto (Dias) | ⚠️ Mínimo (Dias) | Regra de Negócio |
|-------------------|--------|----------------|------------------|------------------|
| **Pequeno** | ≤ 40 | - | - | **Não gera risco** por dias sem coleta. |
| **Médio** | 41-80 | 15 dias corridos | 2 dias úteis | Alerta se **> 2 dias úteis** sem coleta. |
| **Médio/Grande** | 81-150 | 15 dias corridos | 1 dia útil | Alerta se **> 1 dia útil** sem coleta. |
| **Grande** | > 150 | 5 dias úteis | 1 dia útil | Alerta se **> 1 dia útil** sem coleta. |

> [!NOTE]
> O sistema considera **dias úteis** para a contagem mínima, mas tem um **"teto" em dias corridos** para evitar falsos negativos em feriados prolongados.

**Código**: Função `avaliar_risco_por_dias_sem_coleta()` em [`porte_laboratorio.py:168-230`](file:///f:/Progamação/ChurnAi/porte_laboratorio.py#L168-L230)

---

### 2.3. Regras de Perda (Churn)

Define quando um cliente é considerado **perdido**. Existem dois tipos de perda:

#### Perda Recente (Até 6 meses)

Considera-se perda recente quando o laboratório atinge os critérios abaixo **dentro de uma janela de até 180 dias corridos**.

| Categoria / Porte | Critério Mínimo | Critério Máximo (Teto) |
|-------------------|-----------------|------------------------|
| **Pequeno** | 30 dias corridos | 180 dias corridos |
| **Médio** | 15 dias corridos | 180 dias corridos |
| **Médio/Grande** | 15 dias corridos | 180 dias corridos |
| **Grande** | 5 dias úteis | 180 dias corridos |

#### Perda Antiga (Mais de 6 meses)

| Categoria | Critério |
|-----------|----------|
| **Perda Antiga** | **> 180 dias corridos** sem coleta (Todos os portes) |

**Código**: Função `classificar_perda_por_dias_sem_coleta()` em [`porte_laboratorio.py:233-305`](file:///f:/Progamação/ChurnAi/porte_laboratorio.py#L233-L305)

---

## 3. Guia das Telas do Sistema 🖥️

O sistema conta com 6 telas principais acessíveis pelo menu lateral:

### 📅 Tela 1: Fechamento Semanal

**Objetivo**: Monitoramento tático semanal (WoW - Week over Week).

**Métricas Principais**:
- **Volume Semana Atual** - Total de coletas da semana ISO corrente
- **Volume Semana Anterior** - Total da semana ISO anterior
- **Variação WoW (%)** - Crescimento ou queda semanal
- **Média Semanal 2024/2025** - Comparativo anual

**Visualizações**:
- Cards com totais e variações percentuais
- Gráfico de evolução semanal (últimas 12 semanas)
- Lista de risco: laboratórios com queda WoW > 20%

**Colunas da Tabela "Lista de Risco"**:
| Coluna | Descrição |
|--------|-----------|
| **Lab** | Nome fantasia do laboratório |
| **Rede** | Rede/grupo econômico associado |
| **UF** | Estado do laboratório |
| **Porte** | Classificação de tamanho (Pequeno/Médio/Médio-Grande/Grande) |
| **VIP** | Indicador se é cliente estratégico |
| **Última Coleta** | Data da última coleta registrada |
| **Dias Off** | Dias úteis consecutivos sem coleta |
| **Vol. Semana Anterior** | Volume de coletas da semana ISO anterior |
| **Vol. Semana Atual** | Volume de coletas da semana ISO atual |
| **Variação WoW (%)** | 🔴 **COLUNA PRINCIPAL** - Percentual de variação semanal |
| **Média Semanal 2025** | Média de coletas por semana em 2025 |
| **Var. % vs Média 2025** | Variação da semana atual vs média 2025 |
| **Média Top-3 2025** | Média dos 3 maiores meses de 2025 |
| **Var. % vs Top-3 2025** | Variação vs baseline de 2025 |
| **Média Semanal 2024** | Média de coletas por semana em 2024 |
| **Var. % vs Média 2024** | Variação da semana atual vs média 2024 |
| **Média Top-3 2024** | Média dos 3 maiores meses de 2024 |
| **Var. % vs Top-3 2024** | Variação vs baseline de 2024 |
| **Var. % vs Estado** | Variação vs média do estado na semana atual |
| **Em Risco?** | Indica se aplica regra de risco (queda ≥50% ou dias off conforme porte) |

**Uso**: Identificar quedas bruscas de volume na semana corrente para ação imediata.

---

### 📊 Tela 2: Fechamento Mensal

**Objetivo**: Consolidação do mês corrente vs baseline e histórico.

**Métricas Principais**:
- **Volume Mês Atual** - Total de coletas até a data atual
- **Volume Mês Anterior** - Total do mês anterior completo
- **Baseline Mensal** - Média dos Top-3 maiores meses (2024+2025)
- **Var. vs Baseline (%)** - Distância da meta de referência
- **Var. vs Mês Anterior (%)** - Crescimento mensal
- **Projeção de Fechamento** - Estimativa para fim do mês

**Visualizações**:
- Cards com totais e variações
- Gráfico de evolução diária do mês
- Comparativo 2024 vs 2025 (mensal)

**Uso**: Acompanhar o resultado macro do mês e tendências de longo prazo.

> [!TIP]
> A **Baseline Mensal** é individualizada por laboratório, pegando a média dos 3 maiores meses de 2024+2025. Essa métrica é mais robusta contra sazonalidades.

---

### 📋 Tela 3: Análise Detalhada

**Objetivo**: Drill-down individual por laboratório.

**Seleção**: Busca por Nome Fantasia ou CNPJ.

**Métricas Exibidas**:
- **Total Coletas 2024/2025** - Comparativo anual
- **Média Mensal 2024/2025** - Volume médio por mês
- **Baseline Mensal** - Referência de performance
- **Dias sem Coleta** - Inatividade operacional
- **Porte** - Classificação (Pequeno/Médio/Médio-Grande/Grande)
- **WoW (%)** - Variação semanal
- **Preços (3Tox/Trich/STI/Normal)** - Tabela de preços atual

**Visualizações**:
- Gráfico de evolução mensal (2024 vs 2025)
- Tabela "Evolução do Mês (Semana a Semana)"
- Dados de contato e logística

**Colunas da Tabela "Evolução do Mês"**:
| Coluna | Descrição |
|--------|-----------|
| **Semana** | Número da semana ISO do mês |
| **Data Início** | Primeiro dia da semana |
| **Data Fim** | Último dia da semana |
| **Volume** | Total de coletas da semana |
| **Volume Anterior** | Coletas da mesma semana no mês anterior |
| **Var. %** | Variação percentual vs mês anterior |
| **Dias Úteis** | Quantidade de dias úteis na semana |
| **Média/Dia** | Média de coletas por dia útil |

**Uso**: Investigar comportamento individual de um cliente específico.

---

### 🏢 Tela 4: Ranking de Rede

**Objetivo**: Visão consolidada de grupos econômicos e franquias.

**Métricas por Rede**:
- **Volume Total Rede** - Soma de todos os labs da rede
- **Número de Laboratórios** - Quantidade de unidades
- **Labs em Risco** - Quantidade com queda > 20%
- **Média por Lab** - Volume médio distribuído
- **Ranking Interno** - Classificação (Bronze/Prata/Ouro/Diamante)

**Visualizações**:
- Tabela ranking ordenada por volume
- Detalhamento por laboratório dentro da rede

**Colunas da Tabela "Ranking"**:
| Coluna | Descrição |
|--------|-----------|
| **Rede** | Nome da rede/grupo econômico |
| **Ranking** | Classificação interna (Bronze/Prata/Ouro/Diamante) |
| **Volume Total** | Soma de coletas de todos os labs da rede |
| **Nº Labs** | Quantidade de laboratórios na rede |
| **Labs em Risco** | Quantidade de labs com queda > 20% |
| **Média por Lab** | Volume médio por laboratório |
| **Maior Lab** | Nome do laboratório com maior volume da rede |
| **UF Principal** | Estado com maior concentração de labs |

**Uso**: Gestão de contas estratégicas e redes consolidadas.

---

### 🔧 Tela 5: Manutenção VIPs

**Objetivo**: Gestão administrativa de clientes estratégicos.

**Funcionalidades**:
- Cadastro de novos VIPs
- Edição de informações (Rede, Ranking, Contato)
- Exclusão de registros
- Visualização de lista completa

**Dados Gerenciados**:
- CNPJ (identificador único)
- Nome Fantasia
- Rede associada
- Ranking (Bronze/Prata/Ouro/Diamante)
- Contato responsável
- Observações

**Uso**: Manter base de clientes VIP atualizada para filtros e análises.

---

### 🔍 Tela 6: Análise de Concorrente

**Objetivo**: Inteligência competitiva (Gralab).

**KPIs Principais**:
- **Total Gralab** - CNPJs na base do concorrente
- **Total Nossa Base** - CNPJs na nossa base
- **Labs em Comum** - Clientes compartilhados (overlap)
- **Exclusivos Nossos** - Oportunidade de blindagem
- **Exclusivos Concorrente** - Oportunidade de prospecção

**Abas de Análise**:
1. **Visão Geral** - KPIs consolidados
2. **Em Comum** - Lista de labs atendidos por ambos
3. **Exclusivos Nossos** - Labs apenas na nossa base
4. **Exclusivos Gralab** - Labs apenas no concorrente
5. **Movimentações** - Credenciamentos/descredenciamentos

**Colunas das Tabelas de Análise**:

*Tabela "Em Comum"*:
| Coluna | Descrição |
|--------|-----------|
| **CNPJ** | CNPJ do laboratório |
| **Nome** | Razão social ou nome fantasia |
| **UF** | Estado do laboratório |
| **Nossa Base** | Indicador de presença na nossa base |
| **Gralab** | Indicador de presença na base concorrente |
| **Volume 2025** | Coletas em 2025 (nossa base) |
| **Status** | Situação atual (Ativo/Inativo) |

*Tabela "Exclusivos"* (Nossa Base / Gralab):
| Coluna | Descrição |
|--------|-----------|
| **CNPJ** | CNPJ do laboratório |
| **Nome** | Razão social ou nome fantasia |
| **UF** | Estado do laboratório |
| **Cidade** | Município |
| **Volume 2025** | Coletas em 2025 (quando aplicável) |
| **Última Coleta** | Data da última movimentação |

**Uso**: Identificar ameaças competitivas e oportunidades de mercado.

---

## 4. Filtros Globais 🔍

Disponíveis na barra lateral para segmentar qualquer análise:

| Filtro | Descrição |
|--------|-----------|
| **Apenas VIP** | Filtra clientes estratégicos |
| **Representante** | Filtra carteira por executivo de contas |
| **Estado (UF)** | Filtro geográfico por estado |
| **Cidade** | Filtro geográfico por município |
| **Risco Diário** | Filtra por severidade (Normal, Atenção, Risco Alto, Perda) |
| **Ranking Rede** | Filtra por classificação interna (Bronze, Prata, Ouro, Diamante) |
| **Porte** | Filtra por tamanho do laboratório (Pequeno, Médio, Médio/Grande, Grande) |

---

---

## 5. Configurações do Sistema ⚙️

Principais parâmetros configuráveis em [`config_churn.py`](file:///f:/Progamação/ChurnAi/config_churn.py):

| Parâmetro | Valor Padrão | Descrição |
|-----------|--------------|-----------|
| `BASELINE_TOP_N` | 3 | Número de meses usados no cálculo da baseline |
| `REDUCAO_BASELINE_RISCO_ALTO` | 0.50 (50%) | Limiar de queda vs baseline para risco alto |
| `PORTE_PEQUENO_MAX` | 40 | Limite superior para porte Pequeno |
| `PORTE_MEDIO_MAX` | 80 | Limite superior para porte Médio |
| `PORTE_MEDIO_GRANDE_MAX` | 150 | Limite superior para porte Médio/Grande |
| `PERDA_ANTIGA_LIMITE_CORRIDOS` | 180 | Dias corridos para classificar perda como antiga |

---

## 6. Exportação de Dados 📤

O sistema gera arquivos CSV/Excel com os seguintes datasets:

1. **Base Completa Churn**: Todas as métricas calculadas por laboratório
2. **Lista de Risco Semanal**: Laboratórios em situação de atenção
3. **Perdas Recentes/Antigas**: Segregação de churns por categoria
4. **Ranking de Redes**: Consolidação por grupo econômico
5. **Análise de Concorrente**: Comparação com base Gralab

---

## Referências Técnicas 🔧

- **Módulo de Porte**: [`porte_laboratorio.py`](file:///f:/Progamação/ChurnAi/porte_laboratorio.py)
- **Gerador de Dados**: [`gerador_dados_churn.py`](file:///f:/Progamação/ChurnAi/gerador_dados_churn.py)
- **Interface Streamlit**: [`app_streamlit_churn.py`](file:///f:/Progamação/ChurnAi/app_streamlit_churn.py)
- **Configurações**: [`config_churn.py`](file:///f:/Progamação/ChurnAi/config_churn.py)

---

**Última Atualização**: 02/12/2025  
**Versão do Sistema**: V2.0
