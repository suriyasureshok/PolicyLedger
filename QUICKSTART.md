# PolicyLedger Quick Start Guide

**Get PolicyLedger running in under 5 minutes**

---

## 📋 Prerequisites

- ✅ **Python 3.10 or higher** ([Download](https://www.python.org/downloads/))
- ✅ **Node.js 18+ and npm** ([Download](https://nodejs.org/))
- ✅ **Git** ([Download](https://git-scm.com/))

**Check versions**:
```bash
python --version  # Should be 3.10+
node --version    # Should be 18+
npm --version     # Should be 9+
```

---

## 🚀 Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-org/PolicyLedger.git
cd PolicyLedger
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend/policy-ledger-insights
npm install
```

---

## ▶️ Running the Application

### Start Backend

```bash
cd backend
python start_server.py
```

**Backend running at**: `http://localhost:8000`

### Start Frontend (New Terminal)

```bash
cd frontend/policy-ledger-insights
npm run dev
```

**Frontend running at**: `http://localhost:5173`

---

## 🎯 First Steps

### 1. Access Web Interface

Open: **http://localhost:5173**

### 2. Try Live Training

1. Click **"Live Training"**
2. Configure parameters (Episodes: 500, Seed: 42)
3. Click **"Start Training"**
4. Watch real-time metrics

### 3. Explore Ledger

Navigate to **"Ledger"** to view verified policies

### 4. Check Marketplace

Go to **"Marketplace"** to see policy rankings

---

## 🧪 Testing

### API Test

```bash
curl http://localhost:8000/health
```

### Run Demo

```bash
cd backend
python demo.py
```

This runs the complete workflow (30-60 seconds).

---

## 📁 Project Structure

```
PolicyLedger/
├── backend/              # Python FastAPI backend
│   ├── src/
│   │   ├── agent/       # RL training
│   │   ├── verifier/    # Policy verification
│   │   ├── ledger/      # Storage
│   │   └── marketplace/ # Ranking
│   └── main.py          # API server
├── frontend/            # React + TypeScript frontend
│   └── policy-ledger-insights/
└── docs/                # Documentation
```

---

## 🐛 Troubleshooting

### Backend Won't Start

```bash
# Reinstall dependencies
cd backend
pip install -r requirements.txt
```

### Frontend Won't Start

```bash
# Reinstall dependencies
cd frontend/policy-ledger-insights
rm -rf node_modules package-lock.json
npm install
```

### Port Already in Use

**Windows**:
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## 📊 Key Commands

```bash
# Backend
cd backend
pip install -r requirements.txt      # Install
python start_server.py               # Run server
python demo.py                        # Demo workflow

# Frontend
cd frontend/policy-ledger-insights
npm install                          # Install
npm run dev                          # Run dev server
npm run build                        # Build production

# Testing
curl http://localhost:8000/health    # Health check
curl http://localhost:8000/docs      # API docs
```

---

## ✅ Quick Start Checklist

- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] Dependencies installed (backend + frontend)
- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Web interface accessible
- [ ] Demo completed successfully
- [ ] Live training tested

---

## 🎓 Next Steps

- 📖 Read [README.md](README.md) for project overview
- 🏗️ Study [Architecture.md](Architecture.md) for technical details
- ☁️ See [checklist.md](checklist.md) for Google Cloud deployment

---

**You're all set! 🎉**

**Last Updated**: December 30, 2025
