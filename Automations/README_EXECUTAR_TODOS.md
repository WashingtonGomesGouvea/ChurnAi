# Executor diario dos labs

Orquestra os pipelines `cunha`, `sodreLabV2` e `dbLabV2` em sequencia. Horario padrao: **17:00** todos os dias.

Comportamento principal:
- Se iniciar o orquestrador depois das 17:00 e algum lab ainda nao rodou hoje, ele executa os pendentes imediatamente e agenda a proxima rodada para o dia seguinte as 17:00.
- Se todos ja estiverem marcados como concluido no dia, ele apenas espera ate 17:00 do dia seguinte.
- Usa os mesmos arquivos de flag que cada pipeline cria (`.pipeline_completo_YYYY-MM-DD.flag` para `cunha` e `.pipeline_completo.flag` com linhas por data para `sodre` e `db`).
- Mantem a janela aberta; encerre com `Ctrl+C` quando quiser parar o agendamento.

Como rodar
1) No Windows, execute `Automations\executar_todos.bat` (abre cmd e mantem rodando) ou `Automations\executar_todos.ps1` em um PowerShell.
2) Opcionalmente, rode manualmente a partir da raiz do projeto:  
   `python Automations/executar_todos.py`
3) Deixe a janela aberta; o script cuida do proximo horario automaticamente.

Notas
- O script detecta os mesmos diretorios base usados pelos pipelines (OneDrive em C: ou D: nas maquinas reconhecidas; caso contrario, usa `Automations/dbLabV2/arquivos` e `Automations/sodreLabV2/arquivos`).
- Para mudar o horario, edite `RUN_HOUR` e `RUN_MINUTE` em `Automations/executar_todos.py`.
