# Execucao agendada (secao 2 do enunciado: repetir automaticamente o processo ao longo do tempo).
# Chamado pelo Agendador de Tarefas do Windows (tarefa criada por agendamento\registrar_tarefa.ps1).
# Roda a execucao completa (coleta, avaliacao e score) com origem "agendada" e grava a saida em dados\logs\.
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz
$logs = Join-Path $raiz "dados\logs"
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$log = Join-Path $logs ("agendada_" + (Get-Date -Format "yyyy-MM-dd_HHmm") + ".log")
$env:PYTHONIOENCODING = "utf-8"
& (Join-Path $raiz ".venv\Scripts\python.exe") -m coletor.executar --origem agendada *>&1 | Out-File -FilePath $log -Encoding utf8
exit $LASTEXITCODE
