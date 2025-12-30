# PolicyLedger

**Decentralized RL Policy Governance Platform with Tamper-Evident Verification**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

---

## 🎯 Overview

PolicyLedger is a **decentralized governance platform** for reinforcement learning (RL) policies. It solves the fundamental trust problem in distributed RL systems: **How do you verify policy performance claims from untrusted agents without retraining?**

### The Problem

In decentralized RL systems:
- ❌ Agents can falsely claim high rewards
- ❌ No mechanism exists to verify performance claims
- ❌ Learned policies cannot be shared safely
- ❌ No marketplace for RL policy selection exists

### The Solution

PolicyLedger introduces a **verification-first architecture**:

1. **Agents train** at the edge (untrusted environments)
2. **Verifier replays** policies deterministically (trust through replay)
3. **Ledger records** verified results immutably (tamper-evident storage)
4. **Marketplace ranks** policies objectively (argmax verified_reward)
5. **Consumers reuse** winning policies (zero retraining)

**Key Innovation**: Verification through deterministic replay, not through trusting agent reports.

---

## ✨ Features

### Core Capabilities

- 🔐 **Tamper-Evident Ledger**: Hash-chained immutable storage for verified policies
- ✅ **Deterministic Verification**: Replay policies to confirm performance claims
- 📊 **Real-Time Training Visualization**: WebSocket-based live training dashboard
- 🏆 **Policy Marketplace**: Objective ranking based on verified rewards
- 🔄 **Policy Reuse**: Deploy verified policies without retraining
- 🧠 **AI-Powered Explanations**: Gemini API integration for policy insights
- 📈 **Advanced Training Algorithms**: Double Q-Learning with experience replay

### Technology Stack

**Backend:**
- FastAPI (REST + WebSocket APIs)
- NumPy (RL computations)
- Gymnasium (RL environment interface)
- Python 3.10+

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- shadcn/ui (component library)
- TanStack Query (data fetching)
- Recharts (visualization)

**Optional Cloud Integration:**
- Google Cloud Firestore (distributed ledger)
- Vertex AI (scalable verification)
- Gemini API (AI explanations)
- Cloud Functions (event-driven workflows)

---

## 🏗️ Architecture

![Architecture Documentation](Architecture.md)

PolicyLedger consists of 6 core components:

### 1. **Environment** (`src/environments/`)
- Deterministic simulated cyber defense environment
- State: 5-tuple (attack severity, type, system health, confidence, duration)
- Actions: 5 defensive responses (ignore, monitor, rate-limit, block, isolate)
- Seeded RNG ensures reproducible trajectories

### 2. **Training Agent** (`src/agent/`)
- Tabular Q-Learning with epsilon-greedy exploration
- Double Q-Learning variant for reduced overestimation
- Experience replay buffer for improved sample efficiency
- Produces serializable Q-table policies

### 3. **Policy Verifier** (`src/verifier/`)
- Deterministic policy replay engine
- Recomputes rewards independently
- Binary decision: VALID/INVALID
- No trust in agent claims

### 4. **Tamper-Evident Ledger** (`src/ledger/`)
- Append-only hash-chained storage
- Each entry cryptographically linked to previous
- Immutable verified policy records
- Integrity verification via chain validation

### 5. **Policy Marketplace** (`src/marketplace/`)
- Objective policy ranking (argmax verified_reward)
- Timestamp-based tie-breaking
- Read-only operations on ledger
- Deterministic selection

### 6. **Policy Consumer** (`src/consumer/`)
- Zero-retraining policy execution
- Greedy action selection (no exploration)
- Identical execution loop to training/verification
- Safe deployment of verified policies

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Node.js 18+ and npm
- Git

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
python start_server.py
```

Backend runs on: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend/policy-ledger-insights

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on: `http://localhost:5173`

### Using PowerShell Scripts (Windows)

```powershell
# Start backend
.\start-backend.ps1

# Start frontend
cd frontend\policy-ledger-insights
.\start.ps1
```

---

## 📖 Usage Examples

### 1. Live Training Dashboard

Access the web UI at `http://localhost:5173` and:

1. Navigate to **"Live Training"** page
2. Configure training parameters (episodes, seed, environment)
3. Click **"Start Training"**
4. Watch real-time metrics:
   - Episode rewards
   - Q-table growth
   - Action distribution
   - Epsilon decay

### 2. Command Line Demo

```bash
cd backend
python demo.py
```

This runs the complete workflow:
- Trains 6 agents with different configurations
- Verifies all policy claims
- Records verified policies in ledger
- Ranks policies by performance
- Reuses the best policy

### 3. API Integration

```python
import requests

# Submit a training claim
response = requests.post("http://localhost:8000/train", json={
    "agent_id": "agent_001",
    "seed": 42,
    "episodes": 1000
})

# Verify a policy
response = requests.post("http://localhost:8000/verify", json={
    "agent_id": "agent_001"
})

# Get best policy
response = requests.get("http://localhost:8000/marketplace/best")
best_policy = response.json()
```

### 4. Policy Testing

```bash
cd backend
python test_policy.py
```

Tests a specific policy with different environment configurations.

---

## 📊 System Workflow

```
┌─────────────┐
│   AGENT     │  Trains policy (untrusted)
│  (Edge)     │  Claims reward: 850
└──────┬──────┘
       │ Submit (policy + claim)
       ▼
┌─────────────┐
│  VERIFIER   │  Replays policy deterministically
│ (Trusted)   │  Recomputes reward: 850 ✓
└──────┬──────┘
       │ Verified result
       ▼
┌─────────────┐
│   LEDGER    │  Records: hash(policy, 850, timestamp)
│ (Immutable) │  Chain: prev_hash → current_hash
└──────┬──────┘
       │ Query verified policies
       ▼
┌─────────────┐
│ MARKETPLACE │  Ranks by verified_reward
│  (Ranking)  │  Returns best: policy_hash_xyz
└──────┬──────┘
       │ Fetch best policy
       ▼
┌─────────────┐
│  CONSUMER   │  Executes policy (no training)
│   (Reuse)   │  Observes real reward
└─────────────┘
```

---

## 🔬 Key Concepts

### Deterministic Replay

**Why it matters**: Verification requires reproducibility. Same seed + same actions = same trajectory.

**How it works**:
1. Environment uses seeded RNG
2. Agent stores policy as Q-table
3. Verifier replays greedy actions
4. Rewards must match exactly (within threshold)

### Hash Chaining

**Why it matters**: Prevents retroactive tampering with ledger entries.

**How it works**:
```
Entry_N.current_hash = SHA256(
    Entry_N.policy_hash +
    Entry_N.verified_reward +
    Entry_N.timestamp +
    Entry_N-1.current_hash
)
```

Any modification breaks the chain.

### Greedy vs Epsilon-Greedy

- **Training**: Epsilon-greedy (explores + exploits)
- **Verification**: Greedy only (deterministic replay)
- **Reuse**: Greedy only (safe deployment)

**Critical**: Verification and reuse NEVER explore.

---

## 🧪 Testing

```bash
# Run backend tests
cd backend
pytest tests/

# Test specific policy
python test_policy.py

# Verify ledger integrity
python -c "from src.ledger.ledger import verify_chain_integrity, PolicyLedger; verify_chain_integrity(PolicyLedger('ledger.json'))"
```

---

## 📁 Project Structure

```
PolicyLedger/
├── backend/
│   ├── src/
│   │   ├── agent/          # RL training & policy management
│   │   ├── verifier/       # Deterministic verification
│   │   ├── ledger/         # Tamper-evident storage
│   │   ├── marketplace/    # Policy ranking
│   │   ├── consumer/       # Policy reuse
│   │   ├── environments/   # Cyber defense simulation
│   │   ├── training/       # Live training system
│   │   ├── execution/      # Live execution features
│   │   └── explainability/ # AI-powered insights
│   ├── main.py             # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── pyproject.toml      # Project configuration
├── frontend/
│   └── policy-ledger-insights/
│       ├── src/
│       │   ├── components/ # React components
│       │   ├── pages/      # Route pages
│       │   └── lib/        # Utilities
│       ├── package.json    # Node dependencies
│       └── vite.config.ts  # Build configuration
├── Architecture.md         # Detailed architecture docs
├── Quickstart.md          # Setup guide
└── checklist.md           # Google Cloud deployment checklist
```

---

## 🌩️ Google Cloud Integration (Optional)

PolicyLedger is designed for Google Cloud Platform deployment:

- **Firestore**: Distributed ledger with automatic replication
- **Vertex AI**: Scalable policy verification workloads
- **Cloud Functions**: Event-driven marketplace updates
- **Gemini API**: AI-powered policy explanations
- **Cloud Run**: Serverless API deployment
- **Cloud Build**: CI/CD automation

See [checklist.md](checklist.md) for deployment guide.

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Additional RL environments
- Advanced verification techniques
- Distributed verifier network
- Byzantine fault tolerance
- Privacy-preserving verification
- Multi-agent collaboration

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🔗 Resources

- **Architecture Details**: See [Architecture.md](Architecture.md)
- **Quick Setup**: See [Quickstart.md](Quickstart.md)
- **Google Cloud Deployment**: See [checklist.md](checklist.md)
- **API Documentation**: http://localhost:8000/docs (when running)

---

## 🎓 Research Context

PolicyLedger demonstrates key concepts in:
- Decentralized reinforcement learning
- Blockchain-inspired tamper evidence
- Deterministic verification systems
- RL policy marketplaces
- Trustless distributed systems

**Not a production security system** - this is a research prototype for demonstrating verification concepts in distributed RL.

---

**Built with ❤️ for HackNEXA**
