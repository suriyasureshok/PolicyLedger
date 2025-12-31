"""
PolicyLedger Backend API

FastAPI server that provides REST and WebSocket endpoints for:
- Real-time agent training with live visualization
- Policy verification
- Ledger management
- Marketplace operations
- Policy reuse

This bridges the PolicyLedger core with the frontend dashboard.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Set
import json
import time
from datetime import datetime
from pathlib import Path
import asyncio
import ast
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.agent.runner import run_agent, PolicyClaim
from src.verifier.verifier import PolicyVerifier
from src.ledger.ledger import PolicyLedger, verify_chain_integrity
from src.marketplace.ranking import select_best_policy, PolicyMarketplace
from src.consumer.reuse import reuse_best_policy
from src.training.live_trainer import training_manager
from src.explainability.explainer import Explainer
from src.explainability.metrics import ExplanationMetrics
from src.execution.live_executor import (
    LivePolicyExecutor,
    ExecutionConfig,
    AdaptiveEnvironmentPressure,
    PartialObservabilityFilter,
    PolicyConfidenceCalculator
)

# Initialize FastAPI app
app = FastAPI(
    title="PolicyLedger API",
    description="Decentralized RL Policy Marketplace",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
LEDGER_FILE = "ledger.json"
ledger = PolicyLedger(LEDGER_FILE)
verifier = PolicyVerifier()
explainer = Explainer(use_gemini=False)  # Use fallback explainer only

# Training state
training_jobs = {}

# WebSocket connections for live training updates
active_connections: Set[WebSocket] = set()


# ============================================================================
# Helper Functions
# ============================================================================

def load_policy_from_file(policy_path: Path) -> Dict:
    """
    Load and parse policy from JSON file.
    
    Handles nested structure and safely parses tuple keys.
    """
    with open(policy_path, 'r') as f:
        policy_data = json.load(f)
    
    # Handle nested structure (policy might be under "policy" key)
    if "policy" in policy_data:
        policy_dict = policy_data["policy"]
    else:
        policy_dict = policy_data
    
    # Parse tuple keys safely
    policy = {}
    for k, v in policy_dict.items():
        try:
            # Parse tuple string like "(0, 1, 2, 0, 1)"
            key = tuple(map(int, k.strip('()').split(', ')))
            policy[key] = v
        except (ValueError, AttributeError):
            # Try ast.literal_eval as fallback
            try:
                policy[ast.literal_eval(k)] = v
            except Exception as e:
                print(f"Warning: Could not parse policy key '{k}': {e}")
    
    print(f"  [Policy Loader] Loaded policy from {policy_path.name}")
    print(f"  [Policy Loader] Policy has {len(policy)} states")
    
    return policy


# ============================================================================
# WebSocket Connection Manager
# ============================================================================

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, agent_id: str = "global"):
        await websocket.accept()
        if agent_id not in self.active_connections:
            self.active_connections[agent_id] = set()
        self.active_connections[agent_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, agent_id: str = "global"):
        if agent_id in self.active_connections:
            self.active_connections[agent_id].discard(websocket)
    
    async def broadcast(self, message: dict, agent_id: str = "global"):
        """Broadcast message to all connected clients for this agent"""
        if agent_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[agent_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.active_connections[agent_id].discard(conn)

manager = ConnectionManager()


# ============================================================================
# Pydantic Models
# ============================================================================

class AgentTrainRequest(BaseModel):
    agent_id: str
    seed: int = 42
    episodes: int = 150


class LiveTrainRequest(BaseModel):
    """Configuration for live training session"""
    agent_id: str
    seed: int = 42
    max_episodes: Optional[int] = None  # None = infinite until stopped
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: float = 0.995
    learning_rate: float = 0.1
    discount_factor: float = 0.99


class TrainingControlRequest(BaseModel):
    """Control request for training session"""
    agent_id: str
    action: str = Field(..., pattern="^(stop|pause|resume)$")


class AgentTrainResponse(BaseModel):
    agent_id: str
    claimed_reward: float
    policy_hash: str
    status: str
    training_time: float


class VerifyResponse(BaseModel):
    agent_id: str
    verified_reward: float
    status: str
    reason: Optional[str] = None


class LedgerEntryResponse(BaseModel):
    policy_hash: str
    verified_reward: float
    agent_id: str
    timestamp: str
    previous_hash: str
    current_hash: str


class MarketplacePolicy(BaseModel):
    agent_id: str
    policy_hash: str
    verified_reward: float
    timestamp: str
    rank: int


class ReuseResponse(BaseModel):
    agent_id: str
    policy_hash: str
    verified_reward: float
    reused_reward: float
    baseline_reward: float
    improvement: float


class SystemStats(BaseModel):
    total_agents: int
    total_policies: int
    verified_policies: int
    ledger_entries: int
    chain_integrity: bool
    best_policy_reward: Optional[float]


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "PolicyLedger API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ledger_file": LEDGER_FILE,
        "ledger_size": len(ledger.read_all())
    }


@app.post("/agent/train", response_model=AgentTrainResponse)
async def train_agent_endpoint(request: AgentTrainRequest, background_tasks: BackgroundTasks):
    """
    Train a new agent and return policy claim.
    
    This endpoint:
    - Trains an agent with specified parameters
    - Returns the claimed reward and policy hash
    - Does NOT verify or add to ledger (separate steps)
    """
    try:
        start_time = time.time()
        
        # Train agent
        claim = run_agent(
            agent_id=request.agent_id,
            seed=request.seed,
            episodes=request.episodes
        )
        
        training_time = time.time() - start_time
        
        # Store claim for verification
        training_jobs[request.agent_id] = {
            "claim": claim,
            "timestamp": datetime.now().isoformat(),
            "training_time": training_time
        }
        
        return AgentTrainResponse(
            agent_id=claim.agent_id,
            claimed_reward=claim.claimed_reward,
            policy_hash=claim.policy_hash,
            status="trained",
            training_time=training_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Live Training Endpoints (WebSocket)
# ============================================================================

@app.websocket("/ws/train/{agent_id}")
async def websocket_train_endpoint(websocket: WebSocket, agent_id: str):
    """
    WebSocket endpoint for live training with real-time updates.
    
    The frontend connects to this endpoint and receives:
    - Episode-by-episode training metrics
    - Real-time reward charts data
    - Q-table growth stats
    - Action distribution
    
    Send configuration via JSON message after connecting:
    {
        "seed": 42,
        "max_episodes": null,  // null = infinite
        "epsilon_start": 1.0,
        "epsilon_end": 0.01,
        "epsilon_decay": 0.995,
        "env_type": "standard"  // Environment type: standard, short_burst, extended, high_pressure, sparse_attacks
    }
    
    Send control commands:
    {"action": "stop"}
    """
    await manager.connect(websocket, agent_id)
    
    try:
        # Wait for configuration
        config_data = await websocket.receive_json()
        
        # Define callback for training updates
        async def send_update(data):
            try:
                await websocket.send_json(data)
            except:
                pass
        
        # Start training in background
        training_task = asyncio.create_task(
            training_manager.start_training(
                agent_id=agent_id,
                seed=config_data.get('seed', 42),
                max_episodes=config_data.get('max_episodes'),
                callback=send_update,
                config=config_data,
                env_type=config_data.get('env_type', 'standard')
            )
        )
        
        # Listen for control commands
        while True:
            try:
                message = await websocket.receive_json()
                
                if message.get('action') == 'stop':
                    training_manager.stop_training(agent_id)
                    await websocket.send_json({
                        "type": "control_response",
                        "action": "stop",
                        "status": "stopping"
                    })
                    break
                    
            except WebSocketDisconnect:
                # Don't stop training - let it complete
                print(f"   WebSocket disconnected for {agent_id}, but training continues...")
                break
                
    except WebSocketDisconnect:
        # Don't stop training - let it complete  
        print(f"   WebSocket disconnected for {agent_id}, but training continues...")
    finally:
        manager.disconnect(websocket, agent_id)
        
        # Wait for training to complete before saving to ledger
        try:
            print(f"   Waiting for training task to complete for {agent_id}...")
            await training_task
            print(f"   Training task completed for {agent_id}")
        except Exception as e:
            print(f"   Training task error: {e}")
        
        # After training completes, VERIFY then add to ledger if valid
        try:
            session = training_manager.get_session_state(agent_id)
            if session and hasattr(session, 'final_policy_hash') and session.status in ["completed", "stopped"]:
                print(f"Training completed for {agent_id}. Running verification...")
                
                # Load policy for verification
                policy_path = Path("policies") / f"{session.final_policy_hash}.json"
                if not policy_path.exists():
                    print(f"⚠ Policy file not found: {policy_path}")
                else:
                    # Load and parse policy
                    policy = load_policy_from_file(policy_path)
                    
                    # Create policy claim
                    from src.agent.runner import PolicyClaim
                    claim = PolicyClaim(
                        agent_id=agent_id,
                        policy_hash=session.final_policy_hash,
                        claimed_reward=session.final_reward,
                        policy=policy
                    )
                    
                    # VERIFY the policy claim
                    verification_result = verifier.verify(claim)
                    
                    if verification_result.status == VerificationStatus.VALID:
                        # Only add VALID policies to ledger
                        entry = ledger.append(
                            policy_hash=session.final_policy_hash,
                            verified_reward=verification_result.verified_reward,
                            agent_id=agent_id,
                            env_config=session.env_config
                        )
                        print(f"✓ Policy VERIFIED and added to ledger")
                        print(f"  Claimed: {session.final_reward:.3f} | Verified: {verification_result.verified_reward:.3f}")
                        print(f"  Agent: {agent_id} | Environment: {session.env_config.get('display_name', 'Unknown')}")
                    else:
                        # INVALID policy - do NOT add to ledger
                        print(f"✗ Policy INVALID - NOT added to ledger")
                        print(f"  Reason: {verification_result.reason}")
                        print(f"  Claimed: {session.final_reward:.3f} | Verified: {verification_result.verified_reward:.3f}")
            else:
                if session:
                    print(f"Session found but not processing: status={session.status}, has_hash={hasattr(session, 'final_policy_hash')}")
                else:
                    print(f"No session found for agent: {agent_id}")
        except Exception as e:
            print(f"⚠ Warning: Verification/ledger error: {e}")
            import traceback
            traceback.print_exc()


@app.websocket("/ws/execute/{policy_hash}")
async def websocket_execute_endpoint(websocket: WebSocket, policy_hash: str):
    """
    WebSocket endpoint for live policy execution monitoring.
    
    Streams step-by-step decisions in real-time showing:
    - State at each timestep
    - Action taken
    - Reward received
    - System health
    - Decision confidence and entropy
    
    Configuration message format:
    {
        "max_steps": 500,
        "speed_ms": 50,
        "adaptive_pressure": false,
        "partial_observability": false,
        "pressure_rate": 1.0
    }
    
    Features:
    - FEATURE 1: Live decision streaming (Markov decision process visualization)
    - FEATURE 2: Online evaluation mode (no learning, deterministic execution)
    - FEATURE 3: Adaptive environment pressure (escalating difficulty)
    - FEATURE 4: Partial observability toggle (POMDP-like)
    - FEATURE 5: Policy confidence/entropy display (Q-value gaps)
    """
    await websocket.accept()
    
    try:
        # Receive configuration
        config_data = await websocket.receive_json()
        
        print(f"\n[WebSocket] Execution request for policy: {policy_hash}")
        print(f"[WebSocket] Config: max_steps={config_data.get('max_steps')}, adaptive={config_data.get('adaptive_pressure')}, partial_obs={config_data.get('partial_observability')}")
        
        # Load policy
        policy_path = Path("policies") / f"{policy_hash}.json"
        if not policy_path.exists():
            await websocket.send_json({
                "type": "error",
                "message": f"Policy {policy_hash} not found"
            })
            await websocket.close()
            return
        
        # Load and parse policy
        policy = load_policy_from_file(policy_path)
        
        # Create execution config
        exec_config = ExecutionConfig(
            policy_hash=policy_hash,
            max_steps=config_data.get('max_steps', 500),
            speed_ms=config_data.get('speed_ms', 50),
            adaptive_pressure=config_data.get('adaptive_pressure', False),
            partial_observability=config_data.get('partial_observability', False),
            pressure_rate=config_data.get('pressure_rate', 1.0)
        )
        
        # Create environment with varied seed for different executions
        import time
        from src.environments.cyber_env import CyberDefenseEnv
        # Use policy hash + timestamp to ensure different runs have variety
        default_seed = (hash(policy_hash) + int(time.time() * 1000)) % 10000
        env = CyberDefenseEnv(seed=config_data.get('seed', default_seed))
        
        print(f"[WebSocket] Using environment seed: {config_data.get('seed', default_seed)}")
        
        # Create executor
        executor = LivePolicyExecutor(env, policy, exec_config)
        
        # Execute and stream
        await executor.execute_streaming(websocket)
        
    except WebSocketDisconnect:
        print(f"Execution monitoring disconnected for {policy_hash}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


@app.post("/training/start")
async def start_live_training(request: LiveTrainRequest):
    """
    Start a live training session (alternative to WebSocket for simpler clients).
    
    Training will run in the background. Use WebSocket to receive updates.
    """
    try:
        # Check if already training
        existing = training_manager.get_session_state(request.agent_id)
        if existing and existing.status == "running":
            raise HTTPException(
                status_code=400,
                detail=f"Agent {request.agent_id} is already training"
            )
        
        # Start training (no callback, updates go to WebSocket)
        asyncio.create_task(
            training_manager.start_training(
                agent_id=request.agent_id,
                seed=request.seed,
                max_episodes=request.max_episodes,
                callback=lambda data: manager.broadcast(data, request.agent_id),
                config={
                    'epsilon_start': request.epsilon_start,
                    'epsilon_end': request.epsilon_end,
                    'epsilon_decay': request.epsilon_decay
                }
            )
        )
        
        return {
            "status": "started",
            "agent_id": request.agent_id,
            "message": "Training started. Connect via WebSocket for updates."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/training/control")
async def control_training(request: TrainingControlRequest):
    """
    Control a running training session.
    
    Actions: stop, pause, resume
    """
    try:
        if request.action == "stop":
            success = training_manager.stop_training(request.agent_id)
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"No active training session for {request.agent_id}"
                )
            return {"status": "stopped", "agent_id": request.agent_id}
        
        # Add pause/resume logic if needed
        raise HTTPException(status_code=400, detail=f"Action {request.action} not implemented")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/training/sessions")
async def get_training_sessions():
    """Get all active training sessions"""
    return {
        "sessions": training_manager.get_all_sessions(),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/training/session/{agent_id}")
async def get_training_session(agent_id: str):
    """Get state of a specific training session including policy info if completed"""
    state = training_manager.get_session_state(agent_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"No session for {agent_id}")
    
    response = {
        "agent_id": agent_id,
        "status": state.status,
        "episode": state.episode,
        "total_episodes": state.total_episodes,
        "metrics_count": len(state.metrics_history),
        "q_table_size": len(state.q_table)
    }
    
    # Include policy info if training completed
    if hasattr(state, 'final_policy_hash'):
        response["policy_hash"] = state.final_policy_hash
        response["verified_reward"] = state.final_reward
        response["policy_saved"] = True
    
    return response


@app.post("/agent/verify/{agent_id}", response_model=VerifyResponse)
async def verify_agent_endpoint(agent_id: str):
    """
    Verify a trained agent's policy claim.
    
    This endpoint:
    - Checks if policy already exists in ledger (already verified)
    - Verifies the claimed reward is accurate
    - Returns verification status and verified reward
    - Works with both old training_jobs and new training_manager
    """
    try:
        # First check if agent already in ledger (already verified and saved)
        ledger_entries = ledger.read_all()
        for entry in ledger_entries:
            if entry.agent_id == agent_id:
                # Already verified and in ledger
                return VerifyResponse(
                    agent_id=agent_id,
                    verified_reward=entry.verified_reward,
                    status="VALID",
                    reason="Policy already verified and added to ledger"
                )
        
        # Try new training_manager
        session = training_manager.get_session_state(agent_id)
        if session and hasattr(session, 'final_policy_hash'):
            # Create a policy claim from the session
            from src.agent.runner import PolicyClaim
            
            # Load the policy file
            policy_path = Path("policies") / f"{session.final_policy_hash}.json"
            if not policy_path.exists():
                raise HTTPException(status_code=404, detail=f"Policy file not found for {agent_id}")
            
            # Load and parse policy
            policy = load_policy_from_file(policy_path)
            
            claim = PolicyClaim(
                agent_id=agent_id,
                policy_hash=session.final_policy_hash,
                claimed_reward=session.final_reward,
                policy=policy
            )
            
            # Verify claim
            result = verifier.verify(claim)
            
            return VerifyResponse(
                agent_id=claim.agent_id,
                verified_reward=result.verified_reward,
                status=result.status.value,
                reason=result.reason
            )
        
        # Fall back to old training_jobs
        if agent_id not in training_jobs:
            raise HTTPException(
                status_code=404, 
                detail=f"Agent {agent_id} not found. Either training is still in progress, or the agent was never trained."
            )
        
        claim = training_jobs[agent_id]["claim"]
        
        # Verify claim
        result = verifier.verify(claim)
        
        # Store verification result
        training_jobs[agent_id]["verification"] = {
            "verified_reward": result.verified_reward,
            "status": result.status.value,
            "reason": result.reason,
            "timestamp": datetime.now().isoformat()
        }
        
        return VerifyResponse(
            agent_id=claim.agent_id,
            verified_reward=result.verified_reward,
            status=result.status.value,
            reason=result.reason
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ledger/add/{agent_id}")
async def add_to_ledger_endpoint(agent_id: str):
    """
    Add a verified policy to the ledger.
    
    Only verified policies can be added.
    """
    try:
        # Get training job
        if agent_id not in training_jobs:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        job = training_jobs[agent_id]
        
        # Check if verified
        if "verification" not in job:
            raise HTTPException(status_code=400, detail="Policy not verified. Verify first.")
        
        verification = job["verification"]
        if verification["status"] != "VALID":
            raise HTTPException(status_code=400, detail=f"Policy invalid: {verification['reason']}")
        
        claim = job["claim"]
        
        # Add to ledger
        entry = ledger.append(
            policy_hash=claim.policy_hash,
            verified_reward=verification["verified_reward"],
            agent_id=claim.agent_id
        )
        
        return {
            "status": "added",
            "policy_hash": entry.policy_hash,
            "verified_reward": entry.verified_reward,
            "agent_id": entry.agent_id,
            "timestamp": entry.timestamp,
            "current_hash": entry.current_hash
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ledger", response_model=List[LedgerEntryResponse])
async def get_ledger():
    """Get all ledger entries"""
    try:
        entries = ledger.read_all()
        
        return [
            LedgerEntryResponse(
                policy_hash=entry.policy_hash,
                verified_reward=entry.verified_reward,
                agent_id=entry.agent_id,
                timestamp=entry.timestamp,
                previous_hash=entry.previous_hash,
                current_hash=entry.current_hash
            )
            for entry in entries
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ledger/integrity")
async def check_ledger_integrity():
    """Verify ledger chain integrity"""
    try:
        entries = ledger.read_all()
        is_intact, error = verify_chain_integrity(entries)
        
        return {
            "is_valid": is_intact,
            "error": error,
            "total_entries": len(entries),
            "verified_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/marketplace", response_model=List[MarketplacePolicy])
async def get_marketplace():
    """Get ranked policies from marketplace"""
    try:
        marketplace = PolicyMarketplace(ledger)
        ranked = marketplace.get_ranked_policies()
        
        # Get full ledger entries to access timestamps
        entries = ledger.read_all()
        entry_map = {e.policy_hash: e for e in entries}
        
        return [
            MarketplacePolicy(
                agent_id=policy.agent_id,
                policy_hash=policy.policy_hash,
                verified_reward=policy.verified_reward,
                timestamp=entry_map[policy.policy_hash].timestamp,
                rank=i + 1
            )
            for i, policy in enumerate(ranked)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/marketplace/best")
async def get_best_policy():
    """Get the best policy from marketplace"""
    try:
        best = select_best_policy(ledger)
        
        if not best:
            raise HTTPException(status_code=404, detail="No policies in marketplace")
        
        # Get the full ledger entry to access timestamp
        entries = ledger.read_all()
        best_entry = next((e for e in entries if e.policy_hash == best.policy_hash), None)
        
        if not best_entry:
            raise HTTPException(status_code=404, detail="Policy not found in ledger")
        
        return {
            "agent_id": best.agent_id,
            "policy_hash": best.policy_hash,
            "verified_reward": best.verified_reward,
            "timestamp": best_entry.timestamp
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENVIRONMENT CONFIGURATION ENDPOINTS
# =============================================================================

@app.get("/environments")
async def get_environments():
    """Get all available environment types"""
    from src.environments.env_presets import list_env_types
    return {"environments": list_env_types()}


@app.get("/marketplace/by-environment")
async def get_marketplace_by_environment(env_type: Optional[str] = None):
    """
    Get marketplace policies grouped by environment type.
    
    Query params:
        env_type: Filter by specific environment type (optional)
    """
    try:
        marketplace = PolicyMarketplace(ledger)
        all_policies = marketplace.rank_policies()
        
        if not all_policies:
            return {"policies_by_environment": {}}
        
        # Group policies by environment type
        by_env = {}
        for policy in all_policies:
            # Get full entry to access env_config
            entries = ledger.read_all()
            entry = next((e for e in entries if e.policy_hash == policy.policy_hash), None)
            
            if entry and entry.env_config:
                policy_env_type = entry.env_config.get('env_type', 'unknown')
            else:
                policy_env_type = 'unknown'  # Legacy policies without env_config
            
            # Filter by env_type if specified
            if env_type and policy_env_type != env_type:
                continue
            
            if policy_env_type not in by_env:
                by_env[policy_env_type] = []
            
            by_env[policy_env_type].append({
                "rank": len(by_env[policy_env_type]) + 1,  # Rank within environment
                "agent_id": policy.agent_id,
                "policy_hash": policy.policy_hash,
                "verified_reward": policy.verified_reward,
                "timestamp": entry.timestamp if entry else None,
                "env_config": entry.env_config if entry and entry.env_config else None
            })
        
        return {"policies_by_environment": by_env}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/consumer/reuse", response_model=ReuseResponse)
async def reuse_policy_endpoint(seed: int = 9999):
    """
    Reuse the best policy from marketplace.
    
    This demonstrates zero-training policy reuse.
    """
    try:
        import math
        
        best = select_best_policy(ledger)
        
        if not best:
            raise HTTPException(status_code=404, detail="No policies available for reuse")
        
        # Reuse best policy
        result = reuse_best_policy(best, seed=seed)
        
        # Ensure all float values are JSON compliant
        def make_json_safe(value: float) -> float:
            if math.isnan(value) or math.isinf(value):
                return 0.0
            return value
        
        return {
            "agent_id": result["agent_id"],
            "policy_hash": result["policy_hash"],
            "verified_reward": make_json_safe(result["verified_reward"]),
            "reused_reward": make_json_safe(result["policy_reward"]),
            "baseline_reward": make_json_safe(result["baseline_reward"]),
            "improvement": make_json_safe(result["improvement"])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=SystemStats)
async def get_system_stats():
    """Get overall system statistics"""
    try:
        entries = ledger.read_all()
        is_intact, _ = verify_chain_integrity(entries)
        
        best = select_best_policy(ledger)
        best_reward = best.verified_reward if best else None
        
        # Ensure best_reward is JSON compliant (not NaN or Inf)
        if best_reward is not None:
            import math
            if math.isnan(best_reward) or math.isinf(best_reward):
                best_reward = None
        
        # Count unique agents
        unique_agents = len(set(entry.agent_id for entry in entries))
        
        # Count verified policies
        verified_count = len([job for job in training_jobs.values() 
                             if "verification" in job and job["verification"]["status"] == "VALID"])
        
        return SystemStats(
            total_agents=unique_agents,
            total_policies=len(training_jobs),
            verified_policies=verified_count,
            ledger_entries=len(entries),
            chain_integrity=is_intact,
            best_policy_reward=best_reward
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/explainability/best")
async def get_best_policy_explanation():
    """Get explanation for the best policy"""
    try:
        best = select_best_policy(ledger)
        
        if not best:
            raise HTTPException(status_code=404, detail="No policies available")
        
        # Redirect to the specific agent explanation
        return await get_policy_explanation(best.agent_id)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/explainability/{agent_id}")
async def get_policy_explanation(agent_id: str):
    """Get AI-powered explanation of policy behavior using Gemini"""
    try:
        # Find the ledger entry for this agent
        entries = ledger.read_all()
        entry = next((e for e in entries if e.agent_id == agent_id), None)
        
        if not entry:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Find rank
        marketplace = PolicyMarketplace(ledger)
        ranked = marketplace.get_ranked_policies()
        rank = next((i + 1 for i, p in enumerate(ranked) if p.agent_id == agent_id), None)
        
        # Load policy to analyze behavior patterns
        policy_path = Path("policies") / f"{entry.policy_hash}.json"
        if policy_path.exists():
            with open(policy_path) as f:
                policy_data = json.load(f)
                policy = policy_data.get("policy", {})
        else:
            policy = {}
        
        # Analyze action distribution
        if policy:
            action_counts = {}
            for action in policy.values():
                action_counts[action] = action_counts.get(action, 0) + 1
            total_states = len(policy)
            behavior_stats = {
                "ignore_percentage": action_counts.get(0, 0) / total_states if total_states > 0 else 0,
                "monitor_percentage": action_counts.get(1, 0) / total_states if total_states > 0 else 0,
                "rate_limit_percentage": action_counts.get(2, 0) / total_states if total_states > 0 else 0,
                "block_ip_percentage": action_counts.get(3, 0) / total_states if total_states > 0 else 0,
                "isolate_percentage": action_counts.get(4, 0) / total_states if total_states > 0 else 0,
                "total_states_covered": total_states,
            }
        else:
            behavior_stats = {}
        
        # Calculate baseline for comparison
        avg_reward = sum(e.verified_reward for e in entries) / len(entries) if entries else 0
        
        # Create explanation metrics (NamedTuple - use positional args in correct order)
        metrics = ExplanationMetrics(
            environment_name="Cyber Defense Environment",
            policy_identifier=entry.policy_hash,
            verified_reward=entry.verified_reward,
            baseline_reward=avg_reward,
            behavior_stats=behavior_stats
        )
        
        # Generate AI explanation using Gemini
        ai_explanation = explainer.explain(metrics)
        
        # Build response with both AI and structured insights
        response = {
            "agent_id": agent_id,
            "policy_hash": entry.policy_hash,
            "verified_reward": entry.verified_reward,
            "rank": rank,
            "total_policies": len(entries),
            "summary": ai_explanation,
            "behavior_stats": behavior_stats,
            "patterns": [
                {
                    "title": "Defensive Strategy",
                    "description": f"Ignores: {behavior_stats.get('ignore_percentage', 0)*100:.1f}%, Monitors: {behavior_stats.get('monitor_percentage', 0)*100:.1f}%, Rate Limits: {behavior_stats.get('rate_limit_percentage', 0)*100:.1f}%"
                } if behavior_stats else None,
                {
                    "title": "Aggressive Actions",
                    "description": f"Blocks IPs: {behavior_stats.get('block_ip_percentage', 0)*100:.1f}%, Isolates Services: {behavior_stats.get('isolate_percentage', 0)*100:.1f}%"
                } if behavior_stats else None,
                {
                    "title": "State Space Coverage",
                    "description": f"Learned {behavior_stats.get('total_states_covered', 0)} out of 108 possible states ({behavior_stats.get('total_states_covered', 0)/108*100:.1f}% coverage)"
                } if behavior_stats else None,
            ],
            "improvement_suggestions": [
                "Train for more episodes to cover more state space" if behavior_stats.get('total_states_covered', 0) < 50 else None,
                "Consider more aggressive actions for high-severity attacks" if behavior_stats.get('ignore_percentage', 0) > 0.3 else None,
                "Balance defensive and aggressive strategies" if behavior_stats else None,
            ]
        }
        
        # Filter out None values
        response["patterns"] = [p for p in response["patterns"] if p]
        response["improvement_suggestions"] = [s for s in response["improvement_suggestions"] if s]
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/reset")
async def reset_system():
    """Reset the entire system (for demo purposes)"""
    try:
        global training_jobs, ledger
        
        # Clear training jobs
        training_jobs.clear()
        
        # Reset ledger
        ledger = PolicyLedger(LEDGER_FILE)
        
        # Clear ledger file
        if Path(LEDGER_FILE).exists():
            Path(LEDGER_FILE).unlink()
        
        ledger = PolicyLedger(LEDGER_FILE)
        
        return {
            "status": "reset",
            "message": "System reset successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Live Execution Endpoints
# ============================================================================

class ExecutionRequest(BaseModel):
    """Request to execute a policy"""
    policy_hash: str
    max_steps: int = 500
    seed: int = 9999
    adaptive_pressure: bool = False
    partial_observability: bool = False
    pressure_rate: float = 1.0


class ExecutionSummary(BaseModel):
    """Summary of policy execution"""
    policy_hash: str
    total_steps: int
    final_reward: float
    avg_confidence: float
    avg_entropy: float
    execution_time: float
    adaptive_pressure: bool
    partial_observability: bool


@app.post("/execution/run", response_model=ExecutionSummary)
async def execute_policy_batch(request: ExecutionRequest):
    """
    Execute a policy in batch mode (returns all steps at once).
    
    This is useful for:
    - Offline analysis
    - Generating replay data
    - Testing policy behavior
    
    For real-time streaming, use WebSocket endpoint: /ws/execute/{policy_hash}
    """
    try:
        # Load policy
        policy_path = Path("policies") / f"{request.policy_hash}.json"
        if not policy_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Policy {request.policy_hash} not found"
            )
        
        # Load and parse policy
        policy = load_policy_from_file(policy_path)
        
        # Create execution config
        exec_config = ExecutionConfig(
            policy_hash=request.policy_hash,
            max_steps=request.max_steps,
            speed_ms=0,  # No delay for batch
            adaptive_pressure=request.adaptive_pressure,
            partial_observability=request.partial_observability,
            pressure_rate=request.pressure_rate
        )
        
        # Create environment
        from src.environments.cyber_env import CyberDefenseEnv
        env = CyberDefenseEnv(seed=request.seed)
        
        # Create executor and run
        executor = LivePolicyExecutor(env, policy, exec_config)
        steps = executor.execute_batch()
        
        # Calculate summary
        import numpy as np
        summary = ExecutionSummary(
            policy_hash=request.policy_hash,
            total_steps=len(steps),
            final_reward=steps[-1].cumulative_reward if steps else 0.0,
            avg_confidence=float(np.mean([s.confidence for s in steps])) if steps else 0.0,
            avg_entropy=float(np.mean([s.entropy for s in steps])) if steps else 0.0,
            execution_time=steps[-1].time_elapsed if steps else 0.0,
            adaptive_pressure=request.adaptive_pressure,
            partial_observability=request.partial_observability
        )
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/execution/features")
async def get_execution_features():
    """
    Get available execution features and their descriptions.
    
    Documents the 5 key features for live policy monitoring.
    """
    return {
        "features": [
            {
                "id": "streaming_decisions",
                "name": "Live Policy Execution Monitor",
                "description": "Stream step-by-step decisions showing state, action, reward, and system health",
                "rl_concept": "Markov Decision Process visualization",
                "endpoint": "/ws/execute/{policy_hash}",
                "type": "websocket"
            },
            {
                "id": "online_evaluation",
                "name": "Online Evaluation Mode",
                "description": "Fixed policy execution with no learning, deterministic and replayable",
                "rl_concept": "Policy deployment simulation",
                "note": "This is evaluation-only, not training",
                "endpoint": "/execution/run",
                "type": "rest"
            },
            {
                "id": "adaptive_pressure",
                "name": "Adaptive Environment Pressure",
                "description": "Environment difficulty escalates over time - attacks last longer, penalties increase",
                "rl_concept": "Tests policy robustness and generalization",
                "parameter": "adaptive_pressure=true",
                "deterministic": True
            },
            {
                "id": "partial_observability",
                "name": "Partial Observability Toggle",
                "description": "Agent sees limited state (POMDP-like), verification sees full state",
                "rl_concept": "Partially Observable MDP execution",
                "parameter": "partial_observability=true",
                "advanced": True
            },
            {
                "id": "confidence_entropy",
                "name": "Policy Confidence & Entropy Display",
                "description": "Shows Q-value gaps (confidence) and decision entropy for each step",
                "rl_concept": "RL internal state visualization",
                "metrics": ["confidence", "entropy"],
                "confidence_meaning": "Gap between best and second-best action (0-1)",
                "entropy_meaning": "Decision uncertainty via Shannon entropy (0-1)"
            }
        ],
        "usage": {
            "streaming": "Connect to WebSocket /ws/execute/{policy_hash} with config",
            "batch": "POST to /execution/run with ExecutionRequest",
            "config_example": {
                "max_steps": 500,
                "speed_ms": 50,
                "adaptive_pressure": False,
                "partial_observability": False,
                "pressure_rate": 1.0,
                "seed": 9999
            }
        }
    }


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("=" * 80)
    print("🚀 PolicyLedger API Starting")
    print("=" * 80)
    print(f"Ledger file: {LEDGER_FILE}")
    print(f"Ledger entries: {len(ledger.read_all())}")
    print("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("PolicyLedger API shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
