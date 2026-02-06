#!/usr/bin/env bash
# ==========================================================================
# SQL AI Agent - Build Frontend and Start Server
# ==========================================================================
#
# Usage:   ./deploy/build-and-start.sh
#          ./deploy/build-and-start.sh --skip-build   (skip frontend build)
#
# Prerequisites:
#   - Python 3.12+ with venv at venv/
#   - Node.js 20+ (for frontend build)
#   - .env file configured in project root
# ==========================================================================

set -euo pipefail

# Navigate to project root (one level up from deploy/)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"
echo "[INFO] Project root: $PROJECT_ROOT"

# --------------------------------------------------------------------------
# Check prerequisites
# --------------------------------------------------------------------------
if [ ! -f "venv/bin/activate" ]; then
    echo "[ERROR] Python virtual environment not found at venv/"
    echo "[INFO]  Create it with: python3 -m venv venv"
    echo "[INFO]  Then install deps: venv/bin/pip install -r requirements.txt"
    exit 1
fi

# --------------------------------------------------------------------------
# Build frontend (unless --skip-build)
# --------------------------------------------------------------------------
if [ "${1:-}" = "--skip-build" ]; then
    echo "[INFO] Skipping frontend build (--skip-build)"
else
    echo "[INFO] Building frontend..."
    cd frontend
    npm install
    npm run build
    cd ..
    echo "[INFO] Frontend built successfully to frontend/dist/"
fi

# --------------------------------------------------------------------------
# Verify frontend dist exists
# --------------------------------------------------------------------------
if [ ! -f "frontend/dist/index.html" ]; then
    echo "[ERROR] frontend/dist/index.html not found."
    echo "[INFO]  Run this script without --skip-build to build the frontend."
    exit 1
fi

# --------------------------------------------------------------------------
# Activate venv and start server
# --------------------------------------------------------------------------
echo "[INFO] Activating virtual environment..."
source venv/bin/activate

echo "[INFO] Starting SQL AI Agent on http://0.0.0.0:8000"
echo "[INFO] Press Ctrl+C to stop the server."
echo

exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 1
