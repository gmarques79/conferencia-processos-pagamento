# Script PowerShell para iniciar o Backend (FastAPI)
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "Iniciando Backend: Conferência de Processos de Pagamento" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

Set-Location -Path "$PSScriptRoot\backend"

if (-not (Test-Path ".venv")) {
    Write-Host "Criando ambiente virtual Python..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "Ativando ambiente virtual..." -ForegroundColor Green
& ".\.venv\Scripts\Activate.ps1"

Write-Host "Instalando/Verificando dependências..." -ForegroundColor Yellow
& ".\.venv\Scripts\pip.exe" install -r requirements.txt

Write-Host "Iniciando servidor FastAPI na porta 8000..." -ForegroundColor Green
& ".\.venv\Scripts\uvicorn.exe" app.main:app --host 127.0.0.1 --port 8000 --reload
