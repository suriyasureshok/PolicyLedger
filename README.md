# PolicyLedger

**Decentralized Governance Platform for Reinforcement Learning Policies**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

---

## 🎯 Overview

PolicyLedger is a decentralized governance platform for reinforcement learning (RL) policies. It solves the fundamental trust problem in distributed RL systems: **How do you verify policy performance claims from untrusted agents without retraining?**

### The Problem

In decentralized RL systems:
- ❌ Agents can falsely claim high rewards
- ❌ No mechanism exists to verify performance claims without trust
- ❌ Learned policies cannot be shared safely between systems
- ❌ No transparent marketplace for RL policy selection exists

### The Solution

PolicyLedger introduces a **verification-first architecture**:

1. **Agents train** policies at the edge (untrusted environments)
2. **Verifier replays** policies deterministically (trust through replay)
3. **Ledger records** verified results immutably (tamper-evident storage)
4. **Marketplace ranks** policies objectively (based on verified performance)
5. **Consumers reuse** winning policies (zero retraining required)

**Key Innovation**: Verification through deterministic replay, not through trusting agent reports.

---

## ✨ Features

### Core Capabilities

- 🔐 **Tamper-Evident Ledger**: Hash-chained immutable storage for verified policies
- ✅ **Deterministic Verification**: Replay policies to confirm performance claims
- 📊 **Live Training Visualization**: Real-time WebSocket-based dashboard
- 🏆 **Policy Marketplace**: Objective ranking based on verified rewards
- 🔄 **Policy Reuse**: Deploy verified policies without retraining
- 🧠 **AI-Powered Insights**: Gemini API integration for policy explanations
- 📈 **RL Algorithms**: Tabular Q-Learning implementation
- ☁️ **Cloud-Native**: Built on Google Cloud Platform

### Technology Stack

**Backend:**
- FastAPI (REST + WebSocket APIs)
- Python 3.10+
- NumPy (RL computations)
- Gymnasium (RL environment interface)

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- shadcn/ui (component library)
- TanStack Query (state management)
- Recharts (visualization)
- **Dark Dashboard Theme**: Deep navy-purple with purple/pink/cyan accents
- Tailwind CSS with HSL color system
- **Dark Dashboard Theme**: Deep navy-purple (#0f0c1a) with purple/magenta/cyan accents
- Tailwind CSS with HSL color system for dynamic theming

**Google Cloud Platform (Required):**
- **Firestore**: Distributed ledger storage with automatic replication
- **Vertex AI**: Scalable policy verification workloads
- **Gemini API**: AI-powered policy explanations and insights
- **Cloud Run**: Serverless API deployment and auto-scaling
- **Secret Manager**: Secure API key storage

---

## 🏗️ Architecture

PolicyLedger consists of 6 core components:

### 1. **Environment** (`src/environments/`)
- Deterministic simulated cyber defense environment
- State: 5-tuple (attack severity, type, system health, confidence, duration)
- Actions: 5 defensive responses (ignore, monitor, rate-limit, block, isolate)
- Seeded RNG ensures reproducible trajectories

### 2. **Training Agent** (`src/agent/`)
- Tabular Q-Learning with epsilon-greedy exploration
- Produces serializable Q-table policies
- Configurable hyperparameters

### 3. **Policy Verifier** (`src/verifier/`)
- Deterministic policy replay engine
- Recomputes rewards independently
- Binary decision: VALID/INVALID
- No trust in agent claims required

### 4. **Tamper-Evident Ledger** (`src/ledger/`)
- Append-only hash-chained storage
- Each entry cryptographically linked to previous
- Immutable verified policy records
- Integrity verification via chain validation

### 5. **Policy Marketplace** (`src/marketplace/`)
- Objective policy ranking (by verified_reward)
- Timestamp-based tie-breaking
- Read-only operations on ledger
- Deterministic selection

### 6. **Policy Consumer** (`src/consumer/`)
- Zero-retraining policy execution
- Greedy action selection (no exploration)
- Safe deployment of verified policies

For detailed architecture documentation, see [Architecture.md](Architecture.md)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Node.js 18+ and npm
- Git
- **Google Cloud account with billing enabled** (required)
- gcloud CLI installed ([Download](https://cloud.google.com/sdk/docs/install))

### Installation

#### 1. Clone Repository

```bash
git clone https://github.com/your-org/PolicyLedger.git
cd PolicyLedger
```

#### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

#### 3. Google Cloud Setup (Required)

```bash
# Navigate to project root
cd PolicyLedger

# Run GCP setup script
.\setup-gcp.ps1  # Windows
# or
./setup-gcp.sh   # Linux/Mac
```

This will:
- Enable required Google Cloud APIs
- Initialize Firestore database
- Set up Artifact Registry
- Configure service accounts and permissions
- Store Gemini API key in Secret Manager
- Create environment configuration

**Important**: You must have:
- Google Cloud project with **billing enabled**
- Gemini API key from [makersuite.google.com](https://makersuite.google.com/app/apikey)

#### 4. Frontend Setup

```bash
cd frontend/policy-ledger-insights
npm install
```

### Running the Application

#### Start Backend

```bash
cd backend
python start_server.py
```

Backend runs on: `http://localhost:8000`  
API docs: `http://localhost:8000/docs`

#### Start Frontend

```bash
cd frontend/policy-ledger-insights
npm run dev
```

Frontend runs on: `http://localhost:5173`

#### Using PowerShell Scripts (Windows)

```powershell
# Start backend
.\start-backend.ps1

# Start frontend
cd frontend\policy-ledger-insights
npm run dev
```

---

## 📖 Usage Guide

### 1. Live Training Dashboard

1. Navigate to `http://localhost:5173`
2. Go to **"Live Training"** page
3. Configure generation parameters:
   - Number of episodes
   - Training seed
   - Environment settings
4. Click **"Start Training"**
5. Observe real-time metrics:
   - Episode rewards
   - Q-table growth
   - Action distribution
   - Epsilon decay

### 2. Command Line Demo

Run the complete workflow demonstration:

```bash
cd backend
python demo.py
```

This demonstrates:
- Training 6 agents with different configurations
- Verifying all policy claims
- Recording verified policies in ledger
- Ranking policies by performance
- Reusing the best policy

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

---

## 📊 System Workflow

```
┌─────────────┐
│   AGENT     │  Trains policy (untrusted)
│  (Edge)     │  Claims reward: 850
└──────┬──────┘
       │ Submit policy + claim
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
│   (Reuse)   │  Deploys in production
└─────────────┘
```

---

## 🎨 Dashboard UI

### Modern Dark Control Room Theme

The PolicyLedger dashboard features a sophisticated dark aesthetic inspired by control room interfaces:

**Color Palette:**
- **Background**: Almost black (#0f0c1a) with subtle purple tint
- **Primary**: Purple/violet (#8b70ff) - Primary buttons and highlights  
- **Secondary**: Hot pink/magenta (#ff2d75) - Important metrics
- **Accent**: Bright cyan (#00d4ff) - Interactive elements
- **Success**: Teal/green (#2dd4bf) - Positive indicators

**Dashboard Features:**
- 📊 **Live Training** - Real-time WebSocket streaming with animated metrics
- 🔐 **Ledger Browser** - Immutable blockchain-style visualization
- 🏆 **Marketplace** - Verified policy leaderboard with rankings
- 🔄 **Policy Reuse** - Zero-training deployment interface
- 🧠 **Explainability** - AI-powered behavioral insights via Gemini
- 📈 **Analytics** - Interactive charts and data visualization
- ⚡ **Live Execution** - Step-by-step policy execution monitor

**Design Elements:**
- Glassmorphism cards with backdrop blur
- Neon glow effects on key metrics
- Grid patterns for technical aesthetic  
- Smooth animations and transitions
- Gradient text effects

---

## 🧪 Testing

```bash
# Run backend tests
cd backend
pytest tests/

# Test specific policy
python test_policy.py

# Verify ledger integrity
python -c "from src.ledger.ledger import verify_chain_integrity, PolicyLedger; \
           print(verify_chain_integrity(PolicyLedger('ledger.json')))"
```

---

## 📁 Project Structure

```
PolicyLedger/
├── backend/
│   ├── src/
│   │   ├── agent/          # RL policy generation
│   │   ├── verifier/       # Deterministic verification
│   │   ├── ledger/         # Tamper-evident storage
│   │   ├── marketplace/    # Policy ranking
│   │   ├── consumer/       # Policy reuse
│   │   ├── environments/   # Simulation environment
│   │   ├── training/       # Live training system
│   │   └── explainability/ # AI insights (optional)
│   ├── main.py             # FastAPI application
│   ├── demo.py             # Complete workflow demo
│   ├── requirements.txt    # Dependencies
│   └── pyproject.toml      # Project config
├── frontend/
│   └── policy-ledger-insights/
│       ├── src/
│       │   ├── components/ # React components
│       │   ├── pages/      # Route pages
│       │   └── lib/        # Utilities
│       ├── package.json    # Dependencies
│       └── vite.config.ts  # Build config
├── Architecture.md         # Detailed architecture
├── README.md              # This file
└── LICENSE                # MIT License
```

---

## ☁️ Google Cloud Platform Architecture

PolicyLedger is built on Google Cloud Platform for scalability, reliability, and AI capabilities:

### Core GCP Services

#### 1. **Firestore** (Ledger Storage)
- Distributed, serverless NoSQL database
- Automatic replication across regions
- Real-time synchronization
- Stores hash-chained ledger entries
- Scales automatically with demand

#### 2. **Vertex AI** (Policy Verification)
- Scalable policy verification workloads
- Custom training jobs for parallel verification
- Managed compute resources
- Automatic scaling based on verification queue

#### 3. **Gemini API** (AI Insights)
- Policy explanation generation
- Natural language insights
- Performance analysis
- Recommendation engine

#### 4. **Cloud Run** (API Deployment)
- Serverless container deployment
- Auto-scaling from 0 to N instances
- Pay-per-use pricing
- WebSocket support for live training
- HTTPS endpoints with automatic certificates

#### 5. **Secret Manager** (Security)
- Encrypted storage for API keys
- Version control for secrets
- Fine-grained access control
- Audit logging

### Deployment Architecture

```
┌──────────────────────────────────────────────────────┐
│              Frontend (Cloud Storage/Hosting)        │
│                   React SPA                          │
└───────────────────────┬──────────────────────────────┘
                        │ HTTPS
                        ▼
┌──────────────────────────────────────────────────────┐
│              Backend (Cloud Run)                     │
│         FastAPI + WebSocket Support                  │
│  Auto-scaling: 0-100 instances                       │
└───────────┬─────────────────┬────────────────────────┘
            │                 │
            ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│    Firestore     │  │   Vertex AI      │
│  (Ledger Store)  │  │ (Verification)   │
│  Multi-region    │  │ Custom Jobs      │
└──────────────────┘  └──────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────┐
│         Cloud Functions (Event-Driven)               │
│  - on_ledger_update: Update marketplace rankings     │
│  - monitor_verification: Check job status            │
└──────────────────────────────────────────────────────┘
```

### Setup Requirements

- Google Cloud account with **billing enabled** (mandatory)
- Project ID
- Gemini API key from [makersuite.google.com](https://makersuite.google.com/app/apikey)
- gcloud CLI installed and authenticated

---

## 🔬 Key Concepts

### Deterministic Replay

**Why it matters**: Verification requires reproducibility.

**How it works**:
- Environment uses seeded RNG
- Same seed + same actions = same trajectory
- Verifier replays policy greedily (no exploration)
- Rewards must match exactly

### Hash Chaining

**Why it matters**: Prevents tampering with ledger entries.

**How it works**:
```
Entry_N.current_hash = SHA256(
    Entry_N.policy_hash +
    Entry_N.verified_reward +
    Entry_N.timestamp +
    Entry_N-1.current_hash
)
```

Any modification breaks the chain and is immediately detectable.

### Verification vs Trust

**Traditional approach**: Trust agent-reported rewards  
**PolicyLedger approach**: Verify through deterministic replay

```
Training:    ε-greedy (explores)
Verification: Greedy (deterministic)
Reuse:       Greedy (no exploration)
```

---

## 🎓 Research Context

PolicyLedger demonstrates:
- Decentralized RL governance
- Blockchain-inspired verification
- Deterministic replay-based trust
- RL policy marketplace dynamics
- Zero-retraining policy transfer

### Security Scope

**What PolicyLedger provides:**
- ✅ Tamper-evident ledger (detects modifications)
- ✅ Deterministic verification (replay-based trust)
- ✅ Immutable policy records (hash-chained storage)

**What PolicyLedger does NOT prevent:**
- ❌ Sybil attacks (identity verification out of scope)
- ❌ DDoS attacks (network layer security)
- ❌ Side-channel attacks (implementation-level threats)

**Classification**: Cloud-native research prototype built on Google Cloud Platform with production-ready architecture.

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

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

- **Detailed Architecture**: [Architecture.md](Architecture.md)
- **API Documentation**: http://localhost:8000/docs (when running)
- **Live Demo**: http://localhost:5173 (when running)

---

**Built for HackNEXA 2025** ❤️
