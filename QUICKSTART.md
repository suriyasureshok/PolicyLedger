# 🚀 PolicyLedger Quick Start Guide

## Overview
PolicyLedger is a decentralized RL policy marketplace with:
- **Backend**: FastAPI REST API (Python)
- **Frontend**: React + Vite dashboard
- **Core**: Policy training, verification, ledger, and marketplace

---

## 🎯 Quick Start

### Option 1: Start Everything (Recommended)
```powershell
.\start.ps1
```
This will:
- Start backend on `http://localhost:8000`
- Start frontend on `http://localhost:5173`
- Open in separate windows

### Option 2: Backend Only
```powershell
.\start-backend.ps1
```
Or manually:
```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

### Option 3: Run Demo Script
```powershell
.\.venv\Scripts\Activate.ps1
python demo.py
```
Demonstrates the complete workflow with 6 agents.

---

## 📡 API Endpoints

### Training & Verification
- `POST /agent/train` - Train a new agent
- `POST /agent/verify/{agent_id}` - Verify policy claim
- `POST /ledger/add/{agent_id}` - Add verified policy to ledger

### Marketplace
- `GET /marketplace` - Get ranked policies
- `GET /marketplace/best` - Get best policy

### Consumer
- `POST /consumer/reuse` - Reuse best policy (zero-training)

### System
- `GET /ledger` - View all ledger entries
- `GET /ledger/integrity` - Check hash chain integrity
- `GET /stats` - System statistics
- `GET /health` - Health check
- `DELETE /reset` - Reset system (demo only)

### API Documentation
Interactive docs available at: `http://localhost:8000/docs`

---

## 🎨 Frontend Integration

Frontend is located in: `frontend/policy-ledger-insights/`

### Setup Frontend
```bash
cd frontend/policy-ledger-insights
npm install
npm run dev
```

### Environment Configuration
Create `frontend/policy-ledger-insights/.env`:
```
VITE_API_URL=http://localhost:8000
```

---

## 📊 Example Workflow

### Using API (cURL)
```bash
# 1. Train agent
curl -X POST http://localhost:8000/agent/train \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent_001", "seed": 42, "episodes": 150}'

# 2. Verify agent
curl -X POST http://localhost:8000/agent/verify/agent_001

# 3. Add to ledger
curl -X POST http://localhost:8000/ledger/add/agent_001

# 4. Get marketplace rankings
curl http://localhost:8000/marketplace

# 5. Reuse best policy
curl -X POST http://localhost:8000/consumer/reuse
```

### Using Python
```python
import requests

BASE_URL = "http://localhost:8000"

# Train agent
response = requests.post(f"{BASE_URL}/agent/train", json={
    "agent_id": "agent_001",
    "seed": 42,
    "episodes": 150
})
print(response.json())

# Verify
response = requests.post(f"{BASE_URL}/agent/verify/agent_001")
print(response.json())

# Add to ledger
response = requests.post(f"{BASE_URL}/ledger/add/agent_001")
print(response.json())

# Get best policy
response = requests.get(f"{BASE_URL}/marketplace/best")
print(response.json())

# Reuse policy
response = requests.post(f"{BASE_URL}/consumer/reuse")
print(response.json())
```

---

## 🗂️ Project Structure

```
PolicyLedger/
├── main.py                     # FastAPI backend
├── demo.py                     # Complete demo script
├── start.ps1                   # Start both frontend & backend
├── start-backend.ps1           # Start backend only
├── ledger.json                 # Blockchain ledger
├── policies/                   # Stored policy artifacts
├── src/                        # Core modules
│   ├── agent/                  # RL agent training
│   ├── verifier/               # Policy verification
│   ├── ledger/                 # Tamper-evident ledger
│   ├── marketplace/            # Policy ranking
│   ├── consumer/               # Policy reuse
│   └── shared/                 # Shared utilities
├── frontend/
│   └── policy-ledger-insights/ # React dashboard
└── docs/                       # Documentation
```

---

## 🔒 Key Features

### 1. Decentralized Learning
- Agents train independently
- No coordination required
- Different seeds produce different policies

### 2. Deterministic Verification
- Verifier replays policy
- Confirms claimed rewards
- Rejects fraudulent claims

### 3. Tamper-Evident Ledger
- Hash-chained entries
- Immutable record
- Integrity verification

### 4. Policy Marketplace
- Ranks by verified reward
- Tie-breaking by timestamp
- Best policy selection

### 5. Zero-Training Reuse
- Consumer loads best policy
- Instant deployment
- No training required

---

## 🛠️ Development

### Install Dependencies
```powershell
# Backend
pip install fastapi uvicorn pydantic

# Frontend
cd frontend/policy-ledger-insights
npm install
```

### Run Tests
```powershell
pytest tests/
```

### Reset System
```bash
curl -X DELETE http://localhost:8000/reset
```

---

## 📝 Notes

- **Ledger File**: `ledger.json` stores all verified policies
- **Policy Storage**: `policies/` directory contains policy artifacts
- **Demo Mode**: Use 150 episodes for fast demonstrations
- **Production Mode**: Use 500+ episodes for better convergence

---

## 🎯 Demo Presentation Tips

1. **Start with demo.py**: Shows complete workflow
2. **Show API docs**: Interactive Swagger UI at `/docs`
3. **Frontend dashboard**: Visual representation of marketplace
4. **Highlight**: Zero-training policy reuse (THE WOW MOMENT)
5. **Explain**: Tamper-evident ledger (hash chain integrity)

---

## 📚 Additional Resources

- [Architecture Documentation](docs/PHASE_4_ARCHITECTURE.md)
- [API Documentation](http://localhost:8000/docs)
- [Phase Completion Summaries](docs/)

---

## 🤝 Support

For issues or questions, check the documentation in the `docs/` directory.

**Good luck with your demo! 🚀**
