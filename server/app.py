"""
Drug-Triage-Env: FastAPI server + Gradio UI.

Exposes:
  POST /reset  — OpenEnv reset endpoint
  POST /step   — OpenEnv step endpoint
  GET  /state  — OpenEnv state endpoint
  GET  /tasks  — List all available tasks
  GET  /health — Health check
  GET  /ui     — Interactive Gradio pharmacovigilance dashboard
"""

from __future__ import annotations

import json
import os
import time
from contextlib import asynccontextmanager
from typing import Any

import gradio as gr
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from environment.env import DrugTriageEnv
from environment.models import DrugAction
from environment.tasks import TASKS


# ---------------------------------------------------------------------------
# Request / response models (API layer)
# ---------------------------------------------------------------------------

class ResetRequest(BaseModel):
    task_id: str = "easy"


class StepResponse(BaseModel):
    observation: dict[str, Any]
    reward: dict[str, Any]
    done: bool
    info: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


# ---------------------------------------------------------------------------
# Lifespan — initialise environment on startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    initial_task = os.getenv("TASK_ID", "easy")
    app.state.env = DrugTriageEnv(initial_task)
    yield


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Drug-Triage-Env",
    description=(
        "A real-world OpenEnv pharmacovigilance environment where AI agents "
        "investigate FDA FAERS adverse event signals and recommend regulatory actions "
        "across 3 drugs of increasing difficulty."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# OpenEnv API Routes
# ---------------------------------------------------------------------------

@app.post("/reset")
async def reset_env(body: ResetRequest | None = None) -> dict[str, Any]:
    """Reset the environment, optionally switching tasks."""
    task_id = body.task_id if body else "easy"
    env: DrugTriageEnv = app.state.env

    if env.task.task_id != task_id:
        try:
            app.state.env = DrugTriageEnv(task_id)
            env = app.state.env
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    obs = env.reset()
    return obs.model_dump()


@app.post("/step")
async def step_env(action: DrugAction) -> StepResponse:
    """Execute one agent action."""
    env: DrugTriageEnv = app.state.env
    try:
        obs, reward, done, info = env.step(action)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return StepResponse(
        observation=obs.model_dump(),
        reward=reward.model_dump(),
        done=done,
        info=info,
    )


@app.get("/state")
async def get_state() -> dict[str, Any]:
    """Return the current environment state."""
    env: DrugTriageEnv = app.state.env
    return env.state()


@app.get("/tasks")
async def list_tasks() -> list[dict[str, Any]]:
    """Return all available task definitions."""
    return [
        {
            "task_id": t.task_id,
            "name": t.name,
            "difficulty": t.difficulty,
            "drug_name": t.drug_name,
            "description": t.description,
            "max_steps": t.max_steps,
        }
        for t in TASKS
    ]


@app.get("/health")
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        environment="drug-triage-env",
    )


# ---------------------------------------------------------------------------
# Gradio UI — Pharmacovigilance Dashboard
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

* { font-family: 'Inter', sans-serif; box-sizing: border-box; }

body, .gradio-container {
    background: #060e1a !important;
    color: #e0eaff !important;
}

.gradio-container {
    max-width: 1400px !important;
    margin: 0 auto !important;
}

/* Header */
#header-html {
    background: linear-gradient(135deg, #071722 0%, #0a2540 50%, #071722 100%);
    border: 1px solid rgba(0, 210, 180, 0.25);
    border-radius: 12px;
    padding: 28px 36px;
    margin-bottom: 16px;
    box-shadow: 0 4px 32px rgba(0, 210, 180, 0.08);
}

/* Panels */
.panel-box {
    background: #0d1f35;
    border: 1px solid rgba(0, 210, 180, 0.2);
    border-radius: 10px;
    padding: 20px;
    height: 100%;
}

/* Buttons */
button.primary-btn {
    background: linear-gradient(135deg, #00c9a7, #00a8d4) !important;
    color: #000 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 28px !important;
    font-size: 15px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 16px rgba(0, 201, 167, 0.35) !important;
}

button.primary-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 24px rgba(0, 201, 167, 0.5) !important;
}

/* Textareas and inputs */
textarea, .gr-textbox textarea {
    background: #071722 !important;
    color: #e0eaff !important;
    border: 1px solid rgba(0, 210, 180, 0.25) !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
}

/* Radio buttons */
.gr-radio label {
    color: #e0eaff !important;
}

/* Labels */
label span {
    color: #8ab4d4 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

/* Score display */
.score-display {
    font-family: 'JetBrains Mono', monospace;
    font-size: 48px;
    font-weight: 700;
    text-align: center;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #071722; }
::-webkit-scrollbar-thumb { background: rgba(0, 201, 167, 0.4); border-radius: 4px; }
"""

HEADER_HTML = """
<div style="display:flex; align-items:center; gap:24px;">
  <div style="font-size:56px;">🧬</div>
  <div>
    <div style="font-size:28px; font-weight:800; color:#00d4b4; letter-spacing:-0.5px;">
      Drug Adverse Event Triage — OpenEnv
    </div>
    <div style="font-size:15px; color:#8ab4d4; margin-top:6px; font-weight:400;">
      AI-powered pharmacovigilance · FDA FAERS signal detection · Regulatory decision support
    </div>
    <div style="display:flex; gap:12px; margin-top:12px; flex-wrap:wrap;">
      <span style="background:rgba(0,201,167,0.15); color:#00d4b4; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600; border:1px solid rgba(0,201,167,0.3);">✓ OpenEnv Compliant</span>
      <span style="background:rgba(0,168,212,0.15); color:#00c8ff; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600; border:1px solid rgba(0,168,212,0.3);">🧪 3 Tasks (Easy→Hard)</span>
      <span style="background:rgba(255,107,53,0.15); color:#ff8c60; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600; border:1px solid rgba(255,107,53,0.3);">⚡ Real FDA FAERS Data</span>
      <span style="background:rgba(179,136,255,0.15); color:#c7a8ff; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600; border:1px solid rgba(179,136,255,0.3);">🏆 Hackathon 2026</span>
    </div>
  </div>
</div>
"""

TASK_INFO = {
    "easy": {
        "drug": "METFORMIN",
        "signal": "Lactic Acidosis",
        "action": "Monitor",
        "color": "#00c9a7",
        "icon": "🟢",
        "prr": "4.7",
        "ror": "5.1",
        "strength": "STRONG",
        "description": "Biguanide antidiabetic • ~90M US prescriptions/year • Well-characterized signal",
    },
    "medium": {
        "drug": "ROFECOXIB (Vioxx)",
        "signal": "Myocardial Infarction",
        "action": "Withdraw",
        "color": "#ffb300",
        "icon": "🟡",
        "prr": "8.9",
        "ror": "9.7",
        "strength": "CRITICAL",
        "description": "COX-2 NSAID • Withdrawn Oct 2004 • APPROVe trial: 1.92x CV risk",
    },
    "hard": {
        "drug": "ISOTRETINOIN (Accutane)",
        "signal": "Teratogenicity + Depression",
        "action": "Restrict (iPLEDGE REMS)",
        "color": "#ff6b35",
        "icon": "🔴",
        "prr": "47.3 / 6.8",
        "ror": "52.1 / 7.4",
        "strength": "CRITICAL + STRONG",
        "description": "Retinoid • iPLEDGE REMS since 2006 • Two concurrent signals",
    },
}


def get_task_card_html(task_id: str) -> str:
    info = TASK_INFO[task_id]
    strength_color = "#ff1744" if "CRITICAL" in info["strength"] else "#ffb300" if "STRONG" in info["strength"] else "#00c9a7"
    return f"""
<div style="background:#071722; border:1px solid {info['color']}44; border-radius:10px; padding:20px; font-family:'Inter',sans-serif;">
  <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px;">
    <div>
      <div style="font-size:11px; color:#8ab4d4; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">DRUG UNDER INVESTIGATION</div>
      <div style="font-size:22px; font-weight:800; color:{info['color']};">{info['icon']} {info['drug']}</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:11px; color:#8ab4d4; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">DIFFICULTY</div>
      <div style="background:{info['color']}22; color:{info['color']}; padding:4px 14px; border-radius:20px; font-weight:700; border:1px solid {info['color']}55; font-size:13px;">{task_id.upper()}</div>
    </div>
  </div>
  <div style="color:#c0d8f0; font-size:13px; margin-bottom:16px;">{info['description']}</div>
  <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px;">
    <div style="background:#0d1f35; border-radius:8px; padding:12px; border:1px solid rgba(255,255,255,0.08);">
      <div style="font-size:10px; color:#8ab4d4; font-weight:600; text-transform:uppercase; letter-spacing:0.8px;">PRIMARY SIGNAL</div>
      <div style="font-size:14px; font-weight:700; color:#e0eaff; margin-top:4px;">{info['signal']}</div>
    </div>
    <div style="background:#0d1f35; border-radius:8px; padding:12px; border:1px solid rgba(255,255,255,0.08);">
      <div style="font-size:10px; color:#8ab4d4; font-weight:600; text-transform:uppercase; letter-spacing:0.8px;">PRR / ROR</div>
      <div style="font-size:14px; font-weight:700; color:{strength_color}; margin-top:4px;">{info['prr']} / {info['ror']}</div>
    </div>
    <div style="background:#0d1f35; border-radius:8px; padding:12px; border:1px solid rgba(255,255,255,0.08);">
      <div style="font-size:10px; color:#8ab4d4; font-weight:600; text-transform:uppercase; letter-spacing:0.8px;">RECOMMENDED ACTION</div>
      <div style="font-size:14px; font-weight:700; color:{info['color']}; margin-top:4px;">{info['action']}</div>
    </div>
  </div>
</div>"""


DEMO_SCRIPTS = {
    "easy": [
        ("search_faers", {}, "🔍 Querying FDA FAERS database for METFORMIN adverse events..."),
        ("fetch_label", {}, "📋 Fetching official FDA drug label and prescribing information..."),
        ("submit", {"drug_name": "metformin", "primary_signal": "lactic acidosis", "regulatory_action": "monitor"},
         "📤 Submitting assessment: drug=metformin, signal=lactic acidosis, action=monitor"),
    ],
    "medium": [
        ("search_faers", {}, "🔍 Querying FDA FAERS database for ROFECOXIB adverse events..."),
        ("analyze_signal", {}, "📊 Running disproportionality analysis (PRR/ROR/IC025)..."),
        ("check_literature", {}, "📚 Checking APPROVe trial and VIGOR trial data..."),
        ("submit", {"drug_name": "rofecoxib", "primary_signal": "myocardial infarction", "regulatory_action": "withdraw"},
         "📤 Submitting assessment: drug=rofecoxib, signal=myocardial infarction, action=WITHDRAW"),
    ],
    "hard": [
        ("search_faers", {}, "🔍 Querying FDA FAERS for ISOTRETINOIN adverse events..."),
        ("fetch_label", {}, "📋 Fetching FDA label — checking Black Box Warnings..."),
        ("analyze_signal", {}, "📊 Running dual-signal disproportionality analysis..."),
        ("lookup_mechanism", {}, "🔬 Looking up retinoid mechanism and teratogenic pathway..."),
        ("check_literature", {}, "📚 Reviewing iPLEDGE effectiveness and psychiatric literature..."),
        ("submit", {
            "drug_name": "isotretinoin",
            "primary_signal": "teratogenicity",
            "secondary_signal": "depression",
            "regulatory_action": "restrict"
         }, "📤 Submitting dual-signal assessment: restrict via iPLEDGE REMS"),
    ],
}


def format_reward_html(reward_data: dict) -> str:
    if not reward_data:
        return "<div style='color:#8ab4d4;'>No reward data yet.</div>"

    value = reward_data.get("value", 0)
    breakdown = reward_data.get("breakdown", {})
    message = reward_data.get("message", "")

    # Score color
    if value >= 0.7:
        score_color = "#00c9a7"
        grade = "✅ EXCELLENT"
    elif value >= 0.5:
        score_color = "#4fc3f7"
        grade = "👍 GOOD"
    elif value >= 0.3:
        score_color = "#ffb300"
        grade = "⚠️ PARTIAL"
    else:
        score_color = "#ff5252"
        grade = "❌ LOW"

    bd_rows = ""
    for criterion, score in breakdown.items():
        sign = "+" if score >= 0 else ""
        s_color = "#00c9a7" if score > 0 else "#ff5252" if score < 0 else "#8ab4d4"
        bd_rows += f"""
        <tr>
          <td style="padding:6px 8px; color:#c0d8f0; font-size:13px;">{criterion.replace('_', ' ').title()}</td>
          <td style="padding:6px 8px; color:{s_color}; font-weight:700; font-size:13px; text-align:right; font-family:'JetBrains Mono',monospace;">{sign}{score:.2f}</td>
        </tr>"""

    return f"""
<div style="font-family:'Inter',sans-serif;">
  <div style="text-align:center; margin-bottom:20px;">
    <div style="font-size:11px; color:#8ab4d4; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">FINAL SCORE</div>
    <div style="font-size:64px; font-weight:800; color:{score_color}; font-family:'JetBrains Mono',monospace; line-height:1;">{value:.2f}</div>
    <div style="font-size:16px; color:{score_color}; font-weight:600; margin-top:6px;">{grade}</div>
  </div>
  <div style="background:#071722; border-radius:10px; overflow:hidden; border:1px solid rgba(255,255,255,0.08); margin-bottom:16px;">
    <table style="width:100%; border-collapse:collapse;">
      <thead>
        <tr style="background:#0d2137; border-bottom:1px solid rgba(255,255,255,0.08);">
          <th style="padding:8px 8px; text-align:left; color:#8ab4d4; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.8px;">Criterion</th>
          <th style="padding:8px 8px; text-align:right; color:#8ab4d4; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.8px;">Score</th>
        </tr>
      </thead>
      <tbody>{bd_rows}</tbody>
    </table>
  </div>
  <div style="background:#0d1f35; border-radius:8px; padding:12px; border-left:3px solid {score_color};">
    <div style="font-size:11px; color:#8ab4d4; font-weight:600; margin-bottom:4px;">GRADER MESSAGE</div>
    <div style="font-size:12px; color:#c0d8f0;">{message}</div>
  </div>
</div>"""


def run_demo(task_id: str):
    """Generator: yields (log_text, task_card, reward_html) as it animates."""
    env = DrugTriageEnv(task_id)
    obs = env.reset()
    script = DEMO_SCRIPTS[task_id]
    log = []
    task_card = get_task_card_html(task_id)

    log.append(f"{'='*60}")
    log.append(f"🚀 NEW CASE OPENED: {obs.drug_name}")
    log.append(f"Task: {env.task.name}")
    log.append(f"Difficulty: {task_id.upper()} | Max Steps: {env.task.max_steps}")
    log.append(f"{'='*60}")
    log.append("")
    yield "\n".join(log), task_card, ""

    reward_html = ""
    for action_type, params, description in script:
        time.sleep(0.3)
        log.append(f"▶ STEP {env.step_number + 1}: {description}")
        log.append(f"  Action: {action_type}")
        if params:
            log.append(f"  Parameters: {json.dumps(params, indent=4)}")

        action = DrugAction(action_type=action_type, parameters=params)
        obs_new, reward, done, info = env.step(action)

        if action_type != "submit":
            src = obs_new.current_output.get("source", "")
            data = obs_new.current_output.get("data", obs_new.current_output)
            hint = obs_new.current_output.get("hint", "")
            log.append(f"  ✓ Source: {src}")
            # Show first key insight
            if isinstance(data, dict):
                for k, v in list(data.items())[:3]:
                    truncated = str(v)[:120] + "..." if len(str(v)) > 120 else str(v)
                    log.append(f"    {k}: {truncated}")
            if hint:
                log.append(f"  💡 {hint}")
            log.append(f"  Reward: +{reward.value:.2f} | Steps remaining: {info['steps_remaining']}")
        else:
            log.append(f"  📊 Final score: {reward.value:.2f}")
            log.append(f"  {reward.message}")
            reward_html = format_reward_html(reward.model_dump())

        log.append("")
        yield "\n".join(log), task_card, reward_html

        if done:
            log.append(f"{'='*60}")
            log.append("✅ EPISODE COMPLETE")
            log.append(f"{'='*60}")
            yield "\n".join(log), task_card, reward_html
            break


def create_gradio_demo() -> gr.Blocks:
    """Build the interactive pharmacovigilance dashboard."""

    with gr.Blocks(title="Drug Adverse Event Triage — OpenEnv") as demo:
        # Inject custom CSS via HTML block (Gradio 6 compatible)
        gr.HTML(f"<style>{CUSTOM_CSS}</style>")

        # Header
        gr.HTML(value=HEADER_HTML, elem_id="header-html")

        with gr.Row():
            # Left column: task selection + info
            with gr.Column(scale=1):
                gr.Markdown(
                    "### 📋 Case Selection",
                    elem_classes=["panel-label"],
                )
                task_radio = gr.Radio(
                    choices=[
                        ("🟢 Easy — Metformin", "easy"),
                        ("🟡 Medium — Rofecoxib (Vioxx)", "medium"),
                        ("🔴 Hard — Isotretinoin (Accutane)", "hard"),
                    ],
                    value="easy",
                    label="Select Investigation Task",
                    interactive=True,
                )
                task_card = gr.HTML(value=get_task_card_html("easy"))

                gr.Markdown("---")
                gr.Markdown("### 🗂️ API Reference")
                gr.Markdown(
                    """
**OpenEnv Endpoints:**
- `POST /reset` — Start new episode
- `POST /step` — Execute action
- `GET /state` — Current state
- `GET /tasks` — All tasks
- `GET /health` — Health check

**Action Space:**
- `search_faers` — FDA adverse event database
- `fetch_label` — Official FDA labeling
- `analyze_signal` — PRR/ROR disproportionality
- `lookup_mechanism` — Pharmacology
- `check_literature` — Safety literature
- `submit` — Final recommendation
                    """,
                    elem_classes=["api-ref"],
                )

            # Right column: investigation terminal + reward
            with gr.Column(scale=2):
                gr.Markdown("### 🔬 Live Investigation Terminal")
                run_btn = gr.Button(
                    "▶ RUN AGENT INVESTIGATION",
                    variant="primary",
                    elem_classes=["primary-btn"],
                )
                investigation_log = gr.Textbox(
                    value="Select a task and click RUN to watch the AI agent investigate...",
                    label="Investigation Log",
                    lines=22,
                    max_lines=22,
                    interactive=False,
                )

                gr.Markdown("### 📊 Grading & Reward Breakdown")
                reward_display = gr.HTML(
                    value="<div style='color:#8ab4d4; padding:20px; text-align:center; font-size:14px;'>Run an investigation to see the reward breakdown.</div>"
                )

        # Task card update when radio changes
        task_radio.change(
            fn=lambda t: get_task_card_html(t),
            inputs=[task_radio],
            outputs=[task_card],
        )

        # Run button triggers the animated demo
        run_btn.click(
            fn=run_demo,
            inputs=[task_radio],
            outputs=[investigation_log, task_card, reward_display],
        )

        # Footer
        gr.HTML("""
<div style="margin-top:24px; padding:16px; border-top:1px solid rgba(0,210,180,0.15); display:flex; justify-content:space-between; align-items:center; color:#8ab4d4; font-size:12px;">
  <div>🧬 Drug Adverse Event Triage · OpenEnv v1.0.0 · Meta × HuggingFace Hackathon 2026</div>
  <div style="display:flex; gap:16px;">
    <span>📡 API: <code style="color:#00d4b4;">/reset</code> <code style="color:#00d4b4;">/step</code> <code style="color:#00d4b4;">/state</code></span>
    <span>🐳 Docker-ready · HF Spaces deployable</span>
  </div>
</div>
""")

    return demo


# Mount Gradio onto FastAPI at /ui
_gradio_demo = create_gradio_demo()
app = gr.mount_gradio_app(app, _gradio_demo, path="/ui")


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=7860,
        reload=False,
    )


if __name__ == "__main__":
    main()
