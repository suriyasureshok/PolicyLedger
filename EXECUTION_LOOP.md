# PolicyLedger Execution Loop - The Sacred Contract

## 🎯 The One True Loop

**CRITICAL INSIGHT**: Training, verification, and reuse MUST use the EXACT SAME execution loop.

The only difference is **who chooses the action**.

## 📐 The Canonical Loop

```python
# CANONICAL EXECUTION LOOP
# Used by: Training, Verification, Reuse

def execute_policy_episode(env, action_selector, state_discretizer):
    """
    The one true execution loop.
    
    Args:
        env: Environment instance
        action_selector: Function that returns action given state
                        - Training: epsilon-greedy from Q-table
                        - Verification: greedy from policy
                        - Reuse: greedy from policy
        state_discretizer: Function to discretize state
    
    Returns:
        (total_reward, action_sequence, state_sequence)
    """
    # Reset environment (DETERMINISTIC with seed)
    state_dict = env.reset()
    state = state_discretizer(state_dict)
    
    total_reward = 0.0
    action_sequence = []
    state_sequence = [state]
    done = False
    
    # Execute until done
    while not done:
        # Get action (ONLY DIFFERENCE between modes)
        action = action_selector(state)
        action_sequence.append(action)
        
        # Take action in environment
        state_dict, reward, done = env.step(action)
        next_state = state_discretizer(state_dict)
        
        # Accumulate reward
        total_reward += reward
        
        # Record trajectory
        state_sequence.append(next_state)
        
        # Move to next state
        state = next_state
    
    return total_reward, action_sequence, state_sequence
```

## 🔑 Key Differences by Mode

### Training
```python
def train_episode(env, q_table, epsilon):
    def action_selector(state):
        return select_action(state, q_table, epsilon)  # epsilon-greedy
    
    reward, actions, states = execute_policy_episode(
        env, action_selector, discretize_state
    )
    
    # ADDITIONALLY: Update Q-table
    # ... Q-learning updates ...
    
    return reward, actions
```

### Verification
```python
def verify_policy(env, policy):
    def action_selector(state):
        return policy.get(state, default_action)  # greedy, no exploration
    
    reward, actions, states = execute_policy_episode(
        env, action_selector, discretize_state
    )
    
    # NO LEARNING
    return reward
```

### Reuse
```python
def reuse_policy(env, policy):
    def action_selector(state):
        return policy.get(state, default_action)  # greedy, no exploration
    
    reward, actions, states = execute_policy_episode(
        env, action_selector, discretize_state
    )
    
    # NO LEARNING
    return reward
```

## ✅ Current Implementation Status

### Training (`src/agent/trainer.py`)
- ✓ Uses correct loop structure
- ✓ Epsilon-greedy action selection
- ✓ Q-learning updates
- ✓ Returns reward + actions

### Verification (`src/verifier/verifier.py`)
- ✓ Uses correct loop structure
- ✓ Greedy policy execution (epsilon=0)
- ✓ No Q-table updates
- ✓ Deterministic replay

### Reuse (`src/consumer/reuse.py`)
- ⚠️ NEEDS REVIEW
- Must ensure NO learning occurs
- Must use greedy execution (epsilon=0)
- Must be identical to verification loop

## 🔧 Required Actions

1. **Extract Common Loop** (Optional but recommended)
   - Create `src/shared/execution.py`
   - Define `execute_policy_episode()`
   - Import in training, verification, reuse

2. **Verify Reuse Module**
   - Check that no Q-table updates occur
   - Check that epsilon=0
   - Check loop matches verification

3. **Add Tests**
   - Test that same policy + same seed = same reward
   - Test across training/verification/reuse
   - Test determinism

## 🎓 The Philosophy

**One Loop to Rule Them All**

The execution loop is the truth. It's the physics of your system.

- Training: Agent explores and learns
- Verification: Judge replays and measures
- Reuse: Consumer deploys and benefits

Same physics. Same environment. Same rules.

**Only the action chooser differs.**

This is why verification works.
This is why reuse is safe.
This is the foundation of trust.

---

**Remember**: If training, verification, and reuse diverge, the entire system breaks.

Keep the loop sacred.
