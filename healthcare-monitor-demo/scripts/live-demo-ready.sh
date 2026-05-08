#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f ".env" ]]; then
  echo "Missing .env. Create it first:"
  echo "  cp .env.example .env"
  echo "  vi .env"
  exit 1
fi

# shellcheck disable=SC1091
set -a
source .env
set +a

SANDBOX="${NEMOCLAW_SANDBOX:-healthcare-monitor}"
PORT="${PORT:-5188}"
HOST="${HOST:-127.0.0.1}"

echo "1/5 Verifying local image build context and deterministic outputs."
./scripts/run-local-verification.sh

echo "2/5 Checking NemoClaw sandbox status."
nemoclaw "$SANDBOX" status >/tmp/healthcare-monitor-nemoclaw-status.txt
grep -E "Sandbox:|Model:|Provider:|Inference:|OpenClaw:|Phase:" /tmp/healthcare-monitor-nemoclaw-status.txt || cat /tmp/healthcare-monitor-nemoclaw-status.txt

echo "3/5 Probing OpenClaw gateway."
nemoclaw "$SANDBOX" connect --probe-only

echo "4/5 Applying local policy."
./scripts/apply-demo-policy.sh

echo "5/5 Starting web app in the background if needed."
if curl -fsS "http://${HOST}:${PORT}/api/config" >/dev/null 2>&1; then
  echo "Web app is already running at http://${HOST}:${PORT}"
else
  nohup env HOST="$HOST" PORT="$PORT" python3 demo-app/server.py > /tmp/healthcare-monitor-app.log 2>&1 &
  sleep 1
  curl -fsS "http://${HOST}:${PORT}/api/config" >/dev/null
  echo "Web app started at http://${HOST}:${PORT}"
  echo "Log: /tmp/healthcare-monitor-app.log"
fi

cat <<EOF

Ready.

Open the web app:
  http://${HOST}:${PORT}

Open the OpenShell TUI in a second terminal:
  cd $ROOT
  ./scripts/open-openshell-tui.sh

Available web app sections:
  01 Runtime Health
  02 Agent Topology
  03 Operator Dashboard
  04 Local Tool Signal
  05 Multi-Agent Plan
  06 Blocked Egress
  07 OpenShell Monitor
  08 Always-On Watch
EOF
