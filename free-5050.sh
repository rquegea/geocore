#!/usr/bin/env bash
set -e
PORT=${1:-5050}
PID=$(lsof -t -iTCP:$PORT -sTCP:LISTEN || true)
if [ -n "$PID" ]; then
  echo "Matando proceso en puerto $PORT: PID $PID"
  kill -9 $PID
  echo "Puerto $PORT liberado."
else
  echo "No hay proceso escuchando en $PORT."
fi
