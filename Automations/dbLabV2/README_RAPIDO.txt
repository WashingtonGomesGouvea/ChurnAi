================================================================================
                         GUIA RÁPIDO - SODRE SCRAPER
================================================================================

🖥️  DETECÇÃO AUTOMÁTICA DE MÁQUINA
-----------------------------------

O script detecta automaticamente em qual máquina está rodando:

✓ PC CASA (Ryzen 7 7500X)
  - Diretório: D:\OneDrive - Synvia Group\...\cunha
  - Threads: 16 (otimizado para Ryzen)

✓ NOTEBOOK SYNVIA (Intel i7-1165G7) 
  - Diretório: C:\Users\washington.gouvea\OneDrive - Synvia Group\...\cunha
  - Threads: 8 (otimizado para i7)

Detecção baseada em username/hostname do Windows.


⚡ INÍCIO RÁPIDO
----------------

Para iniciar coleta automática diária às 23:00:

    1. Duplo clique em: iniciar_daemon.bat
    
    OU no PowerShell:
    
    2. .\iniciar_daemon.ps1

    OU manualmente:
    
    3. python Automations/cunha/dbLabV2.py --daemon


⏰ HORÁRIO CONFIGURADO: 23:00 (pega dia completo!)


📋 OUTROS COMANDOS ÚTEIS
-------------------------

Executar coleta agora (sem esperar 23h):
    python Automations/cunha/dbLabV2.py

Forçar reprocessamento:
    python Automations/cunha/dbLabV2.py --force

Aumentar velocidade (mais threads):
    python Automations/cunha/dbLabV2.py --threads=24


📊 ARQUIVO EXCEL GERADO
------------------------

Local: D:\OneDrive - Synvia Group\Data Analysis\Churn PCLs\Automations\cunha\
Arquivo: relatorio_completo_laboratorios_sodre.xlsx

Abas:
  ✓ Dados Completos - Todos os labs com preços
  ✓ EntradaSaida - Credenciamentos/Descredenciamentos
  ✓ Resumo Geográfico - Por estado
  ✓ Resumo Credenciamentos - Timeline


🐛 PROBLEMAS?
-------------

"Pipeline já executado" → Use --force
Preços vazios → Delete arquivo CSV e rode novamente
Erro de conexão → Verifique conexão com internet e API do Sodre

Veja COMO_USAR.txt para mais detalhes!


================================================================================
Última atualização: 2025-11-13
================================================================================

