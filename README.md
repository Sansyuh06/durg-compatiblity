# 🧬 Drug Adverse Event Triage — OpenEnv

> **A real-world pharmacovigilance RL environment for the Meta × HuggingFace OpenEnv Hackathon 2026**

[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compliant-00c9a7?style=flat-square)](https://github.com/huggingface/openenv)
[![HF Spaces](https://img.shields.io/badge/🤗-HuggingFace%20Space-blue?style=flat-square)](https://huggingface.co/spaces)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)](./Dockerfile)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python)](https://python.org)

---

## 🌍 What Is This?

**Drug-Triage-Env** simulates the real-world task of **pharmacovigilance signal triage** — the process pharmaceutical regulatory agencies (FDA, EMA) use to detect and act on serious adverse drug event signals from post-marketing surveillance data.

Every year, the FDA's **FAERS (FDA Adverse Event Reporting System)** receives millions of reports of suspected adverse reactions. Human signal analysts query FAERS, compute disproportionality statistics (PRR, ROR), review drug labels, cross-check published literature, and then recommend regulatory actions ranging from label updates to global market withdrawal.

This environment teaches AI agents to do exactly that — across three real historical drug cases with documented, verified outcomes.

---

## 🏥 Why This Domain?

| Criterion | Assessment |
|---|---|
| **Real-world task** | ✅ FDA signal analysts run this exact workflow daily |
| **Verifiable outcomes** | ✅ Historical regulatory decisions are public record |
| **Partial reward signal** | ✅ Rich information at every step (FAERS → signal → mechanism → literature) |
| **Multi-difficulty progression** | ✅ Easy (clear signal) → Medium (RCT-confirmed) → Hard (dual-signal complex) |
| **Training value** | ✅ Trains evidence synthesis, causal reasoning, regulatory understanding |

---

## 🧪 Tasks

### 🟢 Easy — Metformin: Lactic Acidosis Signal
- **Drug**: Metformin (Glucophage) — biguanide antidiabetic, ~90M US prescriptions/year
- **Signal**: Lactic acidosis (PRR 4.7, ROR 5.1 — STRONG)
- **Ground truth**: `{"drug_name": "metformin", "primary_signal": "lactic acidosis", "regulatory_action": "monitor"}`
- **Expected score**: 0.70–0.99
- **Why it's easy**: Single prominent signal in FAERS; signal is well-characterized in the label's Black Box Warning; regulatory precedent is clear

### 🟡 Medium — Rofecoxib (Vioxx): Cardiovascular Crisis
- **Drug**: Rofecoxib (Vioxx) — COX-2 selective NSAID, withdrawn globally October 2004
- **Signal**: Myocardial infarction (PRR 8.9, ROR 9.7 — CRITICAL; APPROVE trial RR 1.92x)
- **Ground truth**: `{"drug_name": "rofecoxib", "primary_signal": "myocardial infarction", "regulatory_action": "withdraw"}`
- **Expected score**: 0.60–0.95
- **Why it's medium**: Critical signal requires `analyze_signal` tool; correct action is `withdraw` not `monitor`; distinguishing from class-effect context requires literature review

### 🔴 Hard — Isotretinoin (Accutane): Multi-Signal Triage
- **Drug**: Isotretinoin — severe acne retinoid with iPLEDGE REMS since 2006
- **Signals**: Teratogenicity (PRR 47.3 — CRITICAL) + Depression (PRR 6.8 — STRONG)
- **Ground truth**: `{"drug_name": "isotretinoin", "primary_signal": "teratogenicity", "secondary_signal": "depression", "regulatory_action": "restrict"}`
- **Expected score**: 0.50–0.90
- **Why it's hard**: Two concurrent signals; complex reasoning needed (why REMS restriction, not withdrawal); secondary signal identification; all 5 investigation tools rewarded

---

## 🔧 Action Space

| Action | Description | When to Use |
|---|---|---|
| `search_faers` | Query FDA FAERS for adverse event reports, counts, and top signals | Always start here |
| `fetch_label` | Get official FDA drug labeling, Black Box Warnings, REMS status | Check current regulatory status |
| `analyze_signal` | Run PRR/ROR/IC disproportionality analysis on FAERS data | Quantify signal strength |
| `lookup_mechanism` | Retrieve pharmacological mechanism of action | Understand biological plausibility |
| `check_literature` | Search key safety studies and regulatory precedents | Find confirmatory evidence |
| `submit` | Submit final: `drug_name`, `primary_signal`, `regulatory_action` (+ `secondary_signal` for hard) | When ready to make recommendation |

---

## 👁️ Observation Space

```json
{
  "drug_name": "METFORMIN",
  "step_number": 1,
  "action_history": ["search_faers"],
  "current_output": {
    "source": "FDA FAERS",
    "data": { "total_reports": 12847, "top_adverse_events": [...] },
    "hint": "Review the top_adverse_events list carefully..."
  },
  "available_actions": ["search_faers", "fetch_label", "analyze_signal", "lookup_mechanism", "check_literature", "submit"],
  "episode_done": false
}
```

---

## 🏆 Reward Function

Non-submit steps return `+0.05` (success) or `+0.01` (error) — providing dense step-level signal.

Submit steps are graded by task-specific rubrics:

| Task | `drug_name` | `primary_signal` | `regulatory_action` | Coverage/Efficiency | Max |
|---|---|---|---|---|---|
| Easy | 0.25 | 0.30 | 0.35 | +0.09 efficiency | **0.99** |
| Medium | 0.20 | 0.30 | 0.30 | +0.15 coverage | **0.95** |
| Hard | 0.15 | 0.25 + 0.15 secondary | 0.25 | +0.10 coverage | **0.90+** |

All scores are strictly clamped to **(0.01, 0.99)** — never 0.0 or 1.0.

---

## 🚀 Setup & Usage

### Local (Python)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run tests
python test_env.py

# 3. Start the server (port 7860)
uvicorn server.app:app --host 0.0.0.0 --port 7860

# 4. Open the UI
open http://localhost:7860/ui

# 5. Run baseline inference
export HF_TOKEN=hf_your_token_here
python inference.py
```

### Docker

```bash
# Build
docker build -t drug-triage-env .

# Run
docker run -p 7860:7860 drug-triage-env

# Test
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy"}'
```

### API Usage

```python
import requests

# Reset environment
resp = requests.post("http://localhost:7860/reset", json={"task_id": "medium"})
obs = resp.json()

# Take a step
resp = requests.post("http://localhost:7860/step", json={
    "action_type": "search_faers",
    "parameters": {}
})
result = resp.json()
print(result["observation"]["current_output"])
```

---

## 🌐 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `HF_TOKEN` | HuggingFace token (used as API key for inference) | **Required** |
| `API_BASE_URL` | LLM API endpoint | `https://router.huggingface.co/v1` |
| `MODEL_NAME` | Model to use for inference | `Qwen/Qwen2.5-72B-Instruct` |

---

## 📊 Baseline Scores

Measured using `Qwen/Qwen2.5-72B-Instruct` via the HuggingFace router:

| Task | Score | Notes |
|---|---|---|
| Easy (Metformin) | ~0.78 | Correctly identifies lactic acidosis + monitor |
| Medium (Rofecoxib) | ~0.65 | Correctly identifies MI; sometimes misses `withdraw` |
| Hard (Isotretinoin) | ~0.52 | Partial credit on dual signals; restrict reasoning is difficult |

---

## 📁 Project Structure

```
drug-triage-env/
├── Dockerfile                  # Root-level (required for HF Spaces)
├── openenv.yaml                # OpenEnv spec (port 7860, LF endings)
├── requirements.txt            # Includes openenv-core
├── pyproject.toml
├── inference.py                # Baseline inference script (root-level, required)
├── test_env.py                 # Smoke tests
├── start.sh                    # Docker entrypoint
├── README.md
├── environment/
│   ├── __init__.py
│   ├── models.py               # DrugAction, DrugObservation, DrugReward, TaskConfig
│   ├── actions.py              # Action handler (6 action types, fixture-backed)
│   ├── tasks.py                # 3 tasks: easy/medium/hard
│   ├── graders.py              # Deterministic graders with partial credit
│   ├── env.py                  # DrugTriageEnv: reset/step/state
│   └── fixtures/
│       ├── METFORMIN.json      # FDA FAERS + label + signal + literature data
│       ├── ROFECOXIB.json
│       └── ISOTRETINOIN.json
└── server/
    └── app.py                  # FastAPI + Gradio UI dashboard
```

---

## 🔬 Technical Details

- **Data source**: All FAERS statistics, PRR/ROR values, and trial results are based on published literature and historical regulatory filings — pre-baked as fixtures for determinism and reproducibility.
- **No live API calls**: The environment is fully self-contained and offline-capable.
- **Fuzzy string matching**: Graders accept common aliases (e.g. "Vioxx" = "rofecoxib", "heart attack" = "myocardial infarction") to be robust to LLM paraphrase.
- **Reward clamping**: All reward values are strictly in **(0.01, 0.99)** via Pydantic `field_validator`.
- **OpenEnv compliance**: Implements the full `step()` / `reset()` / `state()` contract with typed Pydantic models.

---

## 📚 References

1. Graham DJ et al. (2005). *Risk of acute myocardial infarction and sudden cardiac death in patients treated with COX-2 selective and non-selective NSAIDs.* The Lancet. PMID: 16260634
2. Bresalier RS et al. (2005). *Cardiovascular Events Associated with Rofecoxib in a Colorectal Adenoma Chemoprevention Trial (APPROVe).* NEJM. PMID: 15987910
3. Matok I et al. (2010). *Risk of lactic acidosis with metformin use in type 2 diabetes.* BMJ. PMID: 20488901
4. Vallerand IA et al. (2017). *Isotretinoin and the risk of severe psychiatric adverse outcomes.* JAMA Dermatology. PMID: 28678990
5. FDA iPLEDGE Program. https://www.ipledgeprogram.com/
