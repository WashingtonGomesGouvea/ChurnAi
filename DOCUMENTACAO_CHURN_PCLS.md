DOCUMENTAÇÃO TÉCNICA - SISTEMA CHURN PCLS
===========================================

PARTE 1: GLOSSÁRIO DE TERMOS
============================

Antes de entender o sistema, é essencial conhecer o significado de todos os termos e métricas utilizadas. Esta seção explica cada conceito de forma clara.

1. TERMOS FUNDAMENTAIS
----------------------

VOL_HOJE (Volume Hoje)
Definição: Número de coletas registradas no dia atual (data de referência do sistema).
Exemplo: Se hoje é 21/01/2025 e foram registradas 10 coletas, Vol_Hoje = 10.

D-1 (Dia Menos Um)
Definição: Volume de coletas do dia imediatamente anterior ao dia atual.
Exemplo: Se hoje é 21/01/2025, D-1 é o volume de coletas registrado em 20/01/2025.
Se em 20/01/2025 foram registradas 8 coletas, D-1 = 8.

MM7 (Média Móvel de 7 dias)
Definição: Média aritmética simples dos volumes de coletas dos últimos 7 dias.
Inclui o dia atual e os 6 dias anteriores.
Dias sem coleta são contados como zero na média.
Fórmula: MM7 = (Soma dos volumes dos últimos 7 dias) ÷ 7
Exemplo:
Últimos 7 dias: [10, 12, 8, 0, 15, 11, 14] coletas
MM7 = (10 + 12 + 8 + 0 + 15 + 11 + 14) ÷ 7 = 70 ÷ 7 = 10.000

MM30 (Média Móvel de 30 dias)
Definição: Média aritmética simples dos volumes de coletas dos últimos 30 dias.
Inclui o dia atual e os 29 dias anteriores.
Dias sem coleta são contados como zero na média.
Fórmula: MM30 = (Soma dos volumes dos últimos 30 dias) ÷ 30
Exemplo: Se a soma dos últimos 30 dias é 300 coletas, MM30 = 300 ÷ 30 = 10.000

MM90 (Média Móvel de 90 dias)
Definição: Média aritmética simples dos volumes de coletas dos últimos 90 dias.
Usada para análise de longo prazo e comparações sazonais.
Fórmula: MM90 = (Soma dos volumes dos últimos 90 dias) ÷ 90

MM7_BR / MM30_BR (Médias Móveis Nacionais)
Definição: Médias móveis de 7 e 30 dias calculadas com a soma de todos os laboratórios do país, considerando apenas dias úteis (segunda a sexta).
Uso: Referência macro para comparar laboratórios com o comportamento nacional.
Observação: A série é reindexada em calendário business day, com forward-fill antes da média.

MM7_UF / MM30_UF (Médias Móveis por Estado)
Definição: Médias móveis de 7 e 30 dias calculadas para todos os laboratórios da mesma UF, sempre em dias úteis.
Uso: Referência regional para análise de quedas/recuperações.

MM7_CIDADE / MM30_CIDADE (Médias Móveis por Cidade)
Definição: Médias móveis de 7 e 30 dias calculadas para os laboratórios da mesma cidade (quando disponíveis), em dias úteis.
Uso: Contexto local que mostra a curva de comportamento daquele município.

Redução Máxima vs Contextos (Maior_Reducao)
Definição: Percentual de queda do volume do dia em relação às médias móveis disponíveis (MM7_BR, MM7_UF, MM7_CIDADE).
Fórmula Conceitual: Maior_Reducao = max( 1 - Vol_Hoje / MM7_contexto ).
Uso: Determina os limiares de risco diário, usando `REDUCAO_MEDIO_RISCO` (30%) e `REDUCAO_ALTO_RISCO` (50%).

DOW (Day of Week - Dia da Semana)
Definição: Média histórica de coletas para o mesmo dia da semana, calculada com base nos últimos 90 dias.
Por exemplo, se hoje é segunda-feira, DOW é a média de todas as segundas-feiras dos últimos 90 dias.
Serve para normalizar comparações considerando padrões semanais (segundas-feiras podem ter volumes diferentes de sextas-feiras).
Fórmula: DOW = Média dos volumes de todas as ocorrências do mesmo dia da semana nos últimos 90 dias
Exemplo:
Se estamos analisando uma segunda-feira e nos últimos 90 dias houve 13 segundas-feiras com volumes [12, 10, 8, 15, 11, 13, 9, 14, 12, 10, 8, 11, 13]:
DOW = (12 + 10 + 8 + 15 + 11 + 13 + 9 + 14 + 12 + 10 + 8 + 11 + 13) ÷ 13 = 148 ÷ 13 = 11.38

DELTA (Variação Percentual)
Definição: Variação percentual entre dois valores, expressa em porcentagem.
Fórmula geral: Delta = ((Valor Atual - Valor de Referência) ÷ Valor de Referência) × 100
Valor positivo = crescimento
Valor negativo = queda

DELTA_D1 (Delta vs Dia Anterior)
Definição: Variação percentual do volume de hoje comparado com o volume de ontem (D-1).
Fórmula: Delta_D1 = ((Vol_Hoje - Vol_D1) ÷ Vol_D1) × 100
Exemplo:
Vol_Hoje = 14 coletas
Vol_D1 = 11 coletas
Delta_D1 = ((14 - 11) ÷ 11) × 100 = (3 ÷ 11) × 100 = 27.3%
Interpretação: Crescimento de 27.3% em relação ao dia anterior.

DELTA_MM7 (Delta vs Média Móvel de 7 dias)
Definição: Variação percentual do volume de hoje comparado com a média móvel de 7 dias.
Fórmula: Delta_MM7 = ((Vol_Hoje - MM7) ÷ MM7) × 100
Exemplo:
Vol_Hoje = 14 coletas
MM7 = 10.000 coletas
Delta_MM7 = ((14 - 10) ÷ 10) × 100 = (4 ÷ 10) × 100 = 40.0%
Interpretação: Crescimento de 40% em relação à média semanal.

DELTA_MM30 (Delta vs Média Móvel de 30 dias)
Definição: Variação percentual do volume de hoje comparado com a média móvel de 30 dias.
Fórmula: Delta_MM30 = ((Vol_Hoje - MM30) ÷ MM30) × 100
Interpretação: Mostra se o volume atual está acima ou abaixo da tendência mensal.

DELTA_MM90 (Delta vs Média Móvel de 90 dias)
Definição: Variação percentual do volume de hoje comparado com a média móvel de 90 dias.
Usado para análise de longo prazo.

ZEROS_CONSEC (Zeros Consecutivos)
Definição: Número de dias consecutivos sem coletas, contando a partir do dia atual retrocedendo no tempo.
Se hoje teve coleta, zeros_consec = 0.
Se hoje não teve coleta, conta quantos dias consecutivos anteriores também não tiveram coleta.
Exemplo:
Hoje (D0): 0 coletas
D-1: 0 coletas
D-2: 0 coletas
D-3: 5 coletas (última coleta)
zeros_consec = 3 (hoje, D-1 e D-2 não tiveram coletas)

QUEDAS50_CONSEC (Quedas de 50% Consecutivas)
Definição: Número de dias consecutivos (nos últimos 3 dias) em que o volume foi menor que 50% da MM7 local daquele dia.
Para cada dia, calcula a MM7 até aquele dia e verifica se o volume foi menor que 50% dessa média.
Exemplo:
D-2: Volume = 4, MM7 local = 12.0, 50% de MM7 = 6.0, 4 < 6.0? SIM
D-1: Volume = 3, MM7 local = 11.0, 50% de MM7 = 5.5, 3 < 5.5? SIM
Hoje: Volume = 4, MM7 local = 10.0, 50% de MM7 = 5.0, 4 < 5.0? SIM
quedas50_consec = 3 (todos os 3 dias tiveram queda >50%)

RISCO_DIARIO
Definição: Classificação de risco atribuída ao laboratório no dia atual.
Categorias possíveis:
- 🟢 Normal / Estável
- 🟡 Atenção Leve
- 🟠 Risco Moderado
- 🔴 Risco Alto / Agudo
- ⚫ Risco Crítico / Churn Técnico

RECUPERACAO (Flag de Recuperação)
Definição: Indicador booleano que identifica se o laboratório está em processo de recuperação após um período de queda.
Um laboratório está em recuperação se:
- Existem pelo menos 4 dias de dados
- Vol_Hoje está acima ou igual à MM7
- A média dos 3 dias anteriores estava abaixo de 90% da MM7
Exemplo:
Vol_Hoje = 11 coletas
MM7 = 10.000 coletas
Últimos 4 dias: [6, 5, 7, 11] coletas
Média dos últimos 3 dias = (6 + 5 + 7) ÷ 3 = 6.0 coletas
Verificação:
1. Vol_Hoje ≥ MM7? 11 ≥ 10.0? SIM
2. Média dos últimos 3 dias < 90% da MM7? 6.0 < 9.0? SIM
Resultado: Recuperacao = True

CHURN
Definição: Termo que significa "abandono" ou "perda de cliente".
No contexto do sistema, churn técnico ocorre quando um laboratório deixa de operar (sem coletas por período prolongado) ou apresenta quedas severas e consecutivas que indicam possível perda do cliente.

2. CATEGORIAS DE RISCO
----------------------

🟢 NORMAL / ESTÁVEL
Significado: Cliente com comportamento consistente e dentro da faixa normal esperada.
Não requer ação imediata.

🟡 ATENÇÃO LEVE
Significado: Queda leve que pode ser apenas uma oscilação pontual.
Requer monitoramento por alguns dias antes de tomar ação.

🟠 RISCO MODERADO
Significado: Queda moderada que pode indicar início de tendência negativa.
Requer contato da equipe de Customer Success ou comercial em até 48 horas.

🔴 RISCO ALTO / AGUDO
Significado: Queda forte e sustentada que indica problema sério.
Requer ação imediata: contato e revisão de contrato/preço.

⚫ RISCO CRÍTICO / CHURN TÉCNICO
Significado: Cliente possivelmente perdido.
Situação extrema que necessita intervenção imediata.
Requer reunião comercial e plano de recuperação.

PARTE 2: REGRAS DE CATEGORIZAÇÃO DE RISCO
==========================================

### Visão Geral Atualizada

1. O sistema sempre usa **o último dia útil disponível** (business day) como referência para o risco diário. Caso o dataset tenha fim em final de semana, os dias sem coleta são ignorados até o próximo dia útil.
2. As séries diárias (`Dados_Diarios_2025`) são reindexadas em calendário business day com forward-fill antes de calcular médias móveis.
3. Para cada laboratório, calculamos as referências:
   - MM7/MM30 do próprio laboratório (dias úteis).
   - MM7/MM30 nacionais (`MM7_BR`, `MM30_BR`).
   - MM7/MM30 da UF (`MM7_UF`, `MM30_UF`).
   - MM7/MM30 da cidade (`MM7_CIDADE`, `MM30_CIDADE`).
4. O indicador principal passa a ser a **Redução Máxima vs Contextos** (`Maior_Reducao`), que considera a maior queda percentual do volume do dia em relação a cada MM7 de contexto.
5. Os limiares configuráveis `REDUCAO_MEDIO_RISCO` (30%) e `REDUCAO_ALTO_RISCO` (50%) definem os cortes de risco moderado e alto, respectivamente.

### Passos de Classificação

1. **Vol_Hoje:** volume do último dia útil da série business day.
2. **Contextos disponíveis:** filtrar quais médias fazem sentido (somente valores > 0).
3. **Maior_Reducao:** para cada contexto, calcular `1 - (Vol_Hoje / MM7_contexto)` e pegar o maior valor.
4. **Regras críticas:** antes de olhar limiares, verificar se há evento extremo:
   - `Vol_Hoje == 0` com contexto válido ⇒ redução absoluta.
   - `Maior_Reducao ≥ 1.0` (queda de 100%).
   - `zeros_consec ≥ 7` (sete dias úteis consecutivos sem coleta).
   - `quedas50_consec ≥ 3` (três dias consecutivos abaixo de 50% da MM7 local).
5. **Tabela de decisão principal:**

| Risco | Condições | Ação recomendada |
|-------|-----------|------------------|
| ⚫ Crítico | Qualquer condição crítica (zero absoluto, `Maior_Reducao ≥ 1.0`, `zeros_consec ≥ 7`, `quedas50_consec ≥ 3`) | Escalonar imediatamente (churn técnico / atenção máxima). |
| 🔴 Alto | `Maior_Reducao ≥ REDUCAO_ALTO_RISCO` (default 50%) | Intervenção em até 24h; revisar preço/contrato/processos. |
| 🟠 Moderado | `Maior_Reducao ≥ REDUCAO_MEDIO_RISCO` (default 30%) | Contato proativo com CS/comercial em até 48h. |
| 🟡 Atenção | `0 < Maior_Reducao < REDUCAO_MEDIO_RISCO` | Acompanhar por alguns dias; preparar plano de ação. |
| 🟢 Normal | Nenhuma condição acima e sem bandeiras críticas | Monitoramento normal. |

6. `DOW`, `Delta_MM7`, `Delta_D1` e demais deltas continuam disponíveis como métricas auxiliares, mas não interferem mais na régua principal.

### Exemplos Atualizados

- **Laboratório com queda moderada:** Vol_Hoje 70 vs `MM7_BR=110`, `MM7_UF=90`, `MM7_CIDADE=80`. A redução máxima é `1 - 70/110 ≈ 36%` ⇒ risco 🟠 Moderado.
- **Laboratório com operação paralisada:** Vol_Hoje = 0, `MM7_BR>0` ⇒ risco ⚫ Crítico mesmo que médias locais sejam baixas.
- **Laboratório estável:** Vol_Hoje dentro do intervalo das médias (redução ≤ 0) ⇒ risco 🟢 Normal.

### Observações

- `REDUCAO_MEDIO_RISCO` e `REDUCAO_ALTO_RISCO` são configuráveis em `config_churn.py` (padrões 30% e 50%). Ajustar esses valores altera o corte de risco moderado/alto.
- O sistema sempre recalcula os arquivos de saída (`churn_analysis_latest`) com as colunas `MM7_BR`, `MM7_UF`, `MM7_CIDADE`, etc., garantindo que o app consiga reproduzir os mesmos valores.
- A leitura/janela do Streamlit também utiliza os mesmos dados para que KPIs, alertas e dashboards reflitam os limiares atualizados.

PARTE 3: EXPLICAÇÃO TELA POR TELA
==================================

O sistema Churn PCLs possui 4 páginas principais, acessíveis através da barra lateral (sidebar). Cada página é explicada abaixo com seus componentes, cálculos e lógica.

TELA 1: 🏠 VISÃO GERAL
======================

DESCRIÇÃO GERAL
Esta é a tela principal do sistema, exibindo um resumo executivo com KPIs principais e visualizações estratégicas.

COMPONENTES DA TELA

1. CARDS DE KPI (Indicadores Principais)
Localização: Topo da tela (1ª linha com 4 cards) + 2ª linha com indicadores de risco/contexto
O que exibe: Visão executiva da carteira considerando apenas dias úteis (conforme a régua de risco)

Card 1: Labs Monitorados (≤90 dias)
O que mostra: Total de laboratórios que registraram pelo menos uma coleta nos últimos 90 dias.
Cálculo: Contagem de laboratórios onde Dias_Sem_Coleta ≤ 90
Texto adicional: Mostra também "Risco total: X" (labs em risco) e "Recuperação: Y" (labs recuperando)
Lógica: Considera apenas laboratórios ativos recentemente (últimos 90 dias), ignorando laboratórios muito inativos.

Card 2: Coletas Hoje
O que mostra: Soma total de coletas registradas no dia de referência (data atual do sistema).
Cálculo: Soma(Vol_Hoje) de todos os laboratórios
Texto adicional: Mostra também "D-1: X" (volume do dia anterior) e "YTD: Z" (total de coletas em 2025 até agora)
Lógica: Agrega o volume de todos os laboratórios para ter uma visão do volume total do sistema no dia.

Card 3: Labs 🔴 & ⚫ (Alto + Crítico)
O que mostra: Contagem de laboratórios em risco alto ou crítico.
Base: Classificação diária em dias úteis comparando Vol_Hoje com as MM7 de contexto (BR/UF/Cidade).
Texto adicional: Mostra também "⚫ Críticos: X" (apenas os críticos, com queda de 100%/paralisação).
Lógica: Identifica laboratórios que necessitam atenção imediata conforme a nova régua.

Card 4: Sem Coleta (48h)
O que mostra: Laboratórios sem coletas nos últimos 2 dias consecutivos (hoje e D-1).
Cálculo: Contagem onde (Vol_Hoje = 0) E (Vol_D1 = 0) em dias úteis consecutivos.
Texto adicional: Mostra também "Ativos 7D: X%" (percentual de labs com coleta nos últimos 7 dias)
Lógica: Identifica laboratórios que podem estar com problema operacional recente.

Card 5: Distribuição de Risco (dias úteis)
O que mostra: Contagem atualizada de laboratórios por categoria (🟢/🟡/🟠/🔴/⚫) usando a régua com reduções vs. MM7_BR/MM7_UF/MM7_CIDADE.
Lógica: Acompanhamento instantâneo da carteira por nível de criticidade.

Card 6: Labs abaixo da MM7_BR
O que mostra: Quantos laboratórios ficaram abaixo da média móvel nacional (MM7_BR) no último dia útil.
Texto adicional: Percentual em relação ao total monitorado.
Lógica: Mede o quanto a carteira está abaixo da curva nacional.

Card 7: Labs abaixo da MM7_UF
O que mostra: Quantos laboratórios ficaram abaixo da média móvel da própria UF (MM7_UF) no último dia útil.
Texto adicional: Percentual em relação ao total monitorado.
Lógica: Permite avaliar aderência regional às metas.

2. TABS DE VISUALIZAÇÃO
Localização: Abaixo dos cards de KPI
Organização: 5 abas (tabs) diferentes

TAB 1: 📊 RESUMO
O que exibe: Tabela com todos os laboratórios e suas métricas principais.

Colunas exibidas:
- CNPJ_PCL: CNPJ do laboratório (linka para ?cnpj=<valor>, abrindo os detalhes na própria tela)
- Nome_Fantasia_PCL: Nome comercial do laboratório (linka para ?cnpj=<valor>, abrindo os detalhes na própria tela)
- Estado: Estado (UF) onde está localizado
- Cidade: Cidade onde está localizado
- Representante_Nome: Nome do representante responsável
- Vol_Hoje: Volume de coletas do dia atual
- Vol_D1: Volume de coletas do dia anterior
- Delta_D1: Variação percentual vs dia anterior
- MM7: Média móvel de 7 dias (arredondada para 3 casas decimais)
- Delta_MM7: Variação percentual vs MM7
- MM30: Média móvel de 30 dias
- Delta_MM30: Variação percentual vs MM30
- Risco_Diario: Classificação de risco (🟢 Normal, 🟡 Atenção, 🟠 Moderado, 🔴 Alto, ⚫ Crítico)
- Recuperacao: Flag indicando se está em recuperação

Lógica de ordenação: Por padrão, ordenado por Risco_Diario (riscos mais altos primeiro) e depois por Delta_MM7 (maiores quedas primeiro).

Filtros aplicáveis: Todos os filtros da sidebar são aplicados a esta tabela.

TAB 2: 📈 TENDÊNCIAS
O que exibe: Gráficos mostrando tendências de coletas ao longo do tempo.

Gráfico 1: Evolução Mensal (2024 vs 2025)
Tipo: Gráfico de barras agrupadas
Eixo X: Meses do ano (Jan a Dez)
Eixo Y: Número de coletas
Barras: Duas séries - uma para 2024 e outra para 2025
Cálculo: Para cada mês, soma todas as coletas de todos os laboratórios (filtrados) naquele mês.
Fórmula para 2024: Soma de N_Coletas_Jan_24, N_Coletas_Fev_24, etc. de todos os labs
Fórmula para 2025: Soma de N_Coletas_Jan_25, N_Coletas_Fev_25, etc. de todos os labs
Lógica: Compara o desempenho mensal entre anos para identificar tendências.

Gráfico 2: Distribuição por Dia da Semana
Tipo: Gráfico de barras
Eixo X: Dias úteis da semana (Segunda, Terça, Quarta, Quinta, Sexta)
Eixo Y: Número total de coletas (somente dias úteis)
Cálculo: Para cada dia útil da semana, soma todas as coletas registradas naquele dia em 2025 (base business day). Apenas segunda a sexta-feira são considerados.
Lógica: Identifica padrões semanais em dias úteis; sábado e domingo são excluídos dos cálculos e visualizações.

TAB 3: 📊 DISTRIBUIÇÃO
O que exibe: Gráfico de pizza mostrando a distribuição de laboratórios por categoria de risco.

Tipo: Gráfico de pizza (rosca)
Cores: 
- 🟢 Normal: Verde (#16A34A)
- 🟡 Atenção: Amarelo (#F59E0B)
- 🟠 Moderado: Laranja (#FB923C)
- 🔴 Alto: Vermelho (#DC2626)
- ⚫ Crítico: Preto (#111827)

Cálculo: Contagem de laboratórios em cada categoria de Risco_Diario.
Lógica: Dá uma visão rápida da distribuição de risco da carteira.

TAB 4: 🚨 ALTO RISCO
O que exibe: Tabelas e alertas sobre laboratórios em situação crítica.

Seção 1: Alertas de Quedas Severas
Exibe alertas quando há laboratórios com:
- Queda ≥50% vs MM7 E Risco Moderado/Alto/Crítico
- Queda ≥40% vs D-1 E Risco Moderado/Alto/Crítico

Cálculo do alerta 1:
Filtro: (Delta_MM7 ≤ -50) E (Risco_Diario IN {"🟠 Moderado", "🔴 Alto", "⚫ Crítico"})
Ordenação: Por Delta_MM7 (maior queda primeiro)
Limite: Top 15 laboratórios

Cálculo do alerta 2:
Filtro: (Delta_D1 ≤ -40) E (Risco_Diario IN {"🟠 Moderado", "🔴 Alto", "⚫ Crítico"})
Ordenação: Por Delta_D1 (maior queda primeiro)
Limite: Top 15 laboratórios

Lógica: Prioriza laboratórios com quedas severas que já estão em risco, necessitando atenção imediata.

Seção 2: Top 10 Risco Moderado
Exibe: Os 10 laboratórios em Risco Moderado com maiores quedas vs MM7.
Cálculo: Filtra Risco_Diario = "🟠 Moderado" e ordena por Delta_MM7 (maior queda primeiro).
Lógica: Identifica laboratórios que podem escalar para risco alto se a tendência continuar.

TAB 5: 🏆 TOP 100 PCLs
O que exibe: Ranking dos 100 laboratórios com maiores volumes de coletas em 2025.
Cálculo: Soma de todas as colunas N_Coletas_*_25 (todos os meses de 2025) para cada laboratório.
Ordenação: Por total de coletas em ordem decrescente.
Limite: Top 100 laboratórios.

TELA 2: 📋 ANÁLISE DETALHADA
============================

DESCRIÇÃO GERAL
Tela focada em análise aprofundada de laboratórios individuais e comparações detalhadas.

COMPONENTES DA TELA

1. SELETOR DE LABORATÓRIO
Localização: Topo da tela
O que é: Dropdown (caixa de seleção) para escolher um laboratório específico.
Opções: Lista de todos os laboratórios (aplicando os filtros da sidebar).

2. MÉTRICAS DO LABORATÓRIO SELECIONADO
Localização: Abaixo do seletor
O que exibe: Cards com métricas específicas do laboratório selecionado.

Card 1: Volume Hoje
O que mostra: Vol_Hoje do laboratório
Informações adicionais: Comparação com MM7 e MM30

Card 2: Médias Móveis
O que mostra: MM7, MM30 e MM90 do laboratório
Cálculo: Conforme explicado no glossário

Card 3: Variações Percentuais
O que mostra: Delta_MM7, Delta_MM30, Delta_D1
Cálculo: Conforme fórmulas do glossário

Card 4: Classificação de Risco
O que mostra: Risco_Diario atual
Informações adicionais: Histórico de riscos (se disponível)

3. TABS DE ANÁLISE DETALHADA
Localização: Abaixo das métricas
Organização: 3 abas

TAB 1: 📈 EVOLUÇÃO MENSUAL
O que exibe: Gráfico de barras comparando 2024 vs 2025 mês a mês.
Tipo: Gráfico de barras agrupadas
Eixo X: Meses (Jan a Dez)
Eixo Y: Número de coletas
Séries: 2024 e 2025
Cálculo: Para cada mês, pega N_Coletas_Mes_24 e N_Coletas_Mes_25 do laboratório selecionado.
Lógica: Mostra se o laboratório está crescendo, mantendo ou diminuindo volume mensal.

TAB 2: 📊 DISTRIBUIÇÃO SEMANAL
O que exibe: Gráfico mostrando distribuição de coletas por dia da semana.
Tipo: Gráfico de barras
Eixo X: Dias da semana
Eixo Y: Número de coletas (dias úteis)
Cálculo: Soma todas as coletas registradas em cada dia da semana em 2025 para o laboratório selecionado.
Dados: Vem da coluna Dados_Semanais_2025 (JSON com distribuição por dia da semana).

TAB 3: 📉 EVOLUÇÃO DIÁRIA
O que exibe: Gráfico de linha mostrando coletas dia a dia.
Tipo: Gráfico de linha
Eixo X: Datas (dias úteis do ano)
Eixo Y: Número de coletas (considerando calendário empresarial)
Cálculo: Extrai dados da coluna Dados_Diarios_2025 (JSON com estrutura {ano-mês: {dia: coletas}}).
Lógica: Mostra padrões diários, identificando dias sem coleta e tendências.

4. TABELAS DE COMPARAÇÃO
Localização: Abaixo dos gráficos (em abas separadas)

TABELA 1: 📉 Maiores Quedas vs MM7
O que exibe: Laboratórios com maiores quedas percentuais em relação à MM7.
Filtro: Delta_MM7.notna() (apenas labs com dados)
Ordenação: Por Delta_MM7 (menor valor primeiro = maior queda)
Limite: Top 10 laboratórios
Colunas: Nome, Estado, Vol_Hoje, Vol_D1, Delta_D1, MM7, Delta_MM7, Risco_Diario, Recuperacao
Lógica: Identifica laboratórios com declínio estrutural significativo.

TABELA 2: 📈 Altas vs MM7
O que exibe: Laboratórios com maiores altas percentuais em relação à MM7.
Filtro: Delta_MM7 > 0 (apenas crescimentos)
Ordenação: Por Delta_MM7 decrescente (maior alta primeiro)
Limite: Top 10 laboratórios
Lógica: Identifica laboratórios em crescimento ou recuperação.

TABELA 3: 🔁 Recuperações em Andamento
O que exibe: Laboratórios que estão em processo de recuperação.
Filtro: Recuperacao == True AND Delta_MM7.notna()
Ordenação: Por Delta_MM7 decrescente (maior recuperação primeiro)
Limite: Top 10 laboratórios
Lógica: Destaca laboratórios que voltaram a operar acima da MM7 após período de queda.

EXEMPLO PRÁTICO - TABELA DE QUEDAS
Dados do laboratório:
- Vol_Hoje = 3 coletas
- MM7 = 0.429 coletas

Cálculo do Delta_MM7:
Delta_MM7 = ((3 - 0.429) ÷ 0.429) × 100
Delta_MM7 = (2.571 ÷ 0.429) × 100
Delta_MM7 = 6.00 × 100
Delta_MM7 = 600%

Interpretação: O laboratório coletou aproximadamente 7 vezes mais que sua média semanal, indicando recuperação de operação (provavelmente voltou a operar após período de inatividade).

TELA 3: 🏢 RANKING REDE
========================

DESCRIÇÃO GERAL
Tela focada em análise por rede de laboratórios, agrupando dados por rede/comunidade.

COMPONENTES DA TELA

1. FILTRO DE REDE
Localização: Topo da tela
O que é: Dropdown para selecionar uma rede específica.
Fonte de dados: Coluna "Rede" do arquivo VIP (matriz_cs_normalizada.csv).

2. MÉTRICAS DA REDE
Localização: Abaixo do filtro
O que exibe: Cards com métricas agregadas da rede selecionada.
Cálculo: Agrega (soma) todas as métricas dos laboratórios que pertencem à rede selecionada.
Métricas: Total de labs na rede, Total de coletas, Labs em risco, etc.

3. RANKING DE LABORATÓRIOS DA REDE
Localização: Abaixo das métricas
O que exibe: Tabela ordenada por ranking dentro da rede.
Ordenação: Por Ranking_Rede (Bronze, Prata, Ouro, Diamante) e depois por volume.
Dados: Vem do arquivo VIP que contém informações de ranking.

TELA 4: 🔧 MANUTENÇÃO VIPs
==========================

DESCRIÇÃO GERAL
Tela para gerenciar a lista de laboratórios VIP (clientes prioritários).

COMPONENTES DA TELA

1. VISUALIZAÇÃO DA MATRIZ VIP
O que exibe: Tabela editável com todos os laboratórios VIP.
Colunas: CNPJ, Ranking, Ranking_Rede, Rede
Fonte: Arquivo CSV matriz_cs_normalizada.csv

2. FUNCIONALIDADES
- Adicionar novo VIP: Formulário para incluir novo laboratório na lista VIP
- Editar VIP existente: Modificar ranking ou rede de um laboratório
- Remover VIP: Retirar laboratório da lista VIP
- Backup automático: Sistema cria backup antes de alterações

LÓGICA DE FILTRO VIP
Quando o filtro "Apenas VIP" está ativo na sidebar:
- Apenas laboratórios cujo CNPJ está na lista VIP são exibidos
- Normalização de CNPJ: Remove caracteres especiais para comparação (ex: "12.345.678/0001-90" vira "12345678000190")

PARTE 4: FILTROS E FUNCIONALIDADES GLOBAIS
===========================================

FILTROS DISPONÍVEIS NA SIDEBAR
Todos os filtros estão localizados na barra lateral esquerda (sidebar).

Filtro 1: Apenas VIP
Tipo: Toggle (liga/desliga)
O que faz: Mostra apenas laboratórios da lista VIP
Lógica: Filtra por CNPJ normalizado (apenas dígitos)

Filtro 2: Representante
Tipo: Multiselect
O que faz: Restringe os dados aos laboratórios atribuídos aos representantes selecionados.
Lógica: A lista é populada a partir da coluna `Representante_Nome` do dataset filtrado. O filtro opera antes dos KPIs e das demais análises, garantindo consistência nos números exibidos.

Filtro 2: Estado
Tipo: Multiselect (seleção múltipla)
O que faz: Filtra laboratórios por estado (UF)
Opções: Todos os estados brasileiros

Filtro 3: Cidade
Tipo: Multiselect
O que faz: Filtra laboratórios por cidade
Dependência: Depende da seleção de estado

Filtro 4: Representante
Tipo: Multiselect
O que faz: Filtra laboratórios por representante responsável

Filtro 5: Risco Diário
Tipo: Multiselect
O que faz: Filtra por categoria de risco
Opções: 🟢 Normal, 🟡 Atenção, 🟠 Moderado, 🔴 Alto, ⚫ Crítico

Filtro 6: Ranking Rede
Tipo: Multiselect
O que faz: Filtra por ranking dentro da rede
Opções: Bronze, Prata, Ouro, Diamante

Filtro 7: Período de Análise (Mensal)
Tipo: Seleção de ano e meses
O que faz: Filtra dados mensais específicos
Opções: Ano 2024 ou 2025, e meses selecionados

FUNÇÕES GLOBAIS

Botão: 🔄 Atualizar Dados
Localização: Sidebar
O que faz: Limpa o cache e força recarregamento de dados
Lógica: Chama st.cache_data.clear() para invalidar cache

Seção: 📅 Relatórios
Localização: Sidebar (rodapé)
Tipo de Relatório: Dropdown com opções "Semanal" ou "Mensal"
Botão: 📊 Gerar Relatório
O que faz: Gera relatório automático com dados filtrados
Formato: PDF ou Excel (conforme implementação)

PARTE 5: CÁLCULOS E FÓRMULAS COMPLETAS
=======================================

RESUMO DE TODAS AS FÓRMULAS

1. MM7 (Média Móvel de 7 dias)
Fórmula: MM7 = (Soma dos volumes dos últimos 7 dias) ÷ 7
Observação: Inclui dias sem coleta como zero
Arredondamento: 3 casas decimais

2. MM30 (Média Móvel de 30 dias)
Fórmula: MM30 = (Soma dos volumes dos últimos 30 dias) ÷ 30
Observação: Inclui dias sem coleta como zero
Arredondamento: 3 casas decimais

3. MM90 (Média Móvel de 90 dias)
Fórmula: MM90 = (Soma dos volumes dos últimos 90 dias) ÷ 90
Observação: Inclui dias sem coleta como zero
Arredondamento: 3 casas decimais

4. D-1 (Dia Anterior)
Fórmula: D-1 = Volume do dia imediatamente anterior
Observação: Se não há dados do dia anterior, D-1 = 0

5. DOW (Day of Week)
Fórmula: DOW = Média dos volumes de todas as ocorrências do mesmo dia da semana nos últimos 90 dias
Exemplo: Se hoje é segunda-feira, DOW = média de todas as segundas-feiras dos últimos 90 dias
Arredondamento: 1 casa decimal

6. Delta_D1 (Variação vs Dia Anterior)
Fórmula: Delta_D1 = ((Vol_Hoje - Vol_D1) ÷ Vol_D1) × 100
Tratamento de zero: Se Vol_D1 = 0, Delta_D1 = 0.0
Arredondamento: 1 casa decimal

7. Delta_MM7 (Variação vs MM7)
Fórmula: Delta_MM7 = ((Vol_Hoje - MM7) ÷ MM7) × 100
Tratamento de zero: Se MM7 = 0, Delta_MM7 = 0.0
Arredondamento: 1 casa decimal

8. Delta_MM30 (Variação vs MM30)
Fórmula: Delta_MM30 = ((Vol_Hoje - MM30) ÷ MM30) × 100
Tratamento de zero: Se MM30 = 0, Delta_MM30 = 0.0
Arredondamento: 1 casa decimal

9. Delta_MM90 (Variação vs MM90)
Fórmula: Delta_MM90 = ((Vol_Hoje - MM90) ÷ MM90) × 100
Tratamento de zero: Se MM90 = 0, Delta_MM90 = 0.0
Arredondamento: 1 casa decimal

10. Zeros Consecutivos
Fórmula: Conta quantos dias consecutivos (a partir de hoje retrocedendo) tiveram volume = 0
Algoritmo: Se Vol_Hoje = 0, conta quantos dias anteriores consecutivos também tiveram 0

11. Quedas de 50% Consecutivas
Fórmula: Para cada um dos últimos 3 dias, verifica se Vol_Dia < 0.5 × MM7_local_do_dia
Onde MM7_local_do_dia é a MM7 calculada até aquele dia específico
Conta quantos dias consecutivos (nos últimos 3) atenderam essa condição

12. Taxa de Churn
Fórmula: Churn_Rate = (Labs_em_Risco ÷ Total_Labs) × 100
Onde Labs_em_Risco = Labs com Risco_Diario IN {"🟠 Moderado", "🔴 Alto", "⚫ Crítico"}

13. Taxa de Ativos (7D)
Fórmula: Ativos_7D = (Labs com Dias_Sem_Coleta ≤ 7 ÷ Total_Labs) × 100

14. Taxa de Ativos (30D)
Fórmula: Ativos_30D = (Labs com Dias_Sem_Coleta ≤ 30 ÷ Total_Labs) × 100

15. Detecção de Recuperação
Condições:
- Existem pelo menos 4 dias de dados
- Vol_Hoje ≥ MM7
- Média dos últimos 3 dias < 90% da MM7
Fórmula: Recuperacao = True se todas as condições acima forem verdadeiras

EXEMPLO COMPLETO DE CÁLCULO
----------------------------

Cenário: Calcular todas as métricas para um laboratório no dia 21/01/2025

Dados históricos (últimos 30 dias):
Dias 1-23: Volumes variados totalizando 230 coletas
D-6 (15/01): 10 coletas
D-5 (16/01): 12 coletas
D-4 (17/01): 8 coletas
D-3 (18/01): 0 coletas
D-2 (19/01): 15 coletas
D-1 (20/01): 11 coletas
Hoje (21/01): 14 coletas

PASSO 1: Calcular MM7
MM7 = (10 + 12 + 8 + 0 + 15 + 11 + 14) ÷ 7
MM7 = 70 ÷ 7
MM7 = 10.000

PASSO 2: Calcular MM30
MM30 = (230 + 10 + 12 + 8 + 0 + 15 + 11 + 14) ÷ 30
MM30 = 300 ÷ 30
MM30 = 10.000

PASSO 3: Identificar D-1
D-1 = 11 coletas

PASSO 4: Calcular Deltas
Delta_D1 = ((14 - 11) ÷ 11) × 100 = (3 ÷ 11) × 100 = 27.3%
Delta_MM7 = ((14 - 10) ÷ 10) × 100 = (4 ÷ 10) × 100 = 40.0%
Delta_MM30 = ((14 - 10) ÷ 10) × 100 = (4 ÷ 10) × 100 = 40.0%

PASSO 5: Verificar Zeros Consecutivos
Vol_Hoje = 14 (não é zero)
zeros_consec = 0

PASSO 6: Verificar Quedas de 50% Consecutivas
Últimos 3 dias: [15, 11, 14]
MM7 local de D-2: ~12.0, 50% = 6.0, 15 < 6.0? NÃO
MM7 local de D-1: ~11.5, 50% = 5.75, 11 < 5.75? NÃO
MM7 local de hoje: 10.0, 50% = 5.0, 14 < 5.0? NÃO
quedas50_consec = 0

PASSO 7: Classificar Risco
1. Verificar Normal:
   Vol_Hoje ≥ 90% da MM7? 14 ≥ 9.0? SIM ✓
   Vol_Hoje ≤ 120% do D-1? 14 ≤ 13.2? SIM ✓
   Resultado: 🟢 Normal / Estável

PASSO 8: Verificar Recuperação
Últimos 4 dias: [0, 15, 11, 14]
Média dos últimos 3 dias = (15 + 11 + 0) ÷ 3 = 8.67
Verificações:
- Existem 4 dias? SIM ✓
- Vol_Hoje ≥ MM7? 14 ≥ 10.0? SIM ✓
- Média dos últimos 3 < 90% da MM7? 8.67 < 9.0? SIM ✓
Resultado: Recuperacao = True

RESULTADO FINAL:
- MM7: 10.000
- MM30: 10.000
- D-1: 11
- Delta_D1: +27.3%
- Delta_MM7: +40.0%
- Delta_MM30: +40.0%
- Risco_Diario: 🟢 Normal / Estável
- Recuperacao: True

FIM DA DOCUMENTAÇÃO
===================

Esta documentação cobre todos os aspectos do sistema Churn PCLs:
- Glossário completo de termos
- Regras de categorização de risco
- Explicação tela por tela
- Fórmulas e cálculos detalhados
- Exemplos práticos passo a passo

Para dúvidas ou esclarecimentos adicionais, consulte o código-fonte ou entre em contato com a equipe de desenvolvimento.
