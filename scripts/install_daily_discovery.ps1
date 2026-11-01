# Run from the repository root in PowerShell.
# Creates a daily task that runs only while this Windows user is logged in.
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$EnvFile = Join-Path $Root ".env"

if (-not (Test-Path $Python)) {
    throw "Virtual environment not found at $Python. Create it and install requirements first."
}
if (-not (Test-Path $EnvFile)) {
    throw ".env not found. Copy .env.example to .env and configure EXA_API_KEY first."
}

$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

$TaskName = "LinkPilot Daily Public Discovery"
$Arguments = '-m linkpilot.batch_discovery --location "Delhi NCR" --max-results-per-role 5'
$Action = New-ScheduledTaskAction -Execute $Python -Argument $Arguments -WorkingDirectory $Root
$Trigger = New-ScheduledTaskTrigger -Daily -At "9:00AM"
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 45) -MultipleInstances IgnoreNew
$Principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Daily public professional-profile discovery for companies saved in LinkPilot AI." -Force | Out-Null

Write-Host "Created task: $TaskName"
Write-Host "Runs daily at 9:00 AM while you are logged in and your PC is awake."
Write-Host "Logs: $LogDir\ daily-discovery.log"
Write-Host "To run immediately: Start-ScheduledTask -TaskName '$TaskName'"
