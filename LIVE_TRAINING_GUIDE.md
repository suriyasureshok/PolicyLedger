# PolicyLedger - Live Training Quick Start

## 🎯 Overview

PolicyLedger now features **real-time reinforcement learning visualization** with interactive controls. Train RL agents directly from the web interface and watch them learn in real-time!

## 🚀 Quick Start

### 1. Start the Backend Server

```bash
cd backend

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the server
python start_server.py
```

The backend will start on **http://localhost:8000** with:
- REST API: `http://localhost:8000`
- WebSocket: `ws://localhost:8000/ws/train/{agent_id}`
- API Docs: `http://localhost:8000/docs`

### 2. Start the Frontend

```bash
cd frontend/policy-ledger-insights

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

The frontend will start on **http://localhost:5173**

### 3. Open Live Training

1. Navigate to **http://localhost:5173**
2. Click on **"Live Training"** in the navigation
3. Configure your training parameters:
   - **Agent ID**: Unique identifier for your agent
   - **Random Seed**: For reproducible results
   - **Max Episodes**: Leave blank for continuous training
   - **Epsilon Start/End/Decay**: Exploration parameters
4. Click **"Start Training"** and watch your agent learn!

## 📊 Real-Time Visualizations

The Live Training page shows:
- **Reward Over Episodes**: Episode-by-episode rewards with rolling average
- **Exploration Rate (Epsilon)**: How exploration decreases over time
- **Q-Table Growth**: Number of state-action pairs learned
- **Action Distribution**: Which actions the agent is taking

## 🎮 Interactive Controls

- **Start Training**: Begin a new training session
- **Stop Training**: Stop training at any time
- **Configure**: Adjust parameters between sessions

## ⚙️ Training Configuration

### Epsilon (Exploration)
- **Epsilon Start (1.0)**: Initial exploration rate (100% random)
- **Epsilon End (0.01)**: Final exploration rate (1% random)
- **Epsilon Decay (0.995)**: How quickly to reduce exploration

### Episodes
- **Max Episodes**: Set a limit or leave blank for continuous training
- **Seed**: Use the same seed for reproducible results

## 🏗️ Architecture

```
Frontend (React + TypeScript)
    ↓ WebSocket Connection
Backend (FastAPI + Python)
    ↓ Real-time Training
CyberDefenseEnv (RL Environment)
    ↓ Q-Learning
Trained Policy → Verification → Ledger → Marketplace
```

## 📡 API Endpoints

### WebSocket
- `ws://localhost:8000/ws/train/{agent_id}` - Live training updates

### REST
- `POST /training/start` - Start training session
- `POST /training/control` - Stop/pause training
- `GET /training/sessions` - List all active sessions
- `GET /training/session/{agent_id}` - Get session details

## 🔧 System Components

### Backend (`/backend`)
- **main.py**: FastAPI server with WebSocket support
- **src/training/live_trainer.py**: Real-time training manager
- **src/environments/cyber_env.py**: Cyber defense simulation
- **src/agent/trainer.py**: Q-learning implementation

### Frontend (`/frontend/policy-ledger-insights`)
- **src/pages/LiveTraining.tsx**: Interactive training interface
- **src/components/Navigation.tsx**: Navigation with Live Training link
- **src/lib/api.ts**: API client

## 🎯 Key Features

### ✅ Real-Time Training
- Train agents directly from the browser
- See learning progress as it happens
- Stop training at any time

### ✅ Interactive Controls
- Configure hyperparameters
- Start/stop on demand
- No fixed episode limits

### ✅ Live Visualization
- Real-time reward charts
- Q-table growth tracking
- Action distribution analysis
- Epsilon decay visualization

### ✅ No Mock Data
- All visualizations use real training data
- WebSocket streaming for instant updates
- Episode-by-episode metrics

## 🐛 Troubleshooting

### WebSocket Connection Issues
- Ensure backend is running on port 8000
- Check firewall settings
- Verify no CORS errors in browser console

### Training Not Starting
- Check backend logs for errors
- Ensure dependencies are installed
- Verify environment configuration

### Frontend Not Loading
- Run `npm install` in frontend directory
- Clear browser cache
- Check for TypeScript errors

## 📦 Dependencies

### Backend
- FastAPI ≥0.104.0
- uvicorn[standard] ≥0.24.0
- websockets ≥12.0
- numpy ≥1.21.0
- gymnasium ≥0.29.0

### Frontend
- React 18+
- TypeScript 5+
- Recharts (for live charts)
- shadcn/ui components

## 🚦 Next Steps

After training:
1. **Verify** your policy in the Verification page
2. **Submit** to the ledger for immutability
3. **Compete** in the marketplace
4. **Reuse** winning policies without retraining

## 📚 Documentation

- Full API docs: `http://localhost:8000/docs`
- Frontend routes: `/overview`, `/live-training`, `/submissions`, etc.
- Environment details: `backend/src/environments/cyber_env.py`

## 🎓 Learn More

- [Original Architecture](docs/PHASE_4_ARCHITECTURE.md)
- [Cyber Defense Environment](docs/IMPLEMENTATION_SUMMARY_PHASE_11.md)
- [Q-Learning Details](backend/src/agent/trainer.py)

---

**Happy Training! 🚀**
