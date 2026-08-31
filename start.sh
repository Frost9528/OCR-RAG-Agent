#!/bin/bash
# AgenticRAGOCR 一键启动脚本 (Linux/Mac)
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

# 读取后端 .env 中的端口配置（默认 8100）
BACKEND_PORT=8100
FRONTEND_PORT=3000
ENV_FILE="$ROOT/backend/.env"
if [ -f "$ENV_FILE" ]; then
  _port=$(grep -E '^PORT=' "$ENV_FILE" | head -1 | cut -d= -f2)
  [ -n "$_port" ] && BACKEND_PORT="$_port"
fi
# 读取前端 .env 中的端口配置（默认 3000）
FRONTEND_ENV="$ROOT/frontend/.env"
if [ -f "$FRONTEND_ENV" ]; then
  _fport=$(grep -E '^VITE_PORT=' "$FRONTEND_ENV" | head -1 | cut -d= -f2)
  [ -n "$_fport" ] && FRONTEND_PORT="$_fport"
fi

echo "[Backend]  Starting on http://localhost:${BACKEND_PORT} ..."
cd "$ROOT/backend"
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" &
BACKEND_PID=$!

echo "[Frontend] Starting on http://localhost:${FRONTEND_PORT} ..."
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo "[OK] Backend PID=$BACKEND_PID  Frontend PID=$FRONTEND_PID"
echo "Press Ctrl+C to stop all."
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
