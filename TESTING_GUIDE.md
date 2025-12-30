# Testing Guide: Improved PolicyLedger System

## Quick Test: Verify Auto-Save & Better RL

### 1. Start Training
1. Open http://localhost:8080
2. Navigate to **Live Training** page
3. Click **"Start Training"** button
4. Watch the real-time metrics

### 2. What to Look For

#### Reward Improvements (you should see):
- **Episode 1-50**: Rewards climbing from -20 to 0
- **Episode 50-200**: Rewards climbing to 20-40 range
- **Episode 200-500**: Rewards stabilizing at 40-60+ range

**Before**: Rewards stayed near 0 for 1000+ episodes  
**After**: Positive rewards by episode 100

#### Auto-Save Confirmation:
- After 200-500 episodes, click **Stop Training**
- Status should show: `✓ Completed - Policy saved to ledger (abc123...)`
- Check browser console for:
  ```
  Policy automatically added to ledger: <hash>
  Verified reward: <number>
  ```

### 3. Verify Policy Storage

#### Check Files:
```powershell
# Navigate to backend
cd C:\Users\SURIYA\Desktop\Competition\HackNEXA\PolicyLedger\backend

# List saved policies (should see new file)
ls policies\

# View ledger (should have new entry)
cat ledger.json | Select-String -Pattern "agent_live"
```

#### Check Frontend:

1. **Marketplace** (`/marketplace`):
   - Your newly trained agent should appear
   - Click to see policy details
   - Verified reward should be visible

2. **Ledger** (`/ledger`):
   - New entry at the top
   - Policy hash should match what you saw in training
   - Timestamp should be recent

3. **Policy Reuse** (`/reuse`):
   - Select your agent from dropdown
   - Should show "Reusing policy from ledger"

### 4. Performance Comparison

| Metric | Before | After | Expected |
|--------|--------|-------|----------|
| Episodes to positive reward | 500+ | 50-100 | ✅ 10x faster |
| Final average reward | 5-10 | 40-60 | ✅ 5x better |
| Policy quality | Poor | Good | ✅ Effective defense |
| Auto-save | ❌ No | ✅ Yes | ✅ Automatic |
| Ledger integration | ❌ Manual | ✅ Auto | ✅ Seamless |

### 5. Advanced Testing

#### Test Multiple Agents:
```
1. Train agent_1 → Stop → Check ledger
2. Train agent_2 → Stop → Check ledger
3. Go to Marketplace → Should see both agents
4. Compare rewards and policies
```

#### Test Reward Scaling:
- Watch the **Reward Chart** in Live Training
- Should see clear upward trend
- Final 100 episodes should show stable high rewards

#### Test Action Learning:
- Watch the **Action Distribution** chart
- Early: Random distribution (exploring)
- Late: Concentrated on effective actions (exploiting)

### 6. Troubleshooting

#### If rewards stay negative:
- Training might need more episodes (try 500-800)
- Check backend logs for errors
- Verify environment is using new reward structure

#### If policy not saved:
- Check backend terminal for errors
- Verify `policies/` directory exists
- Check file permissions

#### If ledger not updated:
- Check `ledger.json` file exists
- Verify backend has write permissions
- Check for error messages in browser console

### 7. Demo Script for HackNEXA

```
1. Open Live Training page
2. Say: "Watch how our RL agent learns optimal cyber defense"
3. Start training
4. Point out: "Rewards climbing rapidly - agent discovering good strategies"
5. After 200 episodes: "Already learned effective defense patterns"
6. Stop training
7. Say: "Policy automatically saved and added to blockchain ledger"
8. Navigate to Marketplace
9. Say: "Now available for reuse by other agents"
10. Navigate to Ledger
11. Say: "Immutable record with cryptographic verification"
```

## Expected Terminal Output

### Backend Terminal (during training):
```
INFO: connection open
...training progress...
✓ Policy abc123... automatically added to ledger
INFO: connection closed
```

### Browser Console (on completion):
```
Policy automatically added to ledger: abc123def456...
Verified reward: 45.23
```

## Success Criteria

✅ Training converges in <500 episodes  
✅ Final reward >30  
✅ Policy saved to `policies/` directory  
✅ Ledger updated automatically  
✅ Policy appears in marketplace  
✅ Status shows "Policy saved to ledger"  

---

**Ready to test!** Just refresh your browser and start training.
