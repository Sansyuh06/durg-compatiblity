# -*- coding: utf-8 -*-
"""
Drug-Triage-Env: FastAPI server + Interactive HTML Dashboard.

Exposes:
  POST /reset              -- OpenEnv reset endpoint
  POST /step               -- OpenEnv step endpoint
  GET  /state              -- OpenEnv state endpoint
  GET  /tasks              -- List all available tasks
  GET  /health             -- Health check
  GET  /                   -- Premium interactive pharmacovigilance dashboard
  GET  /ui                 -- Alias for /
  POST /api/demo/{task_id} -- Run a scripted demo step (returns JSON)
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from environment.env import DrugTriageEnv
from environment.models import DrugAction
from environment.tasks import TASKS
from .quantamed_sim import (
    compute_pk_curve,
    get_quantamed_candidates,
    get_quantamed_patient_profiles,
    get_quantamed_drug_summary,
    get_quantamed_patient_summary,
    recommend_quantamed_candidates,
    quantum_protein_folding_payload,
    vqe_demo_payload,
)
from .pdf_report import generate_quantamed_pdf


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
    tasks_available: int
    uptime_seconds: float


# ---------------------------------------------------------------------------
# Leaderboard — in-memory store (persists for the lifetime of the process)
# ---------------------------------------------------------------------------

_DIFFICULTY_META: dict[str, dict[str, Any]] = {
    "easy":   {"label": "Easy",   "avg_frontier_score": 0.78, "note": "Clear single signal; well-characterized Black Box Warning"},
    "medium": {"label": "Medium", "avg_frontier_score": 0.65, "note": "Critical signal buried in class-effect noise; requires literature confirmation"},
    "hard":   {"label": "Hard",   "avg_frontier_score": 0.52, "note": "Dual concurrent signals; complex REMS restriction reasoning required"},
}

_leaderboard: list[dict[str, Any]] = []


def _record_leaderboard(task_id: str, score: float, steps_taken: int) -> None:
    """Append a completed episode result to the in-memory leaderboard."""
    _leaderboard.append({
        "task_id": task_id,
        "score": round(score, 4),
        "steps_taken": steps_taken,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    # Keep at most 500 entries so memory stays bounded
    if len(_leaderboard) > 500:
        _leaderboard.pop(0)


# ---------------------------------------------------------------------------
# Lifespan -- initialise environment + lock on startup
# ---------------------------------------------------------------------------

_start_time: float = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the async lock inside the running event loop
    app.state.lock = asyncio.Lock()

    # Initialise environment with graceful fallback on bad TASK_ID
    initial_task = os.getenv("TASK_ID", "easy")
    try:
        app.state.env = DrugTriageEnv(initial_task)
    except ValueError:
        # Bad TASK_ID env var -- fall back to easy rather than crashing
        app.state.env = DrugTriageEnv("easy")

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
async def reset_env(body: Optional[ResetRequest] = None) -> dict[str, Any]:
    """Reset the environment, optionally switching tasks."""
    task_id = (body.task_id if body else None) or "easy"
    async with app.state.lock:
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
    async with app.state.lock:
        env: DrugTriageEnv = app.state.env
        try:
            obs, reward, done, info = env.step(action)
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        # Record completed episodes on the live leaderboard
        if done:
            _record_leaderboard(
                task_id=env.task.task_id,
                score=reward.value,
                steps_taken=env.step_number,
            )

    return StepResponse(
        observation=obs.model_dump(),
        reward=reward.model_dump(),
        done=done,
        info=info,
    )


@app.get("/state")
async def get_state() -> dict[str, Any]:
    """Return the current environment state."""
    async with app.state.lock:
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
        tasks_available=len(TASKS),
        uptime_seconds=round(time.time() - _start_time, 2),
    )


@app.get("/leaderboard")
async def get_leaderboard() -> list[dict[str, Any]]:
    """Return all completed episodes ranked by score (highest first).

    Each entry contains: task_id, score, steps_taken, timestamp.
    Scores are live — the board updates as agents run on this server.
    """
    return sorted(_leaderboard, key=lambda x: x["score"], reverse=True)


# ---------------------------------------------------------------------------
# Demo scripts for the interactive dashboard
# ---------------------------------------------------------------------------

DEMO_SCRIPTS: dict[str, list[tuple[str, dict]]] = {
    "easy": [
        ("search_faers", {}),
        ("fetch_label", {}),
        ("submit", {"drug_name": "metformin", "primary_signal": "lactic acidosis", "regulatory_action": "monitor"}),
    ],
    "medium": [
        ("search_faers", {}),
        ("analyze_signal", {}),
        ("check_literature", {}),
        ("submit", {"drug_name": "rofecoxib", "primary_signal": "myocardial infarction", "regulatory_action": "withdraw"}),
    ],
    "hard": [
        ("search_faers", {}),
        ("fetch_label", {}),
        ("analyze_signal", {}),
        ("lookup_mechanism", {}),
        ("check_literature", {}),
        ("submit", {
            "drug_name": "isotretinoin",
            "primary_signal": "teratogenicity",
            "secondary_signal": "depression",
            "regulatory_action": "restrict",
        }),
    ],
}


@app.post("/api/demo/{task_id}")
async def run_demo_step(task_id: str) -> JSONResponse:
    """Run a complete scripted demo for a task and return all steps as JSON."""
    if task_id not in DEMO_SCRIPTS:
        raise HTTPException(status_code=404, detail=f"Unknown task: {task_id}")

    # Demo uses its own fresh env -- never touches the shared env lock
    env = DrugTriageEnv(task_id)
    env.reset()
    script = DEMO_SCRIPTS[task_id]
    steps_out = []

    for action_type, params in script:
        action = DrugAction(action_type=action_type, parameters=params)
        obs, reward, done, info = env.step(action)
        steps_out.append({
            "action_type": action_type,
            "parameters": params,
            "observation": obs.model_dump(),
            "reward": reward.model_dump(),
            "done": done,
            "info": info,
        })
        if done:
            break

    return JSONResponse({"task_id": task_id, "steps": steps_out})


# ---------------------------------------------------------------------------
# QuantaMed (Quantum-Enhanced Precision Drug Discovery) demo module
# ---------------------------------------------------------------------------

@app.get("/quantamed", response_class=FileResponse)
async def quantamed_dashboard() -> FileResponse:
    """Serve the QuantaMed interactive demo page."""
    return FileResponse("server/quantamed/index.html", media_type="text/html")


# Serve static assets inside the quantamed folder (three.min.js, etc.)
_quantamed_dir = os.path.join(os.path.dirname(__file__), "quantamed")
app.mount("/quantamed", StaticFiles(directory=_quantamed_dir), name="quantamed_static")



@app.get("/api/quantamed/vqe")
async def quantamed_vqe() -> JSONResponse:
    """Return VQE convergence curves for the QuantaMed UI chart."""
    return JSONResponse(vqe_demo_payload())


@app.get("/api/quantamed/pk")
async def quantamed_pk(
    drug: str = Query(..., description="Drug id: vpa|ltg|lev|tpm|zns"),
    daily_dose_mg: float = Query(1000.0, gt=0.0),
    doses_per_day: int = Query(2, ge=1, le=4),
    cyp2c9: str = Query("intermediate"),
    co_med: str = Query("none", description="Optional co-med toggle for DDI demo (e.g., vpa|ocp)"),
) -> JSONResponse:
    """Dose/genotype-adjusted PK curve (one-compartment steady-state)."""
    try:
        payload = compute_pk_curve(
            drug_id=drug,
            daily_dose_mg=daily_dose_mg,
            doses_per_day=doses_per_day,
            cyp2c9=cyp2c9,
            co_med=co_med,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse(payload)


@app.get("/api/quantamed/candidates")
async def quantamed_candidates() -> JSONResponse:
    """Return QuantaMed drug candidates with scoring metadata."""
    return JSONResponse(get_quantamed_candidates())


@app.get("/api/quantamed/patients")
async def quantamed_patients() -> JSONResponse:
    """Return sample patient profiles for the QuantaMed demo."""
    return JSONResponse(get_quantamed_patient_profiles())


@app.get("/api/quantamed/score")
async def quantamed_score(drug: str = Query(..., description="Candidate drug id"), patient: str = Query(..., description="Patient profile id")) -> JSONResponse:
    """Return a scored candidate summary for a patient-specific scenario."""
    try:
        payload = get_quantamed_drug_summary(drug, patient)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse(payload)


@app.get("/api/quantamed/recommendations")
async def quantamed_recommendations(patient: str = Query(..., description="Patient profile id")) -> JSONResponse:
    """Return ranked candidate recommendations for a patient."""
    try:
        payload = recommend_quantamed_candidates(patient)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse(payload)


@app.get("/api/quantamed/patient")
async def quantamed_patient(patient: str = Query(..., description="Patient profile id")) -> JSONResponse:
    """Return patient metadata for the QuantaMed demo."""
    try:
        payload = get_quantamed_patient_summary(patient)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse(payload)


@app.get("/api/quantamed/protein-folding")
async def quantamed_protein_folding(case: str = Query("default", description="Protein folding demo case")) -> JSONResponse:
    """Run a toy quantum-backed protein folding simulation and return animation frames."""
    try:
        payload = quantum_protein_folding_payload(case=case)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse(payload)


@app.get("/api/quantamed/report")
async def quantamed_report(patient: str = Query(..., description="Patient profile id")) -> Response:
    """Generate and return a clinical PDF report for the patient."""
    try:
        pdf_bytes = generate_quantamed_pdf(patient_id=patient)
        return Response(content=bytes(pdf_bytes), media_type="application/pdf")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc



# ---------------------------------------------------------------------------
# Interactive HTML Dashboard
# ---------------------------------------------------------------------------

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "out")


@app.get("/")
async def root_redirect() -> RedirectResponse:
    """Redirect the root URL to the QuantaMed demo app."""
    return RedirectResponse(url="/quantamed")

if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    @app.get("/ui", response_class=FileResponse)
    async def dashboard_ui():
        """Alias for backward compatibility."""
        return FileResponse("server/index.html", media_type="text/html")

    @app.get("/dashboard", response_class=FileResponse)
    async def dashboard():
        """Serve the interactive pharmacovigilance dashboard."""
        return FileResponse("server/index.html", media_type="text/html")


# ---------------------------------------------------------------------------
# Gradio interface — mounted at /gradio (works alongside FastAPI, no HF_TOKEN)
# ---------------------------------------------------------------------------

try:
    import gradio as gr

    # ---------------------------------------------------------------------------
    # Gradio helpers — call the env directly (no HTTP round-trip, no lock deadlock)
    # ---------------------------------------------------------------------------

    def _gr_reset(task: str) -> tuple[str, str]:
        """Start a fresh episode directly on a private env instance."""
        try:
            env = DrugTriageEnv(task)
            obs = env.reset()
            obs_dict = obs.model_dump()
            # Store env on app.state so action buttons can reuse it
            app.state.gradio_env = env
            return (
                f"✅ Episode started — drug: {obs_dict['drug_name']} | task: {task.upper()}",
                f"```json\n{json.dumps(obs_dict, indent=2)}\n```",
            )
        except Exception as e:
            return f"❌ Reset failed: {e}", ""

    def _gr_action(action: str, task: str) -> tuple[str, str]:
        """Run one investigation step on the Gradio-private env."""
        try:
            env: DrugTriageEnv = getattr(app.state, "gradio_env", None)
            if env is None:
                env = DrugTriageEnv(task)
                env.reset()
                app.state.gradio_env = env
            step_action = DrugAction(action_type=action, parameters={})
            obs, reward, done, info = env.step(step_action)
            obs_dict = obs.model_dump()
            rwd_dict = reward.model_dump()
            data = {"observation": obs_dict, "reward": rwd_dict, "done": done, "info": info}
            summary = (
                f"Step {obs_dict.get('step_number', '?')} | action={action} | "
                f"reward={rwd_dict.get('value', 0):.4f} | done={done}"
            )
            return summary, f"```json\n{json.dumps(data, indent=2)}\n```"
        except Exception as e:
            return f"❌ Action failed: {e}", ""

    def _gr_submit(drug: str, primary: str, secondary: str, action: str) -> tuple[str, str]:
        """Submit final assessment on the Gradio-private env."""
        params: dict = {
            "drug_name": drug.strip().lower(),
            "primary_signal": primary.strip().lower(),
            "regulatory_action": action.strip().lower(),
        }
        if secondary.strip():
            params["secondary_signal"] = secondary.strip().lower()
        try:
            env: DrugTriageEnv = getattr(app.state, "gradio_env", None)
            if env is None:
                return "❌ Start an episode first (click New Episode)", ""
            step_action = DrugAction(action_type="submit", parameters=params)
            obs, reward, done, info = env.step(step_action)
            rwd_dict = reward.model_dump()
            bd = rwd_dict.get("breakdown", {})
            bd_str = "\n".join(f"  {k}: {v:+.2f}" for k, v in bd.items()) if bd else ""
            data = {"observation": obs.model_dump(), "reward": rwd_dict, "done": done, "info": info}
            summary = (
                f"🏁 FINAL SCORE: {rwd_dict.get('value', 0):.4f}\n"
                f"{bd_str}\n\n"
                f"Message: {rwd_dict.get('message', '')}"
            )
            return summary, f"```json\n{json.dumps(data, indent=2)}\n```"
        except Exception as e:
            return f"❌ Submit failed: {e}", ""

    def _gr_demo(task: str) -> tuple[str, str]:
        """Run a complete scripted demo directly (mirrors /api/demo/{task})."""
        try:
            if task not in DEMO_SCRIPTS:
                return f"❌ Unknown task: {task}", ""
            env = DrugTriageEnv(task)
            env.reset()
            script = DEMO_SCRIPTS[task]
            steps_out = []
            for action_type, params in script:
                step_action = DrugAction(action_type=action_type, parameters=params)
                obs, reward, done, info = env.step(step_action)
                steps_out.append({
                    "action_type": action_type,
                    "parameters": params,
                    "observation": obs.model_dump(),
                    "reward": reward.model_dump(),
                    "done": done,
                    "info": info,
                })
                if done:
                    break
            data = {"task_id": task, "steps": steps_out}
            lines = []
            for i, s in enumerate(steps_out):
                rwd = s.get("reward", {})
                lines.append(
                    f"Step {i+1}: {s.get('action_type','?')} → reward={rwd.get('value',0):.4f}"
                )
            final = steps_out[-1]["reward"]["value"] if steps_out else 0
            summary = "\n".join(lines) + f"\n\n🏆 Final score: {final:.4f}"
            return summary, f"```json\n{json.dumps(data, indent=2)}\n```"
        except Exception as e:
            return f"❌ Demo failed: {e}", ""

    with gr.Blocks(
        title="Drug Adverse Event Triage — Pharmacovigilance AI",
        theme=gr.themes.Base(
            primary_hue="purple",
            secondary_hue="cyan",
            neutral_hue="slate",
        ),
        css="""
        .gradio-container { max-width: 1100px !important; }
        #title-md h1 { text-align: center; font-size: 2rem; }
        """,
    ) as _gradio_app:

        gr.Markdown(
            """# 🧬 Drug Adverse Event Triage
**Pharmacovigilance AI** · FDA FAERS Signal Detection · 3 Real Historical Drug Cases

> _In 2004, Vioxx killed an estimated 55,000 people before regulators caught the signal. This environment trains AI agents to catch the next one._
""",
            elem_id="title-md",
        )

        with gr.Row():
            task_dd = gr.Dropdown(
                choices=["easy", "medium", "hard"],
                value="easy",
                label="Task (Drug)",
                info="easy=Metformin · medium=Rofecoxib (Vioxx) · hard=Isotretinoin",
            )
            reset_btn = gr.Button("🔄 New Episode", variant="primary")

        with gr.Row():
            status_box = gr.Textbox(label="Episode Status", interactive=False, lines=1)
            raw_box = gr.Code(label="Raw Response", language="json", interactive=False, lines=10)

        gr.Markdown("### 🔬 Investigation Actions")
        with gr.Row():
            faers_btn  = gr.Button("🔍 Search FAERS")
            label_btn  = gr.Button("📄 Fetch Label")
            signal_btn = gr.Button("📈 Analyze Signal")
            mech_btn   = gr.Button("🔬 Lookup Mechanism")
            lit_btn    = gr.Button("📚 Check Literature")

        gr.Markdown("### 📋 Final Assessment (Submit)")
        with gr.Row():
            drug_in    = gr.Textbox(label="Drug Name", placeholder="metformin")
            primary_in = gr.Textbox(label="Primary Signal", placeholder="lactic acidosis")
            second_in  = gr.Textbox(label="Secondary Signal (hard only)", placeholder="depression")
            action_in  = gr.Dropdown(
                choices=["monitor", "restrict", "withdraw"],
                value="monitor",
                label="Regulatory Action",
            )
        submit_btn = gr.Button("⚖️ Submit Assessment", variant="primary")

        gr.Markdown("### 🤖 Auto Demo")
        demo_btn = gr.Button("▶  Run Scripted Demo (perfect score)", variant="secondary")

        reset_btn.click(_gr_reset, inputs=[task_dd], outputs=[status_box, raw_box])
        faers_btn.click(lambda t: _gr_action("search_faers", t),  inputs=[task_dd], outputs=[status_box, raw_box])
        label_btn.click(lambda t: _gr_action("fetch_label", t),   inputs=[task_dd], outputs=[status_box, raw_box])
        signal_btn.click(lambda t: _gr_action("analyze_signal", t), inputs=[task_dd], outputs=[status_box, raw_box])
        mech_btn.click(lambda t: _gr_action("lookup_mechanism", t), inputs=[task_dd], outputs=[status_box, raw_box])
        lit_btn.click(lambda t: _gr_action("check_literature", t),  inputs=[task_dd], outputs=[status_box, raw_box])
        submit_btn.click(_gr_submit, inputs=[drug_in, primary_in, second_in, action_in], outputs=[status_box, raw_box])
        demo_btn.click(_gr_demo, inputs=[task_dd], outputs=[status_box, raw_box])

    # Mount Gradio at /gradio (separate from the Next.js frontend at /)
    gr.mount_gradio_app(app, _gradio_app, path="/gradio")

except ImportError:
    # gradio not installed — /gradio route simply won't exist; harmless
    pass


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "7860")),
        reload=False,
        timeout_keep_alive=30,
    )


if __name__ == "__main__":
    main()
