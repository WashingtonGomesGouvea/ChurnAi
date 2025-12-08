@echo off
REM ================================================================================
REM              SCRIPT DE INICIALIZAÇÃO - COLETA AUTOMÁTICA SODRE
REM ================================================================================
REM
REM Este script inicia o modo daemon para coleta automática às 23:00 todos os dias
REM
REM DETECÇÃO AUTOMÁTICA:
REM   - PC Casa (Ryzen): 16 threads, diretório D:\OneDrive...
REM   - Notebook Synvia (i7): 8 threads, diretório C:\Users\washington.gouvea\OneDrive...
REM
REM IMPORTANTE: Mantenha esta janela aberta para execução contínua
REM             Pressione Ctrl+C para interromper
REM
REM ================================================================================

cd /d "F:\Progamação\ChurnAi"

echo.
echo ================================================================================
echo                    INICIANDO MODO DAEMON - SODRE
echo ================================================================================
echo.
echo Horario de execucao: 23:00 (diariamente)
echo Deteccao automatica: Maquina, diretorios e threads
echo.
echo Pressione Ctrl+C para interromper
echo ================================================================================
echo.

python Automations/cunha/dbLabV2.py --daemon

pause

