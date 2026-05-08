#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "$ROOT/.env" ]]; then
  # shellcheck disable=SC1091
  set -a
  source "$ROOT/.env"
  set +a
fi

MODEL="${NEMOCLAW_MODEL:-nvidia/nvidia/nemotron-3-super-v3}"
ENDPOINT="${NEMOCLAW_ENDPOINT_URL:-https://inference-api.nvidia.com/v1/chat/completions}"
KEY="${NEMOCLAW_PROVIDER_KEY:-${COMPATIBLE_API_KEY:-}}"

if [[ -z "$KEY" ]]; then
  echo "NEMOCLAW_PROVIDER_KEY or COMPATIBLE_API_KEY is required." >&2
  exit 1
fi

if [[ "$ENDPOINT" != */chat/completions ]]; then
  ENDPOINT="${ENDPOINT%/}/chat/completions"
fi

payload="$(mktemp)"
response="$(mktemp)"
trap 'rm -f "$payload" "$response"' EXIT

python3 - "$payload" "$MODEL" <<'PY'
import json
import sys

path, model = sys.argv[1], sys.argv[2]
payload = {
    "model": model,
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Reply with READY in one short sentence."},
    ],
    "max_tokens": 64,
}
with open(path, "w", encoding="utf-8") as handle:
    json.dump(payload, handle)
PY

status="$(
  curl -sS \
    -o "$response" \
    -w "%{http_code}" \
    -H "Authorization: Bearer ${KEY}" \
    -H "Content-Type: application/json" \
    --data-binary "@${payload}" \
    "$ENDPOINT"
)"

if [[ "$status" != 2* ]]; then
  echo "Endpoint probe failed with HTTP $status." >&2
  python3 - "$response" <<'PY' >&2
import json
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
try:
    data = json.loads(text)
    msg = data.get("error", {}).get("message") or data.get("message") or text
except Exception:
    msg = text
print(str(msg)[:800])
PY
  exit 1
fi

python3 - "$response" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
content = (
    data.get("choices", [{}])[0]
    .get("message", {})
    .get("content", "")
    .strip()
)
print("Endpoint probe succeeded.")
print(f"Model response: {content[:200]}")
PY
