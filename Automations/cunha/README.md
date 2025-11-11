# Scraper de Laboratórios Gralab - cunhaLabV2

## 🔧 Configuração

### Variáveis de Ambiente (IMPORTANTE!)

Este script utiliza Azure Function Keys que **NUNCA devem ser commitadas no Git**.

1. Crie um arquivo `.env` na pasta `Automations/cunha/`
2. Adicione as seguintes variáveis:

```env
# Azure Function Keys - CONCORRENTE GRALAB
AZURE_POSTOS_CODE=sua_key_aqui
AZURE_CIDADES_CODE=sua_key_aqui
```

3. O arquivo `.env` já está no `.gitignore` e não será versionado

### Requisitos

```bash
pip install python-dotenv requests pandas openpyxl tqdm schedule
```

## 🚀 Uso

```bash
# Executar o script (detecta automaticamente se já rodou hoje)
python cunhaLabV2.py
```

O script:
- ✅ Verifica se já coletou dados hoje
- ✅ Gera relatórios Excel automaticamente
- ✅ Atualiza a aba EntradaSaida com movimentações
- ✅ Mantém histórico de credenciamentos/descredenciamentos

## 📊 Relatórios Gerados

1. **EntradaSaida**: Apenas laboratórios com movimentações (credenciamentos/descredenciamentos)
2. **Dados Completos**: Lista completa de todos os laboratórios ativos
3. **Resumo Geográfico**: Distribuição por UF
4. **Resumo Credenciamentos**: Totalizador diário e acumulado

## ⚠️ Segurança

**NUNCA** exponha as Azure Function Keys publicamente. São credenciais do concorrente!

