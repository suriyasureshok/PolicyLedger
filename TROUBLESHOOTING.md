# 🔧 Troubleshooting Guide

## Quick Diagnostic Checklist

```bash
# 1. Check Python version
python --version  # Should be 3.10+

# 2. Check Node version
node --version  # Should be 18+

# 3. Check if ports are free
netstat -an | findstr "8000"  # Backend port
netstat -an | findstr "5173"  # Frontend port

# 4. Verify backend dependencies
cd backend
pip list | findstr "fastapi"
pip list | findstr "websockets"

# 5. Verify frontend dependencies
cd frontend/policy-ledger-insights
npm list react
npm list recharts
```

---

## Common Issues & Solutions

### 1. Backend Won't Start

**Symptom**: `python start_server.py` fails

**Possible Causes**:

#### A. Port 8000 Already in Use
```bash
# Find process using port 8000
netstat -ano | findstr ":8000"

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

#### B. Missing Dependencies
```bash
cd backend
pip install -r requirements.txt
# Or install individually:
pip install fastapi uvicorn websockets numpy gymnasium
```

#### C. Python Version Too Old
```bash
python --version
# If < 3.10, upgrade Python:
# Download from python.org
```

**Solution**:
```bash
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
python start_server.py
```

---

### 2. Frontend Won't Start

**Symptom**: `npm run dev` fails

**Possible Causes**:

#### A. Node Modules Not Installed
```bash
cd frontend/policy-ledger-insights
npm install
```

#### B. Port 5173 Already in Use
```bash
# Edit vite.config.ts to use different port
# Or kill process using 5173
netstat -ano | findstr ":5173"
taskkill /PID <PID> /F
```

#### C. Node Version Too Old
```bash
node --version
# If < 18, download from nodejs.org
```

**Solution**:
```bash
cd frontend/policy-ledger-insights
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

### 3. WebSocket Connection Fails

**Symptom**: "Connection failed" in frontend

**Diagnostic Steps**:

```bash
# 1. Check if backend is running
curl http://localhost:8000/
# Should return: {"message":"PolicyLedger API is running"}

# 2. Check if WebSocket endpoint exists
curl http://localhost:8000/docs
# Should show FastAPI docs with /ws/train endpoint

# 3. Test WebSocket manually (PowerShell)
$ws = New-Object System.Net.WebSockets.ClientWebSocket
$uri = [System.Uri]::new("ws://localhost:8000/ws/train")
$ws.ConnectAsync($uri, [System.Threading.CancellationToken]::None)
```

**Common Fixes**:

#### A. CORS Issue
Edit `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Add frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### B. Backend Not Running
```bash
cd backend
python start_server.py
# Wait for: "Uvicorn running on http://0.0.0.0:8000"
```

#### C. Wrong WebSocket URL
Check `frontend/src/pages/LiveTraining.tsx`:
```typescript
const ws = new WebSocket('ws://localhost:8000/ws/train');
// Make sure port matches backend
```

---

### 4. Training Doesn't Start

**Symptom**: Click "Start Training" but nothing happens

**Diagnostic Steps**:

```bash
# 1. Check browser console (F12)
# Look for errors

# 2. Check network tab
# Look for failed requests to /live-training/start

# 3. Check backend logs
# Should see: "Starting training session..."
```

**Common Fixes**:

#### A. API Endpoint Wrong
Check `frontend/src/pages/LiveTraining.tsx`:
```typescript
const response = await fetch('http://localhost:8000/live-training/start', {
  method: 'POST',
  // ...
});
```

#### B. Backend Error
Check backend terminal for errors. Common issues:
- Environment import failed
- Config file missing
- Dependencies not installed

#### C. WebSocket Already Connected
```typescript
// In LiveTraining.tsx, check connection status
if (connectionStatus === 'connected') {
  // Can't start if already connected
}
```

**Solution**:
1. Stop backend
2. Restart backend
3. Refresh frontend
4. Try again

---

### 5. Charts Not Updating

**Symptom**: Training starts but charts don't update

**Diagnostic Steps**:

```bash
# 1. Check WebSocket messages (browser console)
ws.onmessage = (event) => {
  console.log('Received:', event.data);
};

# 2. Check if data is being sent (backend logs)
# Should see: "Sending metrics: episode=1, reward=..."
```

**Common Fixes**:

#### A. State Not Updating
Check `LiveTraining.tsx`:
```typescript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  setMetrics(prev => [...prev, data]); // Should update state
};
```

#### B. Chart Data Format Wrong
Recharts expects:
```typescript
interface DataPoint {
  episode: number;
  reward: number;
  // Must match backend message format
}
```

#### C. Re-render Issue
Add key to charts:
```typescript
<LineChart data={metrics} key={metrics.length}>
  {/* ... */}
</LineChart>
```

---

### 6. Training Converges Too Slowly

**Symptom**: Takes >500 episodes to converge

**Diagnostic Steps**:

```bash
# Check config
cat backend/src/utils/config.py
```

**Tuning Parameters**:

#### A. Learning Rate Too Low
```python
# In config.py
LEARNING_RATE = 0.1  # Increase to 0.2-0.3
```

#### B. Epsilon Decay Too Slow
```python
EPSILON_DECAY = 0.995  # Decrease to 0.99 or 0.98
```

#### C. Optimistic Value Too High/Low
```python
# In trainer.py
optimistic_value = 0.0  # Try 1.0 or 5.0
```

**Recommended Settings**:
```python
EPSILON_START = 1.0
EPSILON_END = 0.01
EPSILON_DECAY = 0.995
LEARNING_RATE = 0.1
DISCOUNT_FACTOR = 0.9
MAX_EPISODES = 1000
```

---

### 7. Verification Fails

**Symptom**: Policies marked as INVALID

**Diagnostic Steps**:

```bash
# Run verification manually
cd backend
python -m src.verifier.cli <policy_hash>
```

**Common Causes**:

#### A. Seed Mismatch
```python
# In verifier.py, check:
env = CyberDefenseEnv()
env.reset(seed=CANONICAL_SEED)  # Must match training seed
```

#### B. State Discretization Different
```python
# Both must use same discretize_state function
from src.agent.state import discretize_state
```

#### C. Tolerance Too Strict
```python
# In verifier.py
tolerance = abs(0.01 * claimed_reward)  # Might be too strict
# Try: tolerance = abs(0.05 * claimed_reward)
```

**Solution**:
1. Verify seeds match everywhere
2. Check discretization is consistent
3. Adjust tolerance if needed
4. Re-run verification

---

### 8. Reuse Performance Poor

**Symptom**: Reuse reward much lower than verified

**Diagnostic Steps**:

```bash
# Run reuse with debugging
cd backend
python -c "
from src.consumer.reuse import execute_policy
result = execute_policy('path/to/policy.json', episodes=10, seed=42)
print(result)
"
```

**Common Causes**:

#### A. Different Seed
```python
# Reuse MUST use different seed than training/verification
# In reuse.py:
env.reset(seed=different_seed)  # NOT CANONICAL_SEED
```

#### B. Epsilon Not Zero
```python
# In reuse.py, check:
def choose_action(state, policy):
    return policy[state]  # No epsilon, pure greedy
```

#### C. Q-table Modified
```python
# Reuse must NOT update Q-table
# Check that there's NO code like:
# q_table[state][action] = new_value  # This should NOT exist
```

**Expected Behavior**:
- Different seed → different performance
- But should still beat random baseline
- Variance is normal for different environments

---

### 9. Ledger Integrity Check Fails

**Symptom**: `verify_chain_integrity()` returns False

**Diagnostic Steps**:

```bash
# Check ledger manually
cd backend
python -c "
from src.ledger.ledger import PolicyLedger
ledger = PolicyLedger('ledger.json')
result = ledger.verify_chain_integrity()
print('Integrity:', result)
"
```

**Common Causes**:

#### A. Manual JSON Editing
```bash
# Never edit ledger.json manually!
# Recreate from scratch:
rm ledger.json
python -m src.agent.runner  # Retrain
```

#### B. Corrupted File
```bash
# Check JSON validity
python -m json.tool ledger.json
```

#### C. Hash Algorithm Changed
```python
# All code must use SHA-256
import hashlib
hash_algo = hashlib.sha256()  # Consistent everywhere
```

**Solution**:
1. Backup current ledger
2. Delete ledger.json
3. Retrain policies
4. Reverify integrity

---

### 10. Frontend Build Fails

**Symptom**: `npm run build` fails

**Common Errors**:

#### A. TypeScript Errors
```bash
# Check types
npm run type-check
```

Fix common type errors:
```typescript
// Before
const data = metrics;  // Type 'any'

// After
const data: TrainingMetrics[] = metrics;
```

#### B. Import Errors
```bash
# Check all imports exist
# Common issue: missing component import
```

#### C. Environment Variables
```bash
# Create .env.production
echo "VITE_API_URL=http://localhost:8000" > .env.production
```

**Solution**:
```bash
# Clean build
rm -rf dist node_modules
npm install
npm run build
```

---

## Performance Issues

### Slow Training

**Symptoms**: Training takes minutes instead of seconds

**Checks**:

```python
# 1. Check episode count
MAX_EPISODES = 1000  # Should be reasonable

# 2. Check max steps per episode
MAX_STEPS = 100  # Should be limited

# 3. Profile the code
import cProfile
cProfile.run('train_policy()')
```

**Optimizations**:

```python
# Use numpy for Q-table
import numpy as np
q_table = np.zeros((state_space, action_space))

# Vectorize operations
# Instead of loops, use numpy operations

# Reduce logging
# Comment out print statements in inner loops
```

---

### High Memory Usage

**Symptoms**: System runs out of memory

**Checks**:

```python
# Check Q-table size
print(f"Q-table entries: {len(q_table)}")

# Check metrics list size
print(f"Metrics stored: {len(metrics)}")
```

**Fixes**:

```python
# Limit metrics history
if len(metrics) > 1000:
    metrics = metrics[-1000:]  # Keep last 1000

# Clear old data
import gc
gc.collect()
```

---

## Environment-Specific Issues

### Windows

#### PowerShell Execution Policy
```powershell
# If scripts won't run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Path Issues
```powershell
# Use forward slashes or double backslashes
$path = "c:/users/..." # Good
$path = "c:\\users\\.." # Good
$path = "c:\users\..."  # Bad - escape sequences
```

### Linux/Mac

#### Permission Issues
```bash
chmod +x start.sh
chmod +x backend/start_server.py
```

#### Python Command
```bash
# Might need python3 instead of python
python3 --version
python3 start_server.py
```

---

## Debug Mode

### Enable Verbose Logging

**Backend**:
```python
# In main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend**:
```typescript
// In LiveTraining.tsx
const DEBUG = true;

if (DEBUG) {
  console.log('WebSocket message:', data);
}
```

### Check Logs

**Backend**:
```bash
# Redirect to file
python start_server.py > backend.log 2>&1

# View logs
tail -f backend.log
```

**Frontend**:
```bash
# Browser console (F12)
# Check Console, Network, and WebSocket tabs
```

---

## Testing Verification

### Manual Verification Test

```python
# backend/test_verification.py
from src.verifier.verifier import PolicyVerifier
from src.agent.runner import PolicyClaim

# Create verifier
verifier = PolicyVerifier()

# Load a claim
with open('policies/test_policy.json') as f:
    claim = PolicyClaim(**json.load(f))

# Verify
result = verifier.verify(claim)
print(f"Result: {result.status}")
print(f"Verified reward: {result.verified_reward}")
```

---

## Reset Everything

### Nuclear Option (Fresh Start)

```bash
# 1. Stop all running processes
taskkill /F /IM python.exe
taskkill /F /IM node.exe

# 2. Delete all generated files
cd backend
rm ledger.json
rm -rf policies/*
rm -rf __pycache__

# 3. Reinstall dependencies
pip install -r requirements.txt

# 4. Frontend
cd frontend/policy-ledger-insights
rm -rf node_modules dist
npm install

# 5. Start fresh
cd backend
python start_server.py

# In another terminal:
cd frontend/policy-ledger-insights
npm run dev
```

---

## Getting Help

### Information to Provide

When asking for help, include:

1. **Error message** (exact text)
2. **What you were doing** (steps to reproduce)
3. **System info**:
   ```bash
   python --version
   node --version
   pip list | grep fastapi
   ```
4. **Logs** (backend terminal output)
5. **Browser console** (if frontend issue)

### Check These First

- [ ] Python 3.10+
- [ ] Node 18+
- [ ] All dependencies installed
- [ ] Ports 8000 & 5173 free
- [ ] No firewall blocking
- [ ] Backend running before frontend
- [ ] Browser console for errors

---

## Success Indicators

### Everything Working

You should see:

1. **Backend terminal**:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   INFO:     WebSocket connection accepted
   INFO:     Starting training session...
   INFO:     Episode 1 complete, reward: -45.2
   ```

2. **Frontend**:
   - Green "Connected" status
   - Charts updating in real-time
   - No console errors

3. **Browser Network Tab**:
   - WebSocket connection: "101 Switching Protocols"
   - Messages flowing both ways

4. **Performance**:
   - Training converges in ~30 seconds
   - Charts smooth, no lag
   - Final reward ~7-10

---

## Quick Reference: Common Commands

```bash
# Start backend
cd backend && python start_server.py

# Start frontend
cd frontend/policy-ledger-insights && npm run dev

# Install backend deps
cd backend && pip install -r requirements.txt

# Install frontend deps
cd frontend/policy-ledger-insights && npm install

# Run tests
cd backend && pytest tests/

# Check logs
tail -f backend.log

# Kill process on port
netstat -ano | findstr ":8000"
taskkill /PID <PID> /F

# Fresh start
rm ledger.json policies/* && python start_server.py
```

---

**Still stuck?** Check:
- [README.md](README.md) for architecture
- [QUICKSTART.md](QUICKSTART.md) for setup
- [LIVE_TRAINING_GUIDE.md](LIVE_TRAINING_GUIDE.md) for training

**Everything working?** Great! Now see:
- [PRESENTATION_SCRIPT.md](PRESENTATION_SCRIPT.md) for demo prep
