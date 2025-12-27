# PolicyLedger

*A Google Cloud–native, fallback-safe RL Policy Marketplace*

![Architecture Diagram](assets/architecture_diagram.png)

---

## 📌 Problem

Reinforcement learning agents train at the edge but lack trust in policy submissions. Verifying policies without retraining is computationally expensive, and no marketplace exists for RL policies due to the inability to verify claimed rewards.

## 🚀 Solution

PolicyLedger learns at the edge, verifies in the cloud, remembers immutably, and reuses intelligence. Decentralized RL agents submit policies to a marketplace where they are verified through deterministic replay, stored in a tamper-evident ledger, and made available for reuse by consumers.

---

## 🏗️ Architecture Summary

**PolicyLedger** operates through a multi-stage pipeline:

1. **Edge Learning**: RL agents (running on edge devices like old phones/laptops) train independently using tabular Q-learning in a shared deterministic environment (`EnergySlotEnv`).

2. **Policy Submission**: Agents submit trained policies with claimed rewards to a submission layer (Firebase REST API or local queue).

3. **Cloud Verification**: Vertex AI custom jobs verify policies by deterministically replaying them in the same environment and recomputing rewards. Invalid claims are rejected.

4. **Immutable Ledger**: Verified policies are stored in a Firestore append-only collection (hash-chained entries) forming a tamper-evident ledger.

5. **Marketplace Ranking**: Cloud Functions trigger on new ledger entries and rank policies by verified reward, updating the best policy reference.

6. **Policy Reuse**: Consumers fetch the best policy from the marketplace and run it immediately without retraining, demonstrating intelligent reuse.

7. **Explainability** (optional): Gemini API generates human-readable explanations of why winning policies work.

---

## ☁️ Google Services Used

- **Firebase/Firestore**: Policy submission endpoints and append-only ledger with immutability rules
- **Vertex AI**: Custom jobs for deterministic policy verification and reward recomputation
- **Cloud Functions**: Event-driven marketplace updates triggered by new ledger entries
- **TensorFlow/TensorFlow Lite**: Agent training and policy export for edge deployment
- **Gemini API**: AI-generated explanations of policy strategies (optional)

**Fallback Strategy**: Every Google service has a local Python/JSON fallback to ensure the system works fully offline.

---

## 🧩 Project Structure

```
PolicyLedger/
├── agent/              # Edge RL training logic
├── verifier/           # Deterministic policy verification
├── ledger/             # Append-only policy storage
├── marketplace/        # Policy ranking and discovery
├── consumer/           # Policy reuse without retraining
├── explainability/     # AI-generated policy explanations
├── shared/             # Shared environment definition
├── requirements-cloud.txt
├── requirements-local.txt
└── README.md
```

Each module exposes **interfaces**, not concrete logic, ensuring modularity.

---

## 🎯 Demo Environment

**EnergySlotEnv**: A deterministic energy scheduling environment where agents manage battery charge/discharge over 24 discrete time steps. The environment uses seeded randomness to ensure reproducibility — same seed produces identical trajectories.

**RL Type**: Tabular Q-learning with discrete state/action spaces  
**Actions**: `{SAVE, USE}` (save energy to battery or use from battery)  
**Reward**: Based on efficient energy utilization given deterministic demand patterns

---

## 🛠️ Requirements

- **Python**: 3.10+
- **Google Cloud Account** (optional, for cloud features)
- **Edge Hardware**: Old phone or laptop for agent demonstration

Install dependencies:
```bash
# For cloud-native mode
pip install -r requirements-cloud.txt

# For local fallback mode
pip install -r requirements-local.txt
```

---

## 🚦 Quick Start

### 1. Train an Agent (Edge)
```bash
python agent/train.py --agent-id agent_A --episodes 1000
```

### 2. Submit Policy
```bash
python agent/submit.py --agent-id agent_A --policy output/policy_A.pkl
```

### 3. Verify Policy (Cloud/Local)
```bash
python verifier/verify.py --policy-hash <hash>
```

### 4. Query Marketplace
```bash
python marketplace/query.py --top 5
```

### 5. Reuse Best Policy (Consumer)
```bash
python consumer/run.py --policy-id <best_policy_hash>
```

---

## 🔥 Key Features

- **Decentralized Learning**: Multiple agents train independently at the edge
- **Trustless Verification**: Policies verified through deterministic replay, not blind trust
- **Tamper-Evident Ledger**: Hash-chained append-only storage (blockchain-inspired, no crypto)
- **Intelligent Reuse**: Consumers use proven policies without retraining
- **Google-Native + Fallback**: Works fully cloud-native or completely offline
- **Explainability**: AI-generated insights into why policies succeed

---

## 📊 Phases Overview

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | Idea & Scope Freeze | ✅ |
| Phase 2 | Repository & Modularity | 🔄 In Progress |
| Phase 3 | Shared Environment | ⏳ Pending |
| Phase 4 | RL Agent Training | ⏳ Pending |
| Phase 5 | Multi-Agent Decentralization | ⏳ Pending |
| Phase 6 | Submission Layer | ⏳ Pending |
| Phase 7 | Verification Layer | ⏳ Pending |
| Phase 8 | Policy Ledger | ⏳ Pending |
| Phase 9 | Marketplace | ⏳ Pending |
| Phase 10 | Policy Reuse | ⏳ Pending |
| Phase 11 | Explainability | ⏳ Pending |
| Phase 12 | Hardware Demo | ⏳ Pending |
| Phase 13 | Logging & Visibility | ⏳ Pending |
| Phase 14 | Story & Pitch | ⏳ Pending |
| Phase 15 | Final Sanity Check | ⏳ Pending |

See [checklist.md](checklist.md) for detailed phase requirements.

---

## 🧠 Core Innovation

> **"PolicyLedger learns at the edge, verifies in the cloud, remembers immutably, and reuses intelligence."**

This project demonstrates how reinforcement learning can scale through **trustless verification** and **intelligent reuse**, enabling a marketplace where agents contribute and consumers benefit from proven policies.

---

## 🎓 IEEE Extension Path

The verification mechanism and policy reuse framework provide strong foundations for academic publication, focusing on:
- Deterministic verification of RL policies without retraining
- Decentralized marketplace architecture for AI model sharing
- Tamper-evident ledgers for ML policy tracking

---

## 📝 License

See [LICENSE](LICENSE) for details.

---