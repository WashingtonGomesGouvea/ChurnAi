# Scraper de Laboratórios DB Toxicológico - dbLabV2

## 🔧 Configuração

### Requisitos

Instale as dependências usando o arquivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

Ou instale manualmente:

```bash
pip install requests pandas openpyxl tqdm matplotlib seaborn schedule
```

**Nota**: Este script não requer variáveis de ambiente ou arquivo `.env`, pois utiliza a API pública do Sodre.

## 🚀 Uso

```bash
# Executar o script (detecta automaticamente se já rodou hoje)
python dbLabV2.py
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

## 🔗 API Utilizada

Este script utiliza a API pública do Sodre:
- **Endpoint**: `https://li-sodretox-af-cidades.azurewebsites.net/api/BuscarPostos`
- **Parâmetros**: `cidade={nome}%20-%20{UF}&finalidade=CNH`
- **Autenticação**: Não requerida (API pública)

