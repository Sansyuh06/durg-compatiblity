"""
Drug-Triage-Env: Baseline inference script.

Runs all three tasks sequentially using an LLM via the OpenAI-compatible
Hugging Face Inference Router API.

Mandatory stdout format:
  [START] task=<id> env=drug-triage-env model=<name>
  [STEP]  step=<n> action=<type> reward=<f> done=<bool> error=<msg|null>
  [END]   success=<bool> steps=<n> score=<f> rewards=<csv>

Usage:
  export HF_TOKEN=hf_...
  export API_BASE_URL=https://router.huggingface.co/v1   # default
  export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct            # default
  python inference.py
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from openai import OpenAI

from environment.env import DrugTriageEnv
from environment.models import DrugAction
from environment.tasks import TASKS

# ---------------------------------------------------------------------------
# Configuration — read from environment variables
# ---------------------------------------------------------------------------

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    print("ERROR: HF_TOKEN environment variable is not set.", flush=True)
    sys.exit(1)

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

# OpenAI client pointed at the HF router
client = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)

SYSTEM_PROMPT = """You are an expert pharmacovigilance agent reviewing FDA FAERS adverse event data.
Your goal is to investigate a drug, identify the primary safety signal, and recommend a regulatory action.

At each step you receive an observation JSON. Respond ONLY with a valid JSON object containing:
  - "action_type": one of ["search_faers", "fetch_label", "analyze_signal", "lookup_mechanism", "check_literature", "submit"]
  - "parameters": dict (empty {} for all non-submit actions)

For the "submit" action, parameters must include:
  - "drug_name": the drug name (lowercase)
  - "primary_signal": the primary adverse event signal (lowercase, descriptive)
  - "regulatory_action": one of ["monitor", "withdraw", "restrict"]
  - "secondary_signal": (only for hard task) secondary adverse event signal

Investigation strategy:
1. Start with search_faers to see the adverse event profile
2. Use analyze_signal to check PRR/ROR signal strength
3. Use fetch_label to check black box warnings and current status
4. Use check_literature or lookup_mechanism for deeper insight
5. Submit your final assessment

No explanation. No markdown. No code fences. Raw JSON only.
Example: {"action_type": "search_faers", "parameters": {}}"""


# ---------------------------------------------------------------------------
# Logging helpers — mandatory format
# ---------------------------------------------------------------------------

def log_start(task_id: str, model: str) -> None:
    print(f"[START] task={task_id} env=drug-triage-env model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: str) -> None:
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} "
        f"done={str(done).lower()} error={error}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: list[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------

def get_llm_action(observation: dict[str, Any], step: int) -> DrugAction:
    """Ask the LLM for the next action. Falls back to submit on parse error."""
    user_content = (
        f"Step {step}. Current observation:\n"
        f"{json.dumps(observation, indent=2, default=str)}\n\n"
        "What is your next action? Reply with raw JSON only."
    )
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=300,
            temperature=0.1,
        )
        raw: str = (response.choices[0].message.content or "").strip()

        # Strip markdown fences if model ignores instructions
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        action_data: dict[str, Any] = json.loads(raw)
        return DrugAction(
            action_type=action_data.get("action_type", "submit"),
            parameters=action_data.get("parameters", {}),
        )
    except Exception as exc:
        print(f"[DEBUG] LLM parse error at step {step}: {exc}", flush=True)
        # Graceful fallback — end episode cleanly
        return DrugAction(action_type="submit", parameters={})


# ---------------------------------------------------------------------------
# Run a single task episode
# ---------------------------------------------------------------------------

def run_task(task_id: str) -> None:
    """Run one full episode of a given task and emit mandatory log lines."""
    env = DrugTriageEnv(task_id)
    obs = env.reset()

    rewards: list[float] = []
    steps: int = 0
    error_msg: str = "null"
    success: bool = False

    log_start(task_id, MODEL_NAME)

    try:
        while not obs.episode_done:
            step_num = env.step_number + 1
            action = get_llm_action(obs.model_dump(), step_num)

            obs, reward, done, info = env.step(action)
            steps += 1
            rewards.append(reward.value)

            step_error = error_msg if error_msg != "null" else "null"
            log_step(
                step=steps,
                action=action.action_type,
                reward=reward.value,
                done=done,
                error=step_error,
            )
            error_msg = "null"

            if done:
                success = reward.value >= 0.5
                break

    except Exception as exc:
        error_msg = str(exc).replace("\n", " ")[:200]
        print(f"[DEBUG] Episode error: {error_msg}", flush=True)
        success = False

    finally:
        avg_score = sum(rewards) / len(rewards) if rewards else 0.0
        final_score = min(0.99, max(0.01, avg_score))
        log_end(
            success=success,
            steps=steps,
            score=final_score,
            rewards=rewards,
        )


# ---------------------------------------------------------------------------
# Main — run all 3 tasks
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all three tasks sequentially and emit evaluation logs."""
    print(f"[INFO] Starting Drug-Triage-Env baseline inference", flush=True)
    print(f"[INFO] Model: {MODEL_NAME}", flush=True)
    print(f"[INFO] API Base: {API_BASE_URL}", flush=True)
    print("", flush=True)

    for task in TASKS:
        run_task(task.task_id)
        print("", flush=True)

    print("[INFO] All 3 tasks completed.", flush=True)


if __name__ == "__main__":
    main()
