# ========================================
#    SISTEMA DE ANALISE DE CHURN PCLs
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    SISTEMA DE ANALISE DE CHURN PCLs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se os dados existem
Write-Host "Verificando dados de churn..." -ForegroundColor Yellow
python verificar_dados.py
$dadosExistem = $LASTEXITCODE -eq 0

if (-not $dadosExistem) {
    Write-Host "Dados nao encontrados. Executando gerador de dados..." -ForegroundColor Yellow
    Start-Process python -ArgumentList "gerador_dados_churn.py" -NoNewWindow -Wait
    Write-Host ""
    
    Write-Host "Verificando dados novamente..." -ForegroundColor Yellow
    python verificar_dados.py
    $dadosExistem = $LASTEXITCODE -eq 0
    
    if (-not $dadosExistem) {
        Write-Host "ERRO: Nao foi possivel gerar os dados!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Dados verificados com sucesso!" -ForegroundColor Green
Write-Host ""

Write-Host "Iniciando dashboard Streamlit..." -ForegroundColor Yellow
streamlit run app_streamlit_churn.py --server.port 8502

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "    SISTEMA INICIADO COM SUCESSO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Dashboard disponivel em: http://localhost:8502" -ForegroundColor Cyan
Write-Host ""
