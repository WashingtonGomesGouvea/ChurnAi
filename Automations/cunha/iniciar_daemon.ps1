# ================================================================================
#              SCRIPT DE INICIALIZAÇÃO - COLETA AUTOMÁTICA GRALAB
# ================================================================================
#
# Este script inicia o modo daemon para coleta automática às 23:00 todos os dias
#
# DETECÇÃO AUTOMÁTICA DE MÁQUINA:
#   - PC Casa (Ryzen 7 7500X): 16 threads padrão, D:\OneDrive...
#   - Notebook Synvia (i7-1165G7): 8 threads padrão, C:\Users\washington.gouvea\OneDrive...
#
# USO:
#   .\iniciar_daemon.ps1              # Execução normal (threads automáticas)
#   .\iniciar_daemon.ps1 -Threads 24  # Com threads personalizadas
#
# IMPORTANTE: Mantenha esta janela aberta para execução contínua
#             Pressione Ctrl+C para interromper
#
# ================================================================================

param(
    [int]$Threads = 0  # 0 = usar detecção automática
)

# Mudar para diretório do projeto
Set-Location "F:\Progamação\ChurnAi"

Write-Host ""
Write-Host "="*80 -ForegroundColor Cyan
Write-Host "             INICIANDO MODO DAEMON - GRALAB" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor Cyan
Write-Host ""
Write-Host "⏰ Horário de execução: 23:00 (diariamente)" -ForegroundColor Green

if ($Threads -eq 0) {
    Write-Host "🖥️  Detecção automática: Máquina, diretório e threads" -ForegroundColor Green
} else {
    Write-Host "🧵 Threads personalizadas: $Threads" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "💡 Mantenha esta janela aberta" -ForegroundColor Yellow
Write-Host "   Pressione Ctrl+C para interromper" -ForegroundColor Yellow
Write-Host ""
Write-Host "="*80 -ForegroundColor Cyan
Write-Host ""

# Executar daemon
if ($Threads -eq 0) {
    # Usar detecção automática
    python Automations/cunha/cunhaLabV2.py --daemon
} else {
    # Usar threads personalizadas
    python Automations/cunha/cunhaLabV2.py --daemon --threads=$Threads
}

Write-Host ""
Write-Host "Daemon encerrado." -ForegroundColor Yellow
Read-Host "Pressione Enter para fechar"

