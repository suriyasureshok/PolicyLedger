# ✅ MASTER CHECKLIST — **PolicyLedger**

*A Google Cloud–native, fallback-safe RL Policy Marketplace*

---

# 🏗️ ARCHITECTURE OVERVIEW
![Architecture Diagram](assets/architecture_diagram.png)

---

## 🧩 PHASE 1 — IDEA & SCOPE FREEZE (NON-NEGOTIABLE)

* [ ] One-sentence **problem statement** frozen
* [ ] One-sentence **solution statement** frozen
* [ ] Demo environment fixed: **Energy Scheduling**
* [ ] RL type fixed: **Tabular Q-learning**
* [ ] Edge hardware fixed: **Old phones / laptop**
* [ ] Ledger definition fixed: **Tamper-evident append-only ledger**
* [ ] Google-first + fallback strategy approved
* [ ] No feature additions after this phase

☠️ If this moves, everything breaks later.

---

## 🧩 PHASE 2 — REPOSITORY, MODULARITY & HYGIENE

### Repo & standards

* [ ] Single Git repository
* [ ] Project name: **PolicyLedger**
* [ ] README with:

  * Problem (2 lines)
  * Architecture summary
  * Google services used
* [ ] Python version fixed (3.10+)
* [ ] Virtual environment created
* [ ] `requirements.txt` split into:

  * `requirements-cloud.txt`
  * `requirements-local.txt`

### Folder structure (STRICT)

* [ ] `agent/`
* [ ] `verifier/`
* [ ] `ledger/`
* [ ] `marketplace/`
* [ ] `consumer/`
* [ ] `explainability/`
* [ ] `shared/`

🧱 Each folder exposes **interfaces**, not concrete logic.

---

## 🧩 PHASE 3 — ENVIRONMENT (SHARED, DETERMINISTIC)

### Environment design

* [ ] Environment name: `EnergySlotEnv`
* [ ] Discrete time steps fixed (e.g., 24)
* [ ] Battery capacity normalized (0–1)
* [ ] Demand schedule deterministic + seeded
* [ ] Reward function written **before coding**

### Code checklist (`shared/env.py`)

* [ ] `reset()` implemented
* [ ] `step(action)` implemented
* [ ] Battery update logic deterministic
* [ ] Demand logic reproducible
* [ ] Reward calculation deterministic
* [ ] Terminal condition defined
* [ ] Same seed → same trajectory

🚫 No randomness without seed
🚫 Environment logic NEVER inside agent or verifier

---

## 🧩 PHASE 4 — RL AGENT (EDGE LEARNING NODE)

### RL design

* [ ] State space discretized
* [ ] Action space = `{SAVE, USE}`
* [ ] Learning rate fixed
* [ ] Discount factor fixed
* [ ] Exploration strategy defined

### Google-first

* [ ] Q-learning implemented using **TensorFlow**
* [ ] Policy exported as **TensorFlow Lite**

### Fallback

* [ ] Pure Python Q-table
* [ ] Policy stored as JSON

### Code checklist

* [ ] Q-table initialized
* [ ] Epsilon-greedy selection
* [ ] Q-update formula correct
* [ ] Episode loop implemented
* [ ] Cumulative reward tracked
* [ ] Average reward computed
* [ ] Training reproducible with seed

### Policy artifact

* [ ] Policy serialized
* [ ] Policy hash generated (SHA-256)
* [ ] Policy metadata stored (agent_id, env_id)

🚫 No deep RL
🚫 No libraries you can’t explain to judges

---

## 🧩 PHASE 5 — MULTI-AGENT DECENTRALIZATION

* [ ] Agent A trains independently
* [ ] Agent B trains independently
* [ ] Same environment definition used
* [ ] Different learned policies produced
* [ ] Different rewards observed
* [ ] Unique agent IDs enforced

🧠 This is your **proof of decentralization**.

---

## 🧩 PHASE 6 — SUBMISSION LAYER (NO TRUST)

### Google-first

* [ ] Firebase REST API endpoint

### Fallback

* [ ] Local submission queue (JSON / in-memory)

### Submission payload schema

* [ ] `agent_id`
* [ ] `policy_hash`
* [ ] `policy_artifact`
* [ ] `claimed_reward`
* [ ] `environment_id`

🚫 Agents NEVER talk to verifier directly
🚫 No peer-to-peer trust

---

## 🧩 PHASE 7 — VERIFICATION LAYER (CORE NOVELTY)

### Google-first

* [ ] **Vertex AI Custom Job**
* [ ] Deterministic replay using shared env
* [ ] Reward recomputation

### Fallback

* [ ] Local verifier script
* [ ] Same replay logic

### Verification logic

* [ ] Policy loaded correctly
* [ ] Replay produces reward
* [ ] Reward mismatch threshold defined
* [ ] Invalid claims rejected
* [ ] Valid claims approved

### Edge cases

* [ ] Inflated reward rejected
* [ ] Policy hash mismatch detected
* [ ] Deterministic replay confirmed

🔥 This is the heart of the project.

---

## 🧩 PHASE 8 — POLICY LEDGER (GOOGLE-NATIVE BLOCKCHAIN)

### Google-first

* [ ] Firestore append-only collection
* [ ] Each entry stores:

  * `policy_hash`
  * `verified_reward`
  * `agent_id`
  * `timestamp`
  * `previous_hash`
* [ ] Firestore rules enforce immutability

### Fallback

* [ ] Local append-only JSON ledger
* [ ] Hash-chained entries

🚫 No wallets
🚫 No tokens
🚫 No crypto buzzwords

---

## 🧩 PHASE 9 — MARKETPLACE (EVENT-DRIVEN)

### Google-first

* [ ] Cloud Function triggered on new ledger entry
* [ ] Policies ranked by verified reward
* [ ] Best policy reference updated

### Fallback

* [ ] Local ranking script

### Logic

* [ ] Tie-breaking rule defined
* [ ] Ranking output visible

🧠 This is where “marketplace” becomes real.

---

## 🧩 PHASE 10 — POLICY REUSE (THE WOW MOMENT)

### Google-first

* [ ] Best policy fetched via Firebase
* [ ] Policy loaded via TFLite runtime

### Fallback

* [ ] Local policy fetch
* [ ] JSON runner

### Demo proof

* [ ] No retraining
* [ ] Environment run immediately
* [ ] Performance logged
* [ ] Compared against random policy

🔥 Judges remember this.

---

## 🧩 PHASE 11 — EXPLAINABILITY (OPTIONAL BUT POWERFUL)

### Google-first

* [ ] Gemini API generates explanation:

  * Why policy won
  * What strategy it used

### Fallback

* [ ] Template-based explanation

🧠 Makes RL human-understandable.

---

## 🧩 PHASE 12 — HARDWARE DEMO (MINIMAL)

* [ ] Old phone runs agent OR consumer
* [ ] Laptop runs verifier / marketplace
* [ ] Network communication works
* [ ] Logs visible live
* [ ] Hardware role explained clearly

🚫 Motors
🚫 Sensors
🚫 Overkill electronics

---

## 🧩 PHASE 13 — LOGGING & VISIBILITY

* [ ] Clear logs at every stage
* [ ] Rewards printed clearly
* [ ] Verification decision visible
* [ ] Ledger entries visible
* [ ] Ranking output visible
* [ ] Policy reuse metrics visible

Judges read **outputs**, not code.

---

## 🧩 PHASE 14 — STORY, PITCH & IEEE PATH

* [ ] 30-second problem explanation
* [ ] 60-second architecture explanation
* [ ] Verifier explained clearly
* [ ] Google services justified
* [ ] Demo rehearsed twice
* [ ] IEEE extension mentioned (verification + reuse)

🚫 No buzzword salad
🚫 No overclaiming

---

## 🧩 PHASE 15 — FINAL SANITY CHECK

* [ ] Works fully offline (fallback)
* [ ] Works fully cloud-native (Google)
* [ ] Fresh machine run tested
* [ ] Repo clean & documented
* [ ] One teammate can explain end-to-end

If one person can’t explain it all, judges won’t either.

---

## 🧠 FINAL LINE (REMEMBER THIS)

> **“PolicyLedger learns at the edge, verifies in the cloud, remembers immutably, and reuses intelligence.”**