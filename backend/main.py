"""
PolicyLedger Backend API

FastAPI server that provides REST endpoints for:
- Agent training
- Policy verification
- Ledger management
- Marketplace operations
- Policy reuse

This bridges the PolicyLedger core with the frontend dashboard.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import time
from datetime import datetime
from pathlib import Path

from src.agent.runner import run_agent, PolicyClaim
from src.verifier.verifier import PolicyVerifier
from src.ledger.ledger import PolicyLedger, verify_chain_integrity
from src.marketplace.ranking import select_best_policy, PolicyMarketplace
from src.consumer.reuse import reuse_best_policy

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

# Training state
training_jobs = {}


# ============================================================================
# Pydantic Models
# ============================================================================

class AgentTrainRequest(BaseModel):
    agent_id: str
    seed: int = 42
    episodes: int = 150


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


@app.post("/agent/verify/{agent_id}", response_model=VerifyResponse)
async def verify_agent_endpoint(agent_id: str):
    """
    Verify a trained agent's policy claim.
    
    This endpoint:
    - Verifies the claimed reward is accurate
    - Returns verification status and verified reward
    - Does NOT add to ledger (separate step)
    """
    try:
        # Get claim from training jobs
        if agent_id not in training_jobs:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found. Train first.")
        
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
    """Get human-readable explanation of policy behavior"""
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
        
        # Generate explanation based on reward performance
        reward = entry.verified_reward
        avg_reward = sum(e.verified_reward for e in entries) / len(entries) if entries else 0
        
        performance_category = "high" if reward > avg_reward * 1.2 else "moderate" if reward > avg_reward * 0.8 else "baseline"
        
        explanations = {
            "high": {
                "summary": f"This policy achieved exceptional performance with a verified reward of {reward:.2f}, significantly outperforming the average.",
                "patterns": [
                    {"title": "Optimal Resource Allocation", "description": f"The policy efficiently allocates resources during peak demand periods, achieving {((reward / avg_reward - 1) * 100):.1f}% better performance than average."},
                    {"title": "Strategic Reserve Management", "description": "Maintains adequate reserves while maximizing utilization during high-value time windows."},
                    {"title": "Rapid Adaptation", "description": "Demonstrates quick recovery and rebalancing after demand spikes, minimizing opportunity costs."}
                ]
            },
            "moderate": {
                "summary": f"This policy demonstrates consistent performance with a verified reward of {reward:.2f}, performing at near-average levels.",
                "patterns": [
                    {"title": "Steady State Operation", "description": "Maintains reliable baseline performance across varied conditions."},
                    {"title": "Conservative Strategy", "description": "Prioritizes stability over maximum reward, suitable for risk-averse deployments."},
                    {"title": "Predictable Behavior", "description": "Exhibits consistent decision patterns that are easy to monitor and validate."}
                ]
            },
            "baseline": {
                "summary": f"This policy shows baseline performance with a verified reward of {reward:.2f}, indicating room for optimization.",
                "patterns": [
                    {"title": "Exploratory Behavior", "description": "May benefit from additional training to discover better strategies."},
                    {"title": "Suboptimal Timing", "description": "Resource allocation timing could be improved for better reward capture."},
                    {"title": "Learning Opportunity", "description": "This policy provides valuable baseline data for training improved variants."}
                ]
            }
        }
        
        explanation = explanations[performance_category]
        
        return {
            "agent_id": agent_id,
            "policy_hash": entry.policy_hash,
            "verified_reward": reward,
            "rank": rank,
            "performance_category": performance_category,
            "summary": explanation["summary"],
            "behavioral_patterns": explanation["patterns"],
            "timestamp": entry.timestamp,
            "disclaimer": "This explanation is generated for human understanding and does not influence verification or ranking."
        }
        
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
