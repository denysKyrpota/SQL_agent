#!/usr/bin/env bash
# ==========================================================================
# SQL AI Agent - Install/manage systemd service
# ==========================================================================
#
# Usage:   sudo ./deploy/install-service.sh install
#          sudo ./deploy/install-service.sh remove
#          ./deploy/install-service.sh status
#          ./deploy/install-service.sh logs
#
# Prerequisites:
#   - Python venv at venv/ with dependencies installed
#   - Frontend built to frontend/dist/
#   - .env file configured in project root
#   - Must run install/remove as root (sudo)
# ==========================================================================

set -euo pipefail

SERVICE_NAME="sqlaiagent"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Navigate to project root
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# --------------------------------------------------------------------------
# Parse command
# --------------------------------------------------------------------------
ACTION="${1:-}"

case "$ACTION" in
    install)
        # Check root
        if [ "$(id -u)" -ne 0 ]; then
            echo "[ERROR] Run with sudo: sudo $0 install"
            exit 1
        fi

        # Check prerequisites
        if [ ! -f "$PROJECT_ROOT/venv/bin/python" ]; then
            echo "[ERROR] Python venv not found at $PROJECT_ROOT/venv/"
            exit 1
        fi

        if [ ! -f "$PROJECT_ROOT/frontend/dist/index.html" ]; then
            echo "[ERROR] Frontend not built. Run build-and-start.sh first."
            exit 1
        fi

        # Detect the user who owns the project directory
        OWNER=$(stat -c '%U' "$PROJECT_ROOT")
        GROUP=$(stat -c '%G' "$PROJECT_ROOT")

        echo "[INFO] Installing $SERVICE_NAME as systemd service..."
        echo "[INFO] Running as user: $OWNER, group: $GROUP"

        cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=SQL AI Agent - Natural language to SQL generation
After=network.target

[Service]
Type=simple
User=$OWNER
Group=$GROUP
WorkingDirectory=$PROJECT_ROOT
Environment=PATH=$PROJECT_ROOT/venv/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=$PROJECT_ROOT/.env
ExecStart=$PROJECT_ROOT/venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

        systemctl daemon-reload
        systemctl enable "$SERVICE_NAME"
        systemctl start "$SERVICE_NAME"

        echo "[INFO] Service installed and started."
        echo "[INFO] Access at http://0.0.0.0:8000"
        echo ""
        echo "  Status:   sudo systemctl status $SERVICE_NAME"
        echo "  Logs:     sudo journalctl -u $SERVICE_NAME -f"
        echo "  Restart:  sudo systemctl restart $SERVICE_NAME"
        echo "  Stop:     sudo systemctl stop $SERVICE_NAME"
        ;;

    remove)
        if [ "$(id -u)" -ne 0 ]; then
            echo "[ERROR] Run with sudo: sudo $0 remove"
            exit 1
        fi

        echo "[INFO] Stopping and removing $SERVICE_NAME..."
        systemctl stop "$SERVICE_NAME" 2>/dev/null || true
        systemctl disable "$SERVICE_NAME" 2>/dev/null || true
        rm -f "$SERVICE_FILE"
        systemctl daemon-reload
        echo "[INFO] Service removed."
        ;;

    status)
        systemctl status "$SERVICE_NAME" --no-pager
        ;;

    logs)
        journalctl -u "$SERVICE_NAME" -f
        ;;

    *)
        echo "Usage: $0 {install|remove|status|logs}"
        exit 1
        ;;
esac
