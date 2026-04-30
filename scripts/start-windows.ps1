$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")

Set-Location $ProjectRoot
docker compose up --build -d

Write-Host "Project Management MVP is running at http://localhost:8000"
