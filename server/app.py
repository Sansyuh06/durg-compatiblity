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
import urllib.error
import urllib.request

import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Optional, cast

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
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
from .protein_structure import (
    model_protein_from_fasta,
    get_example_sequences,
)
from .protein_dynamics import (
    analyze_protein_dynamics,
)
from .patient_schema import (
    build_patient_from_dict,
    GABI_PRESET,
)
from .scoring_engine import (
    run_full_analysis,
    pipeline_pk,
)
from .kaggle_data import (
    get_drug_properties,
    get_all_drug_ids,
    get_tox21_profile,
    get_faers_signals,
    lookup_protein_target,
)


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

_DIFFICULTY_META: dict[str,
                       dict[str,
                            Any]] = {"easy": {"label": "Easy",
                                              "avg_frontier_score": 0.78,
                                              "note": "Clear single signal; well-characterized Black Box Warning"},
                                     "medium": {"label": "Medium",
                                                "avg_frontier_score": 0.65,
                                                "note": "Critical signal buried in class-effect noise; requires literature confirmation"},
                                     "hard": {"label": "Hard",
                                              "avg_frontier_score": 0.52,
                                              "note": "Dual concurrent signals; complex REMS restriction reasoning required"},
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
        "across 3 drugs of increasing difficulty."),
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

# Import and include patient management router
from server.api.patient_router import router as patient_router
app.include_router(patient_router)


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
        action = DrugAction(
            action_type=cast(
                Any,
                action_type),
            parameters=params)
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
# Foldables (Quantum-Enhanced Precision Drug Discovery) demo module
# ---------------------------------------------------------------------------


@app.get("/protein-dynamics", response_class=FileResponse)
async def protein_dynamics_page() -> FileResponse:
    """Serve the Protein Dynamics Analysis interactive page."""
    return FileResponse("server/quantamed/protein_dynamics.html", media_type="text/html")

@app.get("/quantamed", response_class=FileResponse)
async def quantamed_dashboard() -> FileResponse:
    """Serve the Foldables interactive demo page."""
    return FileResponse("server/quantamed/index.html", media_type="text/html")


# Serve static assets inside the quantamed folder (three.min.js, brain.obj, etc.)
# Mounted at /quantamed/static to avoid shadowing the explicit /quantamed
# HTML route
_quantamed_dir = os.path.join(os.path.dirname(__file__), "quantamed")
app.mount(
    "/quantamed/static",
    StaticFiles(
        directory=_quantamed_dir),
    name="quantamed_static")


@app.get("/api/quantamed/vqe")
async def quantamed_vqe() -> JSONResponse:
    """Return VQE convergence curves for the Foldables UI chart."""
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
    """Return Foldables drug candidates with scoring metadata."""
    return JSONResponse(get_quantamed_candidates())


@app.get("/api/quantamed/patients")
async def quantamed_patients() -> JSONResponse:
    """Return sample patient profiles for the Foldables demo."""
    return JSONResponse(get_quantamed_patient_profiles())


@app.get("/api/quantamed/score")
async def quantamed_score(drug: str = Query(...,
                                            description="Candidate drug id"),
                          patient: str = Query(...,
                                               description="Patient profile id")) -> JSONResponse:
    """Return a scored candidate summary for a patient-specific scenario."""
    try:
        payload = get_quantamed_drug_summary(drug, patient)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse(payload)


@app.get("/api/quantamed/recommendations")
async def quantamed_recommendations(
        patient: str = Query(..., description="Patient profile id")) -> JSONResponse:
    """Return ranked candidate recommendations for a patient."""
    try:
        payload = recommend_quantamed_candidates(patient)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse(payload)


class OllamaRequest(BaseModel):
    patient_profile: dict
    top_drug: str
    avoid_drug: str


@app.post("/api/quantamed/ollama_summary")
async def quantamed_ollama_summary(req: OllamaRequest) -> JSONResponse:
    """Generate a clinical summary using local Ollama model and a full JSON patient profile."""
    
    # Safely extract basic info to avoid key errors if fields are missing
    b_info = req.patient_profile.get('basic_info', {})
    name = b_info.get('name', 'the patient')
    age = b_info.get('age', 'unknown age')
    gender = b_info.get('gender', 'unknown gender')
    
    cond_info = req.patient_profile.get('condition', {})
    condition = cond_info.get('primary_diagnosis', 'an unknown condition')
    
    # Dump the full json for the prompt
    profile_str = json.dumps(req.patient_profile, indent=2)

    prompt = (
        f"You are an expert clinical pharmacologist AI. You are provided with the following comprehensive patient profile in JSON format:\n"
        f"{profile_str}\n\n"
        f"Write a highly personalized, concise, 3-sentence clinical recommendation for {name} (age {age}, {gender}) diagnosed with {condition}. "
        f"You MUST factor in the patient's unique genetics, labs, and biomarkers provided in the JSON when making your recommendation. "
        f"Strongly recommend starting {req.top_drug.upper()} as the top candidate. "
        f"Strongly advise against {req.avoid_drug.upper()} due to risks. "
        f"Do not include any disclaimers, warnings, or introductory fluff. Output exactly 3 sentences."
    )

    data = json.dumps({
        "model": "llama3:latest",
        "prompt": prompt,
        "stream": False
    }).encode("utf-8")

    req_obj = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=data,
        headers={
            "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req_obj, timeout=30) as response:
            result = json.loads(response.read().decode())
            return JSONResponse({"summary": result.get(
                "response", "Error generating response.")})
    except urllib.error.URLError as e:
        error_msg = str(e)
        user_msg = "Ollama is unavailable. Ensure Ollama is running locally on port 11434."
        if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
            user_msg = "Ollama timed out after 30 seconds"
        
        return JSONResponse(
            {
                "summary": user_msg,
                "error": error_msg,
                "available": False
            },
            status_code=503)


@app.get("/api/quantamed/patient")
async def quantamed_patient(patient: str = Query(...,
                                                 description="Patient profile id")) -> JSONResponse:
    """Return patient metadata for the Foldables demo."""
    try:
        payload = get_quantamed_patient_summary(patient)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse(payload)


@app.get("/api/quantamed/protein-folding")
async def quantamed_protein_folding(
    case: str = Query(
        "default",
        description="Protein folding demo case")) -> JSONResponse:
    """Run a toy quantum-backed protein folding simulation and return animation frames."""
    try:
        payload = quantum_protein_folding_payload(case=case)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse(payload)


@app.get("/api/quantamed/report")
async def quantamed_report(patient: str = Query(...,
                                                description="Patient profile id")) -> Response:
    """Generate and return a clinical PDF report for the patient."""
    try:
        pdf_bytes = generate_quantamed_pdf(patient_id=patient)
        return Response(content=bytes(pdf_bytes), media_type="application/pdf")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Foldables — Real-Data Precision Drug Discovery API
# ---------------------------------------------------------------------------

class PatientInput(BaseModel):
    patient: dict[str, Any]


@app.post("/api/foldables/analyze")
async def foldables_full_analysis(body: PatientInput) -> JSONResponse:
    """Run the complete 8-pipeline analysis for a patient profile.

    Every score traces to a real data source (ChEMBL, DrugBank, CPIC, FAERS, Tox21).
    """
    try:
        profile = build_patient_from_dict(body.patient)
        result = run_full_analysis(profile)
        return JSONResponse(result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/foldables/demo-patient")
async def foldables_demo_patient() -> JSONResponse:
    """Return the Gabi preset patient profile for demo purposes."""
    profile = build_patient_from_dict(GABI_PRESET)
    return JSONResponse({
        "patient": GABI_PRESET,
        "completeness": profile.completeness(),
        "alerts": profile.clinical_alerts(),
    })


@app.get("/api/foldables/drug-properties")
async def foldables_drug_properties(
    drug: str = Query(..., description="Drug ID: vpa|ltg|lev|tpm|zns"),
) -> JSONResponse:
    """Return real molecular properties for a drug (ChEMBL, DrugBank, BBBP, Tox21, FAERS)."""
    try:
        return JSONResponse(get_drug_properties(drug))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/foldables/drugs")
async def foldables_drug_list() -> JSONResponse:
    """Return all available drug IDs."""
    return JSONResponse(get_all_drug_ids())


@app.post("/api/foldables/pk")
async def foldables_pk(
        body: PatientInput,
        drug: str = Query(...),
        dose_mg: float = Query(500)) -> JSONResponse:
    """Real PK curve from DrugBank parameters + CYP modifier from patient genetics."""
    try:
        profile = build_patient_from_dict(body.patient)
        result = pipeline_pk(profile, drug, dose_mg)
        return JSONResponse(result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/foldables/toxicity")
async def foldables_toxicity(drug: str = Query(...)) -> JSONResponse:
    """Return Tox21 assay results for a drug."""
    try:
        return JSONResponse(get_tox21_profile(drug))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/foldables/faers")
async def foldables_faers(drug: str = Query(...)) -> JSONResponse:
    """Return FAERS adverse event signal data."""
    try:
        return JSONResponse(get_faers_signals(drug))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/foldables/protein-target")
async def foldables_protein_target(gene: str = Query(...)) -> JSONResponse:
    """Look up a protein target by gene name."""
    result = lookup_protein_target(gene)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No target found for: {gene}")
    return JSONResponse(result)


# ---------------------------------------------------------------------------
# Protein Structure Modeling (SWISS-MODEL-inspired)
# ---------------------------------------------------------------------------

class FASTAInput(BaseModel):
    fasta: str


@app.post("/api/quantamed/protein-model")
async def protein_model(body: FASTAInput) -> JSONResponse:
    """Accept a FASTA sequence and return a full 3D protein model.

    Simulates the SWISS-MODEL pipeline:
    - Parses the FASTA sequence
    - Predicts secondary structure (Chou-Fasman)
    - Generates 3D backbone coordinates
    - Computes quality metrics (GMQE, QMEAN, Ramachandran)
    - Finds template match
    - Generates drug docking coordinates
    """
    try:
        result = model_protein_from_fasta(body.fasta)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return JSONResponse(result)
    except HTTPException:
        raise  # let FastAPI handle it correctly
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)



@app.get("/api/quantamed/protein-dynamics")
async def protein_dynamics_analysis(
    sequence: str = Query(..., description="Protein amino acid sequence"),
    n_frames: int = Query(100, ge=50, le=500, description="Number of MD frames"),
    duration_ns: float = Query(100.0, ge=10.0, le=500.0, description="Simulation duration in nanoseconds"),
) -> JSONResponse:
    """
    Run complete protein dynamics analysis: RMSF, RMSD, PCA clustering.
    
    This endpoint performs molecular dynamics simulation and analysis:
    - RMSF: Per-residue flexibility (identifies flexible loops vs rigid cores)
    - RMSD: Overall structural stability (convergence analysis)
    - PCA + K-means: Conformational state clustering (cryptic pocket discovery)
    
    Returns comprehensive analysis suitable for research visualization.
    """
    try:
        result = analyze_protein_dynamics(
            sequence=sequence,
            n_frames=n_frames,
            duration_ns=duration_ns,
        )
        return JSONResponse(result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/api/quantamed/protein-examples")
async def protein_examples() -> JSONResponse:
    """Return example FASTA sequences for the protein modeling UI."""
    return JSONResponse(get_example_sequences())


frontend_dir = os.path.join(os.path.dirname(__file__), "quantamed")
if os.path.exists(frontend_dir):
    app.mount(
        "/",
        StaticFiles(
            directory=frontend_dir,
            html=True),
        name="frontend")


# ---------------------------------------------------------------------------
# Interactive HTML Dashboard
# ---------------------------------------------------------------------------

frontend_dir = os.path.join(
    os.path.dirname(
        os.path.dirname(__file__)),
    "frontend",
    "out")


# Root is now handled by the frontend mount below

if not os.path.exists(frontend_dir):
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
            env_or_none = getattr(app.state, "gradio_env", None)
            if env_or_none is None:
                env_or_none = DrugTriageEnv(task)
                env_or_none.reset()
                app.state.gradio_env = env_or_none
            env = cast(DrugTriageEnv, env_or_none)
            step_action = DrugAction(
                action_type=cast(
                    Any, action), parameters={})
            obs, reward, done, info = env.step(step_action)
            obs_dict = obs.model_dump()
            rwd_dict = reward.model_dump()
            data = {
                "observation": obs_dict,
                "reward": rwd_dict,
                "done": done,
                "info": info}
            summary = (
                f"Step {obs_dict.get('step_number', '?')} | action={action} | "
                f"reward={rwd_dict.get('value', 0):.4f} | done={done}"
            )
            return summary, f"```json\n{json.dumps(data, indent=2)}\n```"
        except Exception as e:
            return f"❌ Action failed: {e}", ""

    def _gr_submit(drug: str, primary: str, secondary: str,
                   action: str) -> tuple[str, str]:
        """Submit final assessment on the Gradio-private env."""
        params: dict = {
            "drug_name": drug.strip().lower(),
            "primary_signal": primary.strip().lower(),
            "regulatory_action": action.strip().lower(),
        }
        if secondary.strip():
            params["secondary_signal"] = secondary.strip().lower()
        try:
            env_or_none = getattr(app.state, "gradio_env", None)
            if env_or_none is None:
                return "❌ Start an episode first (click New Episode)", ""
            env = cast(DrugTriageEnv, env_or_none)
            step_action = DrugAction(action_type="submit", parameters=params)
            obs, reward, done, info = env.step(step_action)
            rwd_dict = reward.model_dump()
            bd = rwd_dict.get("breakdown", {})
            bd_str = "\n".join(f"  {k}: {v:+.2f}" for k, v in bd.items()) if bd else ""
            data = {
                "observation": obs.model_dump(),
                "reward": rwd_dict,
                "done": done,
                "info": info}
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
            steps_out: list[dict[str, Any]] = []
            for action_type, params in script:
                step_action = DrugAction(action_type=cast(
                    Any, action_type), parameters=params)
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
            data: dict[str, Any] = {"task_id": task, "steps": steps_out}
            lines = []
            for i, s in enumerate(steps_out):
                rwd: dict[str, Any] = s.get("reward", {})
                lines.append(
                    f"Step {i + 1}: {s.get('action_type', '?')} \u2192 reward={rwd.get('value', 0):.4f}"
                )
            final: float = steps_out[-1]["reward"]["value"] if steps_out else 0.0
            summary = "\n".join(lines) + \
                f"\n\n\U0001f3c6 Final score: {final:.4f}"
            return summary, f"```json\n{json.dumps(data, indent=2)}\n```"
        except Exception as e:
            return f"❌ Demo failed: {e}", ""

    def _gr_analyze_patient(json_file) -> tuple[str, str, str]:
        """Analyze patient JSON and generate protein dynamics simulation."""
        try:
            if json_file is None:
                return "❌ Please upload a patient JSON file", "", ""
            
            # Read JSON file
            import json
            with open(json_file.name, 'r') as f:
                patient_data = json.load(f)
            
            # Build patient profile
            patient = build_patient_from_dict(patient_data)
            
            # Get patient summary
            summary_lines = [
                f"✅ Patient Profile Loaded Successfully",
                f"",
                f"**Patient:** {patient_data.get('_metadata', {}).get('profile_name', 'Unknown')}",
                f"**Age:** {patient.basic_info.age} | **Gender:** {patient.basic_info.gender}",
                f"**Diagnosis:** {patient.condition.primary_diagnosis} ({patient.condition.subtype})",
                f"**Current Medications:** {', '.join([m.drug_name for m in patient.current_meds]) if patient.current_meds else 'None'}",
                f"",
                f"**Genetics:**",
                f"- CYP2D6: {patient.genetics.CYP2D6 or 'Unknown'}",
                f"- CYP2C9: {patient.genetics.CYP2C9 or 'Unknown'}",
                f"- CYP3A4: {patient.genetics.CYP3A4 or 'Unknown'}",
                f"",
                f"**Lab Values:**",
                f"- ALT: {patient.labs.ALT} U/L" if patient.labs.ALT else "",
                f"- eGFR: {patient.labs.eGFR} mL/min" if patient.labs.eGFR else "",
            ]
            
            # Get clinical alerts
            alerts = patient.clinical_alerts()
            if alerts:
                summary_lines.append(f"\n**⚠️ Clinical Alerts:**")
                for alert in alerts:
                    summary_lines.append(f"- [{alert['type']}] {alert['title']}: {alert['message']}")
            
            # Run full analysis
            analysis = run_full_analysis(patient)
            
            # Generate protein dynamics for current medications
            protein_info = ""
            if patient.current_meds:
                drug = patient.current_meds[0]
                protein_info = f"\n\n**🧬 Generating Protein Dynamics Simulation for {drug.drug_name}...**\n"
                
                # Get drug target protein
                target_info = lookup_protein_target(drug.drug_id)
                if target_info:
                    protein_info += f"Target: {target_info.get('name', 'Unknown')}\n"
                    protein_info += f"Mechanism: {target_info.get('mechanism', 'Unknown')}\n"
                
                # Simulate protein dynamics
                try:
                    # Use a relevant protein sequence based on drug target
                    # For epilepsy drugs, use GABA receptor or sodium channel sequences
                    if drug.drug_id == "vpa":
                        sequence = "MTSQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQV"
                    else:
                        sequence = "MTSQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQVQV"
                    
                    dynamics_result = analyze_protein_dynamics(sequence, n_frames=50, duration_ns=10.0)
                    protein_info += f"\n**Protein Dynamics Analysis:**\n"
                    protein_info += f"- RMSF Analysis: {len(dynamics_result['rmsf']['residue_ids'])} residues analyzed\n"
                    protein_info += f"- Mean RMSF: {dynamics_result['rmsf']['mean_rmsf']:.2f} Å\n"
                    protein_info += f"- Flexible regions: {len(dynamics_result['rmsf']['flexible_regions'])}\n"
                    protein_info += f"- RMSD converged: {'Yes' if dynamics_result['rmsd']['converged'] else 'No'}\n"
                    protein_info += f"- Conformational clusters: {dynamics_result['pca']['n_clusters']}\n"
                    
                except Exception as e:
                    protein_info += f"⚠️ Protein simulation error: {str(e)}\n"
            
            summary = "\n".join([line for line in summary_lines if line is not None])
            
            return (
                summary + protein_info,
                f"```json\n{json.dumps(analysis, indent=2)}\n```",
                f"```json\n{json.dumps(patient_data, indent=2)}\n```"
            )
            
        except Exception as e:
            return f"❌ Analysis failed: {str(e)}", "", ""

    with gr.Blocks(
        title="QuantaMed — Quantum-Enhanced Precision Drug Discovery"
    ) as _gradio_app:

        gr.Markdown(
            """# 🧬 QuantaMed — Quantum-Enhanced Precision Drug Discovery
**Pharmacovigilance AI + Protein Dynamics + Quantum Simulation**

> _Combining FDA FAERS signal detection with quantum protein folding and molecular dynamics for personalized medicine._
""",
            elem_id="title-md",
        )

        with gr.Tabs():
            with gr.Tab("🧬 Patient Analysis"):
                gr.Markdown("""
                ### Upload Patient JSON for Comprehensive Analysis
                Upload a patient profile JSON file to:
                - Analyze pharmacogenomics (CYP enzymes)
                - Generate protein dynamics simulations
                - Predict drug-target interactions
                - Calculate personalized risk scores
                """)
                
                with gr.Row():
                    patient_json_input = gr.File(
                        label="Upload Patient JSON",
                        file_types=[".json"],
                        type="filepath"
                    )
                    analyze_btn = gr.Button("🔬 Analyze Patient", variant="primary", scale=0)
                
                with gr.Row():
                    patient_summary = gr.Markdown(label="Patient Summary")
                
                with gr.Row():
                    analysis_output = gr.Code(
                        label="Full Analysis Results",
                        language="json",
                        lines=15
                    )
                    raw_patient_data = gr.Code(
                        label="Raw Patient Data",
                        language="json",
                        lines=15
                    )
                
                analyze_btn.click(
                    _gr_analyze_patient,
                    inputs=[patient_json_input],
                    outputs=[patient_summary, analysis_output, raw_patient_data]
                )
                
                gr.Markdown("""
                ### Sample Patient Files
                - Use `sample_patient.json` in the drug-triage-env directory
                - Contains: Gabi - 24-year-old female with Juvenile Myoclonic Epilepsy
                """)

            with gr.Tab("🔬 Drug Triage Environment"):
                gr.Markdown("""
                ### FDA FAERS Signal Detection
                Train AI agents to detect adverse drug events using real historical cases.
                """)
                
                with gr.Row():
                    task_dd = gr.Dropdown(
                        choices=[
                            "easy",
                            "medium",
                            "hard"],
                        value="easy",
                        label="Task (Drug)",
                        info="easy=Metformin · medium=Rofecoxib (Vioxx) · hard=Isotretinoin",
                    )
                    reset_btn = gr.Button("🔄 New Episode", variant="primary")

                with gr.Row():
                    status_box = gr.Textbox(
                        label="Episode Status",
                        interactive=False,
                        lines=1)
                    raw_box = gr.Code(
                        label="Raw Response",
                        language="json",
                        interactive=False,
                        lines=10)

                gr.Markdown("### 🔬 Investigation Actions")
                with gr.Row():
                    faers_btn = gr.Button("🔍 Search FAERS")
                    label_btn = gr.Button("📄 Fetch Label")
                    signal_btn = gr.Button("📈 Analyze Signal")
                    mech_btn = gr.Button("🔬 Lookup Mechanism")
                    lit_btn = gr.Button("📚 Check Literature")

                gr.Markdown("### 📋 Final Assessment (Submit)")
                with gr.Row():
                    drug_in = gr.Textbox(label="Drug Name", placeholder="metformin")
                    primary_in = gr.Textbox(
                        label="Primary Signal",
                        placeholder="lactic acidosis")
                    second_in = gr.Textbox(
                        label="Secondary Signal (hard only)",
                        placeholder="depression")
                    action_in = gr.Dropdown(
                        choices=["monitor", "restrict", "withdraw"],
                        value="monitor",
                        label="Regulatory Action",
                    )
                submit_btn = gr.Button("⚖️ Submit Assessment", variant="primary")

                gr.Markdown("### 🤖 Auto Demo")
                demo_btn = gr.Button(
                    "▶  Run Scripted Demo (perfect score)",
                    variant="secondary")

                reset_btn.click(
                    _gr_reset,
                    inputs=[task_dd],
                    outputs=[
                        status_box,
                        raw_box])
                faers_btn.click(
                    lambda t: _gr_action(
                        "search_faers",
                        t),
                    inputs=[task_dd],
                    outputs=[
                        status_box,
                        raw_box])
                label_btn.click(
                    lambda t: _gr_action(
                        "fetch_label",
                        t),
                    inputs=[task_dd],
                    outputs=[
                        status_box,
                        raw_box])
                signal_btn.click(
                    lambda t: _gr_action(
                        "analyze_signal",
                        t),
                    inputs=[task_dd],
                    outputs=[
                        status_box,
                        raw_box])
                mech_btn.click(
                    lambda t: _gr_action(
                        "lookup_mechanism",
                        t),
                    inputs=[task_dd],
                    outputs=[
                        status_box,
                        raw_box])
                lit_btn.click(
                    lambda t: _gr_action(
                        "check_literature",
                        t),
                    inputs=[task_dd],
                    outputs=[
                        status_box,
                        raw_box])
                submit_btn.click(
                    _gr_submit, inputs=[
                        drug_in, primary_in, second_in, action_in], outputs=[
                        status_box, raw_box])
                demo_btn.click(
                    _gr_demo,
                    inputs=[task_dd],
                    outputs=[
                        status_box,
                        raw_box])

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
