# PolicyLedger Backend

FastAPI backend for PolicyLedger's tamper-evident RL policy verification system.

## Features

- Tabular Q-Learning (with optional Double Q-Learning experimental variant)
- Live policy generation via WebSocket
- Multi-agent concurrent training support
- Deterministic policy verification
- Tamper-evident ledger management
- Cyber defense environment simulation

## Running

```bash
uv run fastapi dev main.py --host 0.0.0.0 --port 8000
```
