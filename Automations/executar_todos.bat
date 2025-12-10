@echo off
REM Run all pipelines in sequence (keeps window open while scheduler loops)

pushd "%~dp0.."
python Automations\executar_todos.py
popd

pause
