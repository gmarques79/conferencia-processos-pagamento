# Script PowerShell para iniciar o Frontend (React + Vite)
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "Iniciando Frontend: Conferência de Processos de Pagamento" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

Set-Location -Path "$PSScriptRoot\frontend"

if (-not (Test-Path "node_modules")) {
    Write-Host "Instalando dependências do Node.js..." -ForegroundColor Yellow
    npm install
}

Write-Host "Iniciando servidor Vite..." -ForegroundColor Green
npm run dev
