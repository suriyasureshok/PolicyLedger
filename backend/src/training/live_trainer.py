"""
Live Training System with Real-time Updates

This module provides continuous training with WebSocket streaming for
real-time visualization in the frontend.

Features:
- Continuous training (until stopped by user)
- Real-time episode-by-episode updates
- Training metrics streaming
- Start/stop controls from frontend
"""

import asyncio
from typing import Dict, Optional, Callable
from dataclasses import dataclass, asdict
import time
from datetime import datetime

from src.agent.trainer import initialize_q_table, train_episode, select_action
from src.agent.state import discretize_state
from src.agent.double_q_learning import (
    initialize_double_q_tables, 
    ExperienceReplay, 
    merge_q_tables
)
from src.environments.cyber_env import CyberDefenseEnv
from src.shared.config import (
    EPSILON_START, EPSILON_END, EPSILON_DECAY,
    REPLAY_BUFFER_SIZE, REPLAY_BATCH_SIZE, REPLAY_START_SIZE
)


@dataclass
class TrainingMetrics:
    """Real-time training metrics for frontend visualization"""
    episode: int
    reward: float
    avg_reward: float  # Rolling average
    epsilon: float
    q_table_size: int
    actions_taken: Dict[str, int]
    timestamp: str
    training_time: float
    
    def to_dict(self):
        return asdict(self)


@dataclass
class TrainingState:
    """Current state of a training session"""
    agent_id: str
    status: str  # "running", "stopped", "completed", "error"
    episode: int
    total_episodes: Optional[int]
    start_time: float
    metrics_history: list
    q_table: Dict
    q_table_a: Dict  # First Q-table for Double Q-Learning
    q_table_b: Dict  # Second Q-table for Double Q-Learning
    replay_buffer: ExperienceReplay  # Experience replay buffer
    env: CyberDefenseEnv
    seed: int


class LiveTrainingManager:
    """
    Manages live training sessions with real-time updates.
    
    Supports multiple concurrent training sessions, each streaming
    updates to connected WebSocket clients.
    """
    
    def __init__(self):
        self.sessions: Dict[str, TrainingState] = {}
        self.callbacks: Dict[str, Callable] = {}
    
    async def start_training(
        self,
        agent_id: str,
        seed: int,
        max_episodes: Optional[int],
        callback: Callable,
        config: Dict
    ) -> None:
        """
        Start a new training session with real-time updates.
        
        Args:
            agent_id: Unique identifier for this agent
            seed: Random seed for reproducibility
            max_episodes: Maximum episodes (None = infinite until stopped)
            callback: Async function to call with each update
            config: Training configuration (learning rate, epsilon, etc.)
        """
        print(f"🏁 Starting training for {agent_id}")
        print(f"   Seed: {seed}, Max Episodes: {max_episodes}")
        print(f"   Config: {config}")
        print(f"   🚀 Using Double Q-Learning with Experience Replay")
        
        # Initialize environment
        env = CyberDefenseEnv(seed=seed)
        
        # Initialize Double Q-Learning tables
        q_table_a, q_table_b = initialize_double_q_tables()
        
        # Initialize Experience Replay buffer
        replay_buffer = ExperienceReplay(
            max_size=REPLAY_BUFFER_SIZE,
            batch_size=REPLAY_BATCH_SIZE,
            min_size=REPLAY_START_SIZE
        )
        
        # Merge Q-tables for compatibility (used for final policy)
        q_table = merge_q_tables(q_table_a, q_table_b)
        
        # Create training state
        state = TrainingState(
            agent_id=agent_id,
            status="running",
            episode=0,
            total_episodes=max_episodes,
            start_time=time.time(),
            metrics_history=[],
            q_table=q_table,
            q_table_a=q_table_a,
            q_table_b=q_table_b,
            replay_buffer=replay_buffer,
            env=env,
            seed=seed
        )
        
        self.sessions[agent_id] = state
        self.callbacks[agent_id] = callback
        
        print(f"✓ Session created for {agent_id}")
        
        # Start training loop
        await self._training_loop(agent_id, config)
        
        print(f"🏁 Training loop ended for {agent_id}")
    
    async def _training_loop(self, agent_id: str, config: Dict):
        """Main training loop with real-time updates"""
        print(f"🔁 Entering training loop for {agent_id}")
        state = self.sessions[agent_id]
        epsilon = config.get('epsilon_start', EPSILON_START)
        epsilon_end = config.get('epsilon_end', EPSILON_END)
        epsilon_decay = config.get('epsilon_decay', EPSILON_DECAY)
        
        print(f"   Epsilon: {epsilon} → {epsilon_end} (decay: {epsilon_decay})")
        
        episode = 0
        rewards_window = []  # For rolling average
        window_size = 100
        
        try:
            print(f"   Initial status: {state.status}")
            while state.status == "running":
                if episode % 10 == 0:  # Log every 10 episodes
                    print(f"   {agent_id} - Episode {episode}, status: {state.status}")
                # Check if we've reached max episodes
                if state.total_episodes and episode >= state.total_episodes:
                    state.status = "completed"
                    break
                
                # Train one episode with Double Q-Learning
                episode_start = time.time()
                reward, actions = train_episode(
                    state.env,
                    state.q_table,
                    epsilon,
                    discretize_state,
                    q_table_a=state.q_table_a,
                    q_table_b=state.q_table_b,
                    replay_buffer=state.replay_buffer
                )
                episode_time = time.time() - episode_start
                
                # Update merged Q-table for metrics
                state.q_table = merge_q_tables(state.q_table_a, state.q_table_b)
                
                # Update rolling average
                rewards_window.append(reward)
                if len(rewards_window) > window_size:
                    rewards_window.pop(0)
                avg_reward = sum(rewards_window) / len(rewards_window)
                
                # Create metrics
                metrics = TrainingMetrics(
                    episode=episode,
                    reward=reward,
                    avg_reward=avg_reward,
                    epsilon=epsilon,
                    q_table_size=len(state.q_table),
                    actions_taken=actions,
                    timestamp=datetime.now().isoformat(),
                    training_time=time.time() - state.start_time
                )
                
                # Store metrics
                state.metrics_history.append(metrics)
                state.episode = episode
                
                # Send update to frontend
                callback = self.callbacks.get(agent_id)
                if callback:
                    try:
                        await callback({
                            "type": "training_update",
                            "agent_id": agent_id,
                            "metrics": metrics.to_dict(),
                            "status": state.status
                        })
                    except Exception as cb_err:
                        print(f"   ⚠ Callback error for {agent_id}: {cb_err}")
                        # Don't stop training, just continue without sending updates
                        pass
                
                # Decay epsilon
                epsilon = max(epsilon_end, epsilon * epsilon_decay)
                
                episode += 1
                
                # Small delay to prevent overwhelming the frontend
                await asyncio.sleep(0.01)
        
        except Exception as e:
            print(f"❌ ERROR in training loop for {agent_id}: {e}")
            import traceback
            traceback.print_exc()
            state.status = "error"
            if agent_id in self.callbacks:
                try:
                    await self.callbacks[agent_id]({
                        "type": "error",
                        "agent_id": agent_id,
                        "error": str(e)
                    })
                except:
                    print(f"   Failed to send error to callback")
        
        finally:
            # Save policy and add to ledger if training completed successfully
            if state.status in ["completed", "stopped"] and episode > 0:
                try:
                    from src.agent.policy import extract_policy, serialize_policy, hash_policy
                    from pathlib import Path
                    import json
                    
                    # Extract policy from Q-table
                    policy = extract_policy(state.q_table)
                    
                    # Serialize to bytes for hashing
                    policy_bytes = serialize_policy(policy)
                    policy_hash = hash_policy(policy_bytes)
                    
                    # Save policy to disk as JSON
                    policy_dir = Path("policies")
                    policy_dir.mkdir(exist_ok=True)
                    policy_path = policy_dir / f"{policy_hash}.json"
                    
                    # Convert policy to JSON-serializable format
                    serializable_policy = {
                        str(state): action
                        for state, action in policy.items()
                    }
                    
                    with open(policy_path, 'w') as f:
                        json.dump(serializable_policy, f, indent=2)
                    
                    # Calculate average reward for ledger
                    if state.metrics_history:
                        recent_rewards = [m.reward for m in state.metrics_history[-100:]]
                        verified_reward = sum(recent_rewards) / len(recent_rewards)
                    else:
                        verified_reward = 0.0
                    
                    # Store for potential ledger addition
                    state.final_policy_hash = policy_hash
                    state.final_reward = verified_reward
                    
                    print(f"✓ Policy saved: {policy_hash[:16]}... (reward: {verified_reward:.2f})")
                    
                except Exception as e:
                    print(f"Error saving policy: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Send final update
            if agent_id in self.callbacks:
                final_data = {
                    "type": "training_complete",
                    "agent_id": agent_id,
                    "status": state.status,
                    "total_episodes": episode,
                    "total_time": time.time() - state.start_time
                }
                
                # Include policy info if saved
                if hasattr(state, 'final_policy_hash'):
                    final_data["policy_hash"] = state.final_policy_hash
                    final_data["verified_reward"] = state.final_reward
                    final_data["policy_saved"] = True
                
                await self.callbacks[agent_id](final_data)
    
    def stop_training(self, agent_id: str) -> bool:
        """Stop a training session"""
        if agent_id in self.sessions:
            self.sessions[agent_id].status = "stopped"
            return True
        return False
    
    def get_session_state(self, agent_id: str) -> Optional[TrainingState]:
        """Get current state of a training session"""
        return self.sessions.get(agent_id)
    
    def get_all_sessions(self) -> Dict[str, Dict]:
        """Get summary of all active sessions"""
        return {
            agent_id: {
                "status": state.status,
                "episode": state.episode,
                "total_episodes": state.total_episodes,
                "running_time": time.time() - state.start_time
            }
            for agent_id, state in self.sessions.items()
        }
    
    def cleanup_session(self, agent_id: str):
        """Remove a completed session"""
        if agent_id in self.sessions:
            del self.sessions[agent_id]
        if agent_id in self.callbacks:
            del self.callbacks[agent_id]


# Global training manager instance
training_manager = LiveTrainingManager()
