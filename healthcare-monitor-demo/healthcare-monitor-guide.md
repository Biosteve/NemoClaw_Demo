# Healthcare Monitor Agentic Claw

OpenClaw-native multi-agent healthcare operations example for NemoClaw and OpenShell.

This repository follows the shape used by the public `brevdev/nemoclaw-demos` examples:

- root `openclaw.json`
- root `TOOLS.md`
- root `policy.yaml`
- repeatable setup and verification scripts
- `SKILL.md` directories with YAML frontmatter
- a local web app for exercising the runtime
- self-contained synthetic data and deterministic local tools

The project is designed to be rebuilt from source into a fresh NemoClaw sandbox. The OpenClaw configuration, agents, skills, data, scripts, and cron job are baked into the custom sandbox image before runtime lock-down.

## What This Example Shows

- A `main` OpenClaw coordinator delegates to specialist OpenClaw subagents with `sessions_spawn`.
- Specialist agents have separate workspaces, prompts, skills, and restricted tool permissions.
- Leaf agents can read and execute local tools, but cannot spawn additional agents or write files.
- A deterministic Python CLI provides the evidence for intake, triage, capacity planning, payer audit, reports, and blocked-egress tests.
- OpenShell policy blocks an intentional outbound lookup that is not explicitly allowed.
- A local web app exposes runtime checks, topology inspection, local tool output, multi-agent execution, policy behavior, and recurring watch configuration.

All healthcare records in this repository are synthetic. The agents provide operational decision-support for an example workflow only. They do not provide medical advice, diagnoses, or real payer determinations.

## Architecture

```text
Linux or Brev host
  ├── NemoClaw CLI
  ├── OpenShell gateway
  └── Sandbox "healthcare-monitor"
       ├── /sandbox/.openclaw/openclaw.json
       ├── /sandbox/.openclaw/skills/
       ├── /sandbox/.openclaw/workspace-main/
       ├── /sandbox/.openclaw/workspace-intake/
       ├── /sandbox/.openclaw/workspace-clinical-triage/
       ├── /sandbox/.openclaw/workspace-capacity-planner/
       ├── /sandbox/.openclaw/workspace-payer-audit/
       ├── /sandbox/.openclaw/workspace-command-writer/
       ├── /sandbox/.openclaw/workspace/data/
       ├── /sandbox/.openclaw/workspace/scripts/
       └── /sandbox/.openclaw/cron/jobs.json
```

OpenClaw subagent flow:

```text
main
  ├── agents_list
  ├── sessions_spawn(agentId="intake")
  │    └── python3 .../care_backlog_analyzer.py intake
  ├── sessions_spawn(agentId="clinical-triage")
  │    └── python3 .../care_backlog_analyzer.py triage
  ├── sessions_spawn(agentId="capacity-planner")
  │    └── python3 .../care_backlog_analyzer.py schedule
  ├── sessions_spawn(agentId="payer-audit")
  │    └── python3 .../care_backlog_analyzer.py audit
  └── exec python3 .../care_backlog_analyzer.py report
```

## Folder Layout

| Path | Purpose |
|---|---|
| `Dockerfile.sandbox` | Custom NemoClaw sandbox image build. |
| `openclaw.json` | OpenClaw agent, tool, skill, model, plugin, and subagent config. |
| `TOOLS.md` | Workspace-level operating notes for OpenClaw agents. |
| `policy.yaml` | Custom OpenShell egress policy preset for the local web app. |
| `workspaces/` | Per-agent `AGENTS.md`, `TOOLS.md`, persona, user, identity, and memory files. |
| `skills/` | Shared OpenClaw skills with YAML frontmatter. |
| `data/` | Synthetic referrals, notes, capacity, payer rules, and escalation rules. |
| `workspace/scripts/` | Deterministic Python CLI copied into the sandbox image. |
| `openclaw-cron/` | Scheduled Healthcare Monitor Watch job. |
| `demo-app/` | Local web application for testing and inspection. |
| `docs/` | Architecture, Brev setup, reset, and troubleshooting guides. |
| `scripts/` | Setup, verification, policy, app, and packaging helpers. |

## Requirements

- Linux host or Brev instance.
- Docker available to the user running NemoClaw.
- Network access to install NemoClaw/OpenShell if they are not already installed.
- An API key that can call `https://inference-api.nvidia.com/v1/chat/completions`.
- Access to the model `nvidia/nvidia/nemotron-3-super-v3`, or a compatible model you intentionally substitute.

## Environment

Create `.env` from the example:

```bash
cd ~/healthcare-monitor-agentic-claw
cp -n .env.example .env
chmod 600 .env
vi .env
```

Recommended values for the included configuration:

```bash
NEMOCLAW_PROVIDER=custom
NEMOCLAW_ENDPOINT_URL=https://inference-api.nvidia.com/v1/chat/completions
NEMOCLAW_MODEL=nvidia/nvidia/nemotron-3-super-v3
NEMOCLAW_PROVIDER_KEY=your-api-key
NEMOCLAW_SANDBOX=healthcare-monitor
NEMOCLAW_POLICY_TIER=restricted
NEMOCLAW_POLICY_MODE=suggested
NEMOCLAW_INSTALL_IF_MISSING=1
NEMOCLAW_ACCEPT_THIRD_PARTY_SOFTWARE=1
NEMOCLAW_DESTROY_EXISTING=0
NEMOCLAW_APPLY_LOCAL_POLICY=1
HOST=0.0.0.0
PORT=5188
```

Keep `.env` private. It is ignored by git and should not be copied into the sandbox image.

## Build And Run

Run each command from the repository root.

### 1. Verify Local Files

```bash
./scripts/run-local-verification.sh
```

This validates:

- Python analyzer commands: `intake`, `triage`, `schedule`, `audit`, `report`, `watch-summary`, `agent-topology`
- cron JSON
- `openclaw.json` structure
- specialist workspaces
- skill frontmatter
- shell script syntax
- Python syntax

### 2. Probe The Custom Endpoint

```bash
./scripts/probe-custom-endpoint.sh
```

The probe sends a minimal Chat Completions request to `NEMOCLAW_ENDPOINT_URL`. It should return `READY`.

### 3. Build The Sandbox

```bash
./scripts/brev-runtime-setup.sh
```

The setup script:

- installs NemoClaw/OpenShell if enabled and missing
- applies the local onboarding compatibility patch when needed
- runs local verification
- builds `Dockerfile.sandbox`
- runs `nemoclaw onboard --from Dockerfile.sandbox`
- applies `policy.yaml`

The onboarding output should show:

```text
Provider: custom
Chat Completions API available
Using Other OpenAI-compatible endpoint
Sandbox 'healthcare-monitor' created
```

### 4. Run Readiness Checks

```bash
./scripts/live-demo-ready.sh
```

This re-runs verification, checks the sandbox status, probes the OpenClaw gateway, applies the local policy preset, and starts the web app if needed.

### 5. Open The Web App

On the host:

```text
http://127.0.0.1:5188
```

For Brev or another remote browser environment, expose or forward port `5188`. The app is normally started with:

```bash
HOST=0.0.0.0 PORT=5188 ./scripts/start-demo-app.sh
```

## CLI Smoke Tests

Load `.env` first:

```bash
set -a
source .env
set +a
```

Show the effective sandbox status:

```bash
nemoclaw "$NEMOCLAW_SANDBOX" status
```

List OpenClaw agents:

```bash
openshell sandbox exec --name "$NEMOCLAW_SANDBOX" -- openclaw agents
```

Inspect topology from the Python CLI:

```bash
openshell sandbox exec --name "$NEMOCLAW_SANDBOX" -- \
  python3 /sandbox/.openclaw/workspace/scripts/care_backlog_analyzer.py agent-topology
```

Run each deterministic tool:

```bash
openshell sandbox exec --name "$NEMOCLAW_SANDBOX" -- \
  python3 /sandbox/.openclaw/workspace/scripts/care_backlog_analyzer.py intake

openshell sandbox exec --name "$NEMOCLAW_SANDBOX" -- \
  python3 /sandbox/.openclaw/workspace/scripts/care_backlog_analyzer.py triage

openshell sandbox exec --name "$NEMOCLAW_SANDBOX" -- \
  python3 /sandbox/.openclaw/workspace/scripts/care_backlog_analyzer.py schedule

openshell sandbox exec --name "$NEMOCLAW_SANDBOX" -- \
  python3 /sandbox/.openclaw/workspace/scripts/care_backlog_analyzer.py audit

openshell sandbox exec --name "$NEMOCLAW_SANDBOX" -- \
  python3 /sandbox/.openclaw/workspace/scripts/care_backlog_analyzer.py report
```

Run a specialist directly:

```bash
openshell sandbox exec --name "$NEMOCLAW_SANDBOX" -- \
  openclaw agent --agent capacity-planner --json \
    -m "Run the capacity workflow. Use the healthcare-capacity-planning skill and execute the schedule analyzer. Return a concise summary only." \
    --session-id healthcare-monitor-capacity-check
```

Run the coordinator:

```bash
openshell sandbox exec --name "$NEMOCLAW_SANDBOX" -- \
  openclaw agent --agent main --json \
    -m "Use agents_list, then sessions_spawn with explicit agentId for intake, clinical-triage, capacity-planner, and payer-audit. Then run the report analyzer and return the 48-hour healthcare monitor plan." \
    --session-id healthcare-monitor-main-check
```

Run the blocked-egress check:

```bash
openshell sandbox exec --name "$NEMOCLAW_SANDBOX" -- \
  python3 /sandbox/.openclaw/workspace/scripts/care_backlog_analyzer.py blocked-lookup
```

Expected output:

```text
EGRESS_BLOCKED
reason=<urlopen error Tunnel connection failed: 403 Forbidden>
```

## Web App Checks

Verify the app:

```bash
curl -fsS "http://127.0.0.1:${PORT:-5188}/api/config"
curl -fsS "http://127.0.0.1:${PORT:-5188}/api/dashboard"
curl -fsS "http://127.0.0.1:${PORT:-5188}/api/topology"
```

Run the key app actions:

```bash
curl -fsS -X POST "http://127.0.0.1:${PORT:-5188}/api/run/agent-plan"
curl -fsS -X POST "http://127.0.0.1:${PORT:-5188}/api/run/blocked-lookup"
```

The app binds to `HOST` and `PORT`. If the page is unavailable from a remote browser, confirm the process is listening on `0.0.0.0:5188`:

```bash
ss -ltnp | grep 5188
```

## Important Learnings And Workarounds

### Sandbox Config Is Image-Baked

OpenClaw config inside the sandbox is effectively runtime-locked. Do not depend on modifying `/sandbox/.openclaw/openclaw.json` from inside the sandbox. Put config changes in the repo and rebuild with `Dockerfile.sandbox`.

### Use Chat Completions For This Endpoint

The custom endpoint used by this example is OpenAI-compatible Chat Completions:

```text
https://inference-api.nvidia.com/v1/chat/completions
```

The setup script configures OpenClaw for `openai-completions`. If a Responses API probe fails or reports missing streaming events, falling back to Chat Completions is expected.

### Shared Gateway Inference Is Not Per-Sandbox Isolation

Multiple sandboxes can share the same OpenShell gateway. In that case, `openshell inference get` shows the gateway-level provider/model. The OpenClaw config in each sandbox still records model IDs, but the `inference.local` route is gateway-managed. Use separate gateways if you need hard endpoint isolation between sandboxes.

### Disable Unused Plugins

`openclaw.json` disables unused bundled plugins. This avoids runtime plugin staging that can require network/package access under restricted OpenShell policy.

### Keep Subagent Config Conservative

This OpenClaw version accepts subagent allowlists on individual agents, while concurrency/depth limits are safer under defaults. Avoid unsupported keys such as `systemPromptOverride`, `sandbox.backend`, `contextLimits`, or per-agent subagent keys not accepted by the installed OpenClaw version.

### `sessions_yield` Can Be Awkward In CLI Runs

For web-app reliability, the `agent-plan` action uses OpenClaw subagent spawning as an audit trail, then displays the deterministic sandbox report as the final evidence source. This avoids a model-generated summary accidentally drifting from payer/audit facts while still exercising `agents_list`, `sessions_spawn`, and `exec`.

### Blocked Egress Should Exit Cleanly

The blocked lookup command catches the expected OpenShell denial and exits with `0` while printing `EGRESS_BLOCKED`. This makes the web action show a successful policy block instead of looking like an application crash.

### Remote Web Access Needs `0.0.0.0`

For local-only use, `127.0.0.1` is fine. For Brev or an IDE port-forwarded browser, start the web app with:

```bash
HOST=0.0.0.0 PORT=5188 ./scripts/start-demo-app.sh
```

## Reset

To rebuild the sandbox from scratch:

```bash
NEMOCLAW_FORCE_DESTROY_EXISTING=1 ./scripts/brev-runtime-setup.sh
```

This destroys and recreates only `NEMOCLAW_SANDBOX`.

To restart only the web app:

```bash
fuser -k 5188/tcp || true
HOST=0.0.0.0 PORT=5188 ./scripts/start-demo-app.sh
```

## Package

```bash
./scripts/package-demo.sh
```

The archive excludes local state, caches, and `.env`.

## Notes

NemoClaw and OpenClaw are evolving quickly. Treat this repository as a repeatable example architecture and validation harness, not a production medical workflow.
