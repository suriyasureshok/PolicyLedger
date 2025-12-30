# Multi-Agent Training Arena - Quick Start Guide

## 🎯 What's New

**Multi-Agent Training Arena** allows you to:
- ✅ Train multiple RL agents simultaneously
- ✅ Compare performance in real-time
- ✅ Run competitive experiments with different configurations
- ✅ Automatically save all policies to ledger
- ✅ Visual leaderboard and performance comparison

## 🚀 How to Use

### 1. Access the Arena

Navigate to: **http://localhost:8080/multi-agent**

Or click **"Multi-Agent Arena"** in the navigation menu

### 2. Add Your First Agent

1. Click **"Add Agent"** button
2. Enter agent details:
   - **Agent Name**: e.g., "Alpha", "Beta", "Gamma"
   - **Random Seed**: Different seeds = different exploration patterns
   - **Max Episodes**: How many episodes to train (leave blank for infinite)
3. Click **"Add Agent"**

### 3. Add More Agents

Repeat step 2 to add multiple agents. Each agent gets:
- Unique color for easy identification
- Independent training session
- Separate WebSocket connection
- Own metrics tracking

### 4. Start Training

**Option A: Train All Agents Together**
- Click **"Start All"** button (top-right)
- All agents begin training simultaneously

**Option B: Train Individual Agents**
- Click **"Start"** on specific agent card
- Train agents one by one or in custom groups

### 5. Monitor Performance

**Performance Comparison Chart** (top):
- Shows average reward curves for all agents
- Color-coded by agent
- Real-time updates as training progresses

**Individual Agent Cards**:
- Current episode & reward
- Live mini-chart of progress
- Q-table size & epsilon value
- Training time

**Leaderboard Table** (bottom):
- Ranked by best average reward
- Shows current status of all agents
- Compare final performance

### 6. Stop Training

**Option A: Stop All**
- Click **"Stop All"** button

**Option B: Stop Individual**
- Click **"Stop"** on specific agent card

### 7. Remove Agents

- Click trash icon on agent card
- Only works when agent is stopped

## 💡 Example Use Cases

### Experiment 1: Seed Comparison
Test how different random seeds affect learning:
```
Agent Alpha - Seed: 42
Agent Beta  - Seed: 123
Agent Gamma - Seed: 999
```

### Experiment 2: Hyperparameter Tuning
Compare different exploration strategies (future enhancement):
```
Agent Conservative - Epsilon End: 0.1 (more exploration)
Agent Aggressive   - Epsilon End: 0.01 (more exploitation)
```

### Experiment 3: Competitive Training
Train a team of agents to see which learns fastest:
```
Agent Red   - Team A
Agent Blue  - Team B
Agent Green - Team C
```

## 📊 What Gets Saved

When training completes, each agent automatically:
1. ✅ Saves policy to `backend/policies/{hash}.json`
2. ✅ Adds entry to `backend/ledger.json`
3. ✅ Becomes available in Marketplace
4. ✅ Shows completion status with policy hash

## 🎨 Visual Features

- **Color-coded agents**: Each agent has unique color
- **Real-time charts**: Performance comparison updates live
- **Status indicators**: Green = training, Gray = stopped
- **Leaderboard**: Automatic ranking by performance
- **Mini-charts**: Individual progress on each card

## 🔧 Technical Details

### Backend Support
The backend already supports multiple concurrent sessions:
- Each agent gets independent `TrainingState`
- Separate WebSocket connections per agent
- No interference between agents
- Thread-safe session management

### Frontend Architecture
- Independent WebSocket per agent
- Reactive state management
- Efficient chart rendering (last 500 points)
- Automatic color assignment

### Performance
- Can handle 5-10 agents simultaneously
- Each agent: ~10-50 updates/second
- Charts optimized for smooth rendering
- No lag with multiple active sessions

## 🐛 Troubleshooting

**Problem: Agent won't start**
- Check backend is running: http://localhost:8000
- Check browser console for errors
- Verify unique agent names

**Problem: Performance comparison not showing**
- Need at least 1 agent with metrics
- Chart appears after first few episodes
- Refresh page if stuck

**Problem: WebSocket errors**
- Restart backend server
- Clear browser cache
- Check for port conflicts

## 🎯 Best Practices

1. **Naming**: Use descriptive names (Alpha, Fast, Conservative)
2. **Seeds**: Use different seeds for fair comparison
3. **Episodes**: Start with 200-500 for quick tests
4. **Monitoring**: Watch first 50 episodes for convergence
5. **Cleanup**: Remove unused agents to reduce clutter

## 📈 Expected Results

### Episode 0-50
- Random exploration
- Negative/low rewards
- High epsilon (>0.8)

### Episode 50-200
- Pattern recognition
- Rewards climbing to 20-40
- Epsilon decreasing (0.3-0.6)

### Episode 200-500
- Policy convergence
- Stable rewards (40-60+)
- Low epsilon (<0.2)

## 🚀 Demo Script for HackNEXA

1. **Setup** (30 seconds):
   - Navigate to Multi-Agent Arena
   - Add 3 agents: "Alpha", "Beta", "Gamma"
   - Use seeds: 42, 123, 999

2. **Launch** (10 seconds):
   - Click "Start All"
   - Show all agents training simultaneously

3. **Monitor** (1 minute):
   - Point out performance comparison chart
   - Show individual agent progress
   - Highlight leaderboard updates

4. **Results** (30 seconds):
   - Stop after 200 episodes
   - Compare final rewards
   - Show policies saved to ledger

5. **Explain** (1 minute):
   - "Each agent learns independently"
   - "Different seeds = different strategies"
   - "All policies automatically saved"
   - "Ready for reuse in production"

---

**Ready to train!** Open http://localhost:8080/multi-agent and start your first multi-agent experiment! 🎉
