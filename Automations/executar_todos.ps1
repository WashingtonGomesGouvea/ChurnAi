# Run all pipelines in sequence and keep the scheduler alive.

$projectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $projectRoot

python Automations\executar_todos.py
