# AgenticRAGOCR 一键启动脚本 (Windows PowerShell)
$root = $PSScriptRoot

# 读取后端 .env 中的端口配置（默认 8100）
$backendPort = 8100
$frontendPort = 3000
$envFile = "$root\backend\.env"
if (Test-Path $envFile) {
    $match = Select-String -Path $envFile -Pattern '^PORT=(\d+)' | Select-Object -First 1
    if ($match) { $backendPort = [int]$match.Matches[0].Groups[1].Value }
}
# 读取前端 .env 中的端口配置（默认 3000）
$feEnvFile = "$root\frontend\.env"
if (Test-Path $feEnvFile) {
    $match = Select-String -Path $feEnvFile -Pattern '^VITE_PORT=(\d+)' | Select-Object -First 1
    if ($match) { $frontendPort = [int]$match.Matches[0].Groups[1].Value }
}

Write-Host "[Backend]  Starting on http://localhost:$backendPort ..." -ForegroundColor Cyan
$backend = Start-Process -PassThru -FilePath "$root\backend\.venv\Scripts\python.exe" `
    -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port $backendPort" `
    -WorkingDirectory "$root\backend"

Write-Host "[Frontend] Starting on http://localhost:$frontendPort ..." -ForegroundColor Cyan
$frontend = Start-Process -PassThru -FilePath "cmd.exe" `
    -ArgumentList "/c npm run dev" `
    -WorkingDirectory "$root\frontend"

Write-Host "[OK] Backend PID=$($backend.Id)  Frontend PID=$($frontend.Id)" -ForegroundColor Green
Write-Host "Press Enter to stop all services..."
$null = Read-Host
Stop-Process -Id $backend.Id, $frontend.Id -Force -ErrorAction SilentlyContinue
