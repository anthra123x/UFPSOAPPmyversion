#!/usr/bin/env bash
# Script para iniciar el servidor de desarrollo UFPSO Horarios & Gestión Académica
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================================="
echo "Iniciando UFPSO Horarios & Gestión Académica"
echo "=================================================="

cd "$PROJECT_DIR"

if [ ! -d ".venv" ]; then
    echo "Creando entorno virtual .venv..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r backend/requirements.txt
fi

export PYTHONPATH="$PROJECT_DIR/backend"

echo "Aplicación Web disponible en: http://localhost:8000"
echo "Documentación interactiva API: http://localhost:8000/docs"
echo "Presiona Ctrl+C para detener."

exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
