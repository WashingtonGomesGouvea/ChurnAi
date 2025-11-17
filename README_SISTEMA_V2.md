# Sistema de Alertas Churn v2

## 📋 Resumo

Refatoração completa do sistema de alertas de churn, migrando de comparativos D-1 (voláteis) para baseline mensal robusta + WoW + controle por UF, com cap de 30-50 alertas/dia.

## ✅ Implementações Concluídas

### 1. Módulo de Feriados (`feriados_brasil.py`)
- ✅ Feriados nacionais fixos (2024-2026)
- ✅ Feriados móveis (Carnaval, Páscoa, Corpus Christi)
- ✅ Feriados estaduais por UF
- ✅ Funções: `is_feriado()`, `is_dia_util()`, `dias_uteis_entre()`
- ✅ Teste integrado no módulo

**Uso:**
```python
from feriados_brasil import is_dia_util, dias_uteis_entre

# Verificar se é dia útil
if is_dia_util(data, uf='SP'):
    print("É dia útil em SP")

# Contar dias úteis entre datas
dias = dias_uteis_entre(inicio, fim, uf='RJ')
```

### 2. Módulo de Porte (`porte_laboratorio.py`)
- ✅ Classificação: Grande (≥100), Médio (50-99), Pequeno (<50)
- ✅ Baseado em volume médio mensal
- ✅ Funções para aplicar em DataFrame
- ✅ Gatilhos de dias sem coleta por porte:
  - Grande: ≥1 dia útil
  - Médio: ≥2 dias úteis
  - Pequeno: ≥3 dias úteis

**Uso:**
```python
from porte_laboratorio import aplicar_porte_dataframe, aplicar_gatilho_dataframe

# Classificar porte
df = aplicar_porte_dataframe(df, coluna_volume='Media_Coletas_Mensal_2025')

# Aplicar gatilho de dias sem coleta
df = aplicar_gatilho_dataframe(df, coluna_dias='Dias_Sem_Coleta', coluna_porte='Porte')
```

### 3. Configurações (`config_churn.py`)
Novos parâmetros adicionados:

```python
# Baseline mensal
BASELINE_TOP_N = 3  # Top N meses de 2024

# Limiares de risco v2
REDUCAO_BASELINE_RISCO_ALTO = 0.50  # 50%
REDUCAO_WOW_RISCO_ALTO = 0.50  # 50%

# Porte de laboratório
PORTE_GRANDE_MIN = 100  # coletas/mês
PORTE_MEDIO_MIN = 50    # coletas/mês

# Dias sem coleta por porte
DIAS_SEM_COLETA_GRANDE = 1
DIAS_SEM_COLETA_MEDIO = 2
DIAS_SEM_COLETA_PEQUENO = 3

# Cap de alertas
ALERTA_CAP_MIN = 30
ALERTA_CAP_MAX = 50
ALERTA_CAP_DEFAULT = 40

# Concorrência Gralab
GRALAB_JANELA_DIAS = 14

# Pesos de severidade
PESO_PERCENTUAL_QUEDA = 100
PESO_VOLUME_HISTORICO = 50
PESO_DIAS_SEM_COLETA = 30
PESO_BONUS_CONCORRENTE = 50
```

### 4. Motor de Risco Refatorado (`gerador_dados_churn.py`)

#### Baseline Mensal Robusta
- ✅ Calcula média dos top-N meses de 2024 (configurável: 3 ou 6)
- ✅ Menos suscetível a sazonalidade
- ✅ Função: `calcular_baseline_mensal_robusta()`

#### WoW (Week over Week)
- ✅ Comparação semana ISO atual vs anterior
- ✅ Considera apenas dias úteis (excluindo feriados por UF)
- ✅ Função: `calcular_wow_iso()`

#### Classificação de Risco Binária
- ✅ Sistema simplificado: **"Perda (Risco Alto)"** ou **"Normal"**
- ✅ Elimina categorias intermediárias (médio, baixo)
- ✅ Critérios claros:
  1. Queda >50% vs baseline mensal
  2. Queda >50% WoW
  3. Dias sem coleta ≥ limiar por porte

#### Integração Concorrência Gralab
- ✅ Lê aba "EntradaSaida" do Excel do Gralab
- ✅ Janela de 7-14 dias (configurável)
- ✅ Adiciona colunas: `Apareceu_Gralab`, `Gralab_Data`, `Gralab_Tipo`
- ✅ Função: `integrar_dados_gralab()`

#### Controle por UF
- ✅ Alertas segmentados por estado
- ✅ Cap proporcional por UF
- ✅ Considera feriados estaduais

**Novas Colunas Geradas:**
- `Baseline_Mensal`: Baseline robusta
- `WoW_Semana_Atual`: Volume semana atual
- `WoW_Semana_Anterior`: Volume semana anterior
- `WoW_Percentual`: Variação WoW
- `Queda_Baseline_Pct`: % queda vs baseline
- `Porte`: Classificação do laboratório
- `Gatilho_Dias_Sem_Coleta`: Boolean indicando ativação
- `Apareceu_Gralab`: Boolean indicando concorrência
- `Gralab_Data`: Data da aparição
- `Gralab_Tipo`: Tipo de movimentação
- `Status_Risco_V2`: Classificação binária
- `Motivo_Risco_V2`: Descrição do motivo
- `Severidade`: Score de priorização

### 5. Gerenciador de Alertas (`alertas_manager.py`)

#### Ranking de Severidade
- ✅ Score baseado em 4 pesos:
  - Percentual de queda (0-100 pts)
  - Volume histórico (0-50 pts)
  - Dias sem coleta (0-30 pts)
  - Concorrente (+50 pts bonus)

#### Cap de Alertas
- ✅ Limita a 30-50 alertas/dia (configurável)
- ✅ Prioriza por severidade
- ✅ Função: `aplicar_cap_alertas()`

#### Processamento por UF
- ✅ Segmentação automática por estado
- ✅ Cap proporcional por UF
- ✅ Função: `processar_alertas_por_uf()`

#### Relatórios
- ✅ Geração automática de estatísticas
- ✅ Exportação CSV por UF
- ✅ Relatório consolidado formatado

**Arquivos Gerados:**
- `alertas_prioritarios.csv`: Top N alertas mais severos
- `alertas_uf_{UF}.csv`: Alertas por estado

### 6. Backtest (`backtest_alertas.py`)

Sistema completo de validação:
- ✅ Simula N dias úteis passados
- ✅ Testa múltiplos limiares (40%, 45%, 50%, 55%, 60%)
- ✅ Gera relatório CSV com estatísticas
- ✅ Gera gráficos de distribuição
- ✅ Recomenda melhor limiar para atingir 30-50 alertas/dia

**Uso:**
```bash
python backtest_alertas.py
```

**Saídas:**
- `backtest_resultado_{timestamp}.csv`: Estatísticas por limiar
- `backtest_distribuicao_{timestamp}.png`: Gráficos visuais
- Recomendação de limiar ideal no console

**Métricas Calculadas:**
- Média de alertas/dia
- Mediana
- Desvio padrão
- Min/Max
- Percentis (P25, P75, P90, P95)
- Indicador se está dentro da meta

### 7. Interface Streamlit (`app_streamlit_churn.py`)

#### Helpers Amigáveis
- ✅ Dicionário `HELPERS_V2` com tooltips explicativos
- ✅ Funções de exibição:
  - `exibir_bloco_concorrencia()`: Alerta visual de concorrência
  - `exibir_metricas_v2()`: Métricas do sistema v2
  - `exibir_helper_icone()`: Ícones de ajuda

#### Filtros Atualizados
- ✅ **Filtro UF prioritário** na sidebar
- ✅ Opção "Todas" para visão global
- ✅ Aplicação automática nos dados filtrados

#### Wording Atualizado
- ✅ "Possível perda" → "Perda"
- ✅ "Alto Risco" → "Perda (Risco Alto)"
- ✅ Remoção de categorias intermediárias
- ✅ Textos claros e diretos

## 🚀 Como Usar o Sistema v2

### 1. Executar Gerador de Dados

```bash
python gerador_dados_churn.py
```

**O que faz:**
- Extrai dados do MongoDB
- Calcula baseline mensal
- Calcula WoW por laboratório
- Classifica porte
- Integra dados Gralab
- Aplica classificação de risco v2
- Calcula severidade
- Aplica cap de alertas
- Gera alertas por UF
- Salva arquivos CSV/Parquet

**Arquivos gerados:**
- `churn_analysis_latest.parquet`: Análise completa
- `churn_analysis_latest.csv`: Versão CSV
- `alertas_prioritarios.csv`: Top alertas
- `alertas_uf_{UF}.csv`: Alertas por estado

### 2. Executar Backtest (Opcional)

```bash
python backtest_alertas.py
```

**O que faz:**
- Testa diferentes limiares
- Gera relatórios e gráficos
- Recomenda melhor configuração

**Quando executar:**
- Após mudanças nos limiares
- Periodicamente para validar sistema
- Quando alertas estiverem fora da meta (30-50/dia)

### 3. Visualizar no Streamlit

```bash
streamlit run app_streamlit_churn.py
```

**Recursos v2:**
- Filtro por UF na sidebar
- Métricas de baseline e WoW
- Alertas de concorrência
- Helpers explicativos em tooltips
- Classificação binária (Perda/Normal)

## 📊 Critérios de Aceite

✅ **Todos os critérios foram atendidos:**

- [x] D-1 não afeta classificação de risco (existe apenas para analytics)
- [x] Baseline mensal robusta calculada (top-3 de 2024, parâmetro BASELINE_TOP_N)
- [x] WoW funciona com semanas ISO fixas, apenas dias úteis
- [x] Feriados nacionais + UF excluídos do cômputo
- [x] Porte definido e aplicado ao gatilho de dias sem coleta (1/2/3)
- [x] Controle por UF em pipeline e UI
- [x] Cap global de 30-50 alertas/dia com ranking
- [x] Alerta inclui bloco de concorrência (Gralab)
- [x] Backtest gera relatório CSV + gráfico
- [x] Wording: "Perda (Risco Alto)" (sem intermediários)
- [x] Helpers e tooltips em português claro

## 🔧 Ajustes e Configuração

### Ajustar Limiares

Edite `config_churn.py`:

```python
# Para alertas mais sensíveis (mais alertas)
REDUCAO_BASELINE_RISCO_ALTO = 0.40  # 40% ao invés de 50%

# Para alertas menos sensíveis (menos alertas)
REDUCAO_BASELINE_RISCO_ALTO = 0.60  # 60% ao invés de 50%
```

**Recomendado:** Execute backtest após qualquer mudança para validar impacto.

### Ajustar Cap de Alertas

```python
ALERTA_CAP_DEFAULT = 35  # De 40 para 35 alertas/dia
```

### Ajustar Porte de Laboratório

```python
PORTE_GRANDE_MIN = 150  # De 100 para 150 coletas/mês
PORTE_MEDIO_MIN = 75    # De 50 para 75 coletas/mês
```

### Ajustar Janela de Concorrência

```python
GRALAB_JANELA_DIAS = 7  # De 14 para 7 dias
```

## 📈 Monitoramento

### KPIs do Sistema v2

1. **Alertas/Dia**: Deve ficar entre 30-50
2. **Taxa de Falsos Positivos**: Monitorar laboratórios que saíram de risco
3. **Cobertura de Concorrência**: % de alertas com sinal Gralab
4. **Distribuição por UF**: Verificar se há estados sem alertas

### Relatórios Automáticos

O sistema gera automaticamente:
- Relatório consolidado no log
- Estatísticas de severidade
- Distribuição por UF
- Distribuição por porte

## 🐛 Troubleshooting

### "Módulos v2 não disponíveis"

**Causa:** Importação dos módulos falhou.

**Solução:**
1. Verificar se os arquivos existem:
   - `feriados_brasil.py`
   - `porte_laboratorio.py`
   - `alertas_manager.py`
2. Verificar imports no topo de `gerador_dados_churn.py`

### "Arquivo Gralab não encontrado"

**Causa:** Excel do Gralab não está no caminho esperado.

**Solução:**
1. Verificar caminho: `{OUTPUT_DIR}/Automations/cunha/relatorio_completo_laboratorios_gralab.xlsx`
2. Executar script do Gralab: `python Automations/cunha/cunhaLabV2.py`
3. Sistema continua funcionando sem dados Gralab (apenas sem sinal de concorrência)

### "Sem dados para backtest"

**Causa:** Arquivo `churn_analysis_latest.parquet` não existe ou não tem colunas v2.

**Solução:**
1. Executar primeiro: `python gerador_dados_churn.py`
2. Verificar se colunas v2 foram geradas
3. Depois executar: `python backtest_alertas.py`

### Alertas fora da meta (muito alto ou muito baixo)

**Solução:**
1. Executar backtest: `python backtest_alertas.py`
2. Verificar recomendação de limiar
3. Ajustar `REDUCAO_BASELINE_RISCO_ALTO` e `REDUCAO_WOW_RISCO_ALTO`
4. Executar gerador novamente
5. Repetir até atingir meta

## 📚 Arquitetura

```
ChurnAi/
│
├── feriados_brasil.py           # Módulo de feriados
├── porte_laboratorio.py         # Módulo de classificação de porte
├── alertas_manager.py           # Gerenciador de alertas com cap
├── backtest_alertas.py          # Script de validação
│
├── config_churn.py              # Configurações atualizadas
├── gerador_dados_churn.py       # Motor refatorado
├── app_streamlit_churn.py       # Interface atualizada
│
└── {OUTPUT_DIR}/
    ├── churn_analysis_latest.parquet
    ├── alertas_prioritarios.csv
    └── alertas_uf_{UF}.csv
```

## 🎯 Próximos Passos (Futuro)

1. **Feedback Loop**: Rastrear labs que saíram de risco para calcular falsos positivos
2. **Ajuste Automático**: ML para otimizar limiares baseado em histórico
3. **Alertas por E-mail**: Envio automático dos top alertas
4. **Dashboard Executivo**: Visão resumida para gestão
5. **API REST**: Expor alertas via API para integração

## 📝 Changelog

### v2.0.0 (2025-11-14)
- ✅ Sistema de baseline mensal robusta
- ✅ Cálculo WoW com semanas ISO
- ✅ Classificação binária de risco
- ✅ Módulo de feriados nacional + UF
- ✅ Classificação por porte de laboratório
- ✅ Integração dados Gralab
- ✅ Sistema de cap de alertas com severidade
- ✅ Controle por UF
- ✅ Backtest completo
- ✅ Interface atualizada com helpers

## 📧 Suporte

Para dúvidas ou problemas:
1. Verificar logs em `gerador_dados_churn.log`
2. Executar testes dos módulos: `python feriados_brasil.py`
3. Validar dados: `python backtest_alertas.py`

---

**Sistema Syntox Churn v2** - Alertas Inteligentes e Acion

áveis 🚀

