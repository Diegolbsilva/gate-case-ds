# Cria (ou recria) a tarefa diaria no Agendador de Tarefas do Windows. Rodar uma vez, na raiz do projeto:
#     powershell -ExecutionPolicy Bypass -File agendamento\registrar_tarefa.ps1
#     powershell -ExecutionPolicy Bypass -File agendamento\registrar_tarefa.ps1 -Hora 07:30
# Conferir:  Get-ScheduledTask -TaskName "GATE avaliacao diaria" | Get-ScheduledTaskInfo
# Rodar ja:  Start-ScheduledTask -TaskName "GATE avaliacao diaria"
# Remover:   Unregister-ScheduledTask -TaskName "GATE avaliacao diaria" -Confirm:$false
param([string]$Hora = "09:00")
$nome = "GATE avaliacao diaria"
$script = Join-Path $PSScriptRoot "executar_agendado.ps1"
$acao = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$script`""
$gatilho = New-ScheduledTaskTrigger -Daily -At $Hora
# StartWhenAvailable: se o computador estava desligado no horario, roda assim que ligar.
# Limite de 2 h: uma execucao leva cerca de 20 min; acima disso, algo travou e a tarefa e encerrada.
# MultipleInstances IgnoreNew: nunca duas execucoes ao mesmo tempo no mesmo banco.
$config = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $nome -Action $acao -Trigger $gatilho -Settings $config -Force `
    -Description "GATE/MPRJ: coleta, avaliacao e score diarios dos portais da transparencia (coletor.executar --origem agendada)" | Out-Null
Write-Host "Tarefa '$nome' criada: todo dia as $Hora. Log de cada execucao em dados\logs\."
