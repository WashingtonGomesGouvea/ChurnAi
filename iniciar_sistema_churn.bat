@echo off
echo ========================================
echo    SISTEMA DE ANALISE DE CHURN PCLs
echo ========================================
echo.
echo Iniciando gerador de dados...
start "Gerador Churn" python gerador_dados_churn.py
echo.
echo Aguardando 10 segundos para o gerador inicializar...
timeout /t 10 /nobreak
echo.
echo Iniciando dashboard Streamlit...
start "Dashboard Churn" streamlit run app_streamlit_churn.py --server.port 8502
echo.
echo ========================================
echo    SISTEMA INICIADO COM SUCESSO!
echo ========================================
echo.
echo Dashboard disponivel em: http://localhost:8502
echo.
pause
