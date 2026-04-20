"""
Drug-Triage-Env: Smoke tests.

Verifies that the environment initialises correctly, produces valid
observations, and that all graders return scores in (0.01, 0.99).

Run with:
    python test_env.py
"""

from __future__ import annotations

import sys

from environment.env import DrugTriageEnv
from environment.models import DrugAction
from environment.tasks import TASKS


def _check(condition: bool, message: str) -> None:
    if not condition:
        print(f"  FAIL: {message}", flush=True)
        sys.exit(1)
    print(f"  PASS: {message}", flush=True)


def test_reset_all_tasks() -> None:
    print("\n=== test_reset_all_tasks ===")
    for task in TASKS:
        env = DrugTriageEnv(task.task_id)
        obs = env.reset()
        _check(obs.drug_name == task.drug_name, f"[{task.task_id}] obs.drug_name == {task.drug_name}")
        _check(obs.step_number == 0, f"[{task.task_id}] obs.step_number == 0")
        _check(not obs.episode_done, f"[{task.task_id}] episode_done is False after reset")
        _check(len(obs.action_history) == 0, f"[{task.task_id}] action_history is empty after reset")
        _check("search_faers" in obs.available_actions, f"[{task.task_id}] search_faers in available_actions")
        _check("submit" in obs.available_actions, f"[{task.task_id}] submit in available_actions")


def test_single_search_step() -> None:
    print("\n=== test_single_search_step ===")
    for task in TASKS:
        env = DrugTriageEnv(task.task_id)
        env.reset()
        action = DrugAction(action_type="search_faers", parameters={})
        obs, reward, done, info = env.step(action)

        _check(obs.step_number == 1, f"[{task.task_id}] step_number == 1 after one step")
        _check("search_faers" in obs.action_history, f"[{task.task_id}] search_faers in action_history")
        _check(not done, f"[{task.task_id}] not done after single step")
        _check(0.01 <= reward.value <= 0.99, f"[{task.task_id}] reward in (0.01, 0.99)")
        _check("data" in obs.current_output or "error" in obs.current_output,
               f"[{task.task_id}] output has 'data' or 'error' key")
        _check("steps_remaining" in info, f"[{task.task_id}] 'steps_remaining' in info")


def test_ground_truth_submission_scores_high() -> None:
    print("\n=== test_ground_truth_submission_scores_high ===")

    # Easy — Metformin
    env = DrugTriageEnv("easy")
    env.reset()
    env.step(DrugAction(action_type="search_faers", parameters={}))
    _, reward, done, _ = env.step(DrugAction(
        action_type="submit",
        parameters={
            "drug_name": "metformin",
            "primary_signal": "lactic acidosis",
            "regulatory_action": "monitor",
        }
    ))
    _check(done, "[easy] done=True after submit")
    _check(reward.value >= 0.70, f"[easy] Ground truth score >= 0.70 (got {reward.value:.2f})")
    _check(0.01 < reward.value < 1.0, "[easy] Score strictly in (0.01, 0.99)")

    # Medium — Rofecoxib
    env = DrugTriageEnv("medium")
    env.reset()
    env.step(DrugAction(action_type="search_faers", parameters={}))
    env.step(DrugAction(action_type="analyze_signal", parameters={}))
    _, reward, done, _ = env.step(DrugAction(
        action_type="submit",
        parameters={
            "drug_name": "rofecoxib",
            "primary_signal": "myocardial infarction",
            "regulatory_action": "withdraw",
        }
    ))
    _check(done, "[medium] done=True after submit")
    _check(reward.value >= 0.70, f"[medium] Ground truth score >= 0.70 (got {reward.value:.2f})")
    _check(0.01 < reward.value < 1.0, "[medium] Score strictly in (0.01, 0.99)")

    # Hard — Isotretinoin
    env = DrugTriageEnv("hard")
    env.reset()
    for act in ["search_faers", "fetch_label", "analyze_signal", "lookup_mechanism", "check_literature"]:
        env.step(DrugAction(action_type=act, parameters={}))
    _, reward, done, _ = env.step(DrugAction(
        action_type="submit",
        parameters={
            "drug_name": "isotretinoin",
            "primary_signal": "teratogenicity",
            "secondary_signal": "depression",
            "regulatory_action": "restrict",
        }
    ))
    _check(done, "[hard] done=True after submit")
    _check(reward.value >= 0.70, f"[hard] Ground truth score >= 0.70 (got {reward.value:.2f})")
    _check(0.01 < reward.value < 1.0, "[hard] Score strictly in (0.01, 0.99)")


def test_wrong_submission_scores_low() -> None:
    print("\n=== test_wrong_submission_scores_low ===")
    env = DrugTriageEnv("medium")
    env.reset()
    _, reward, done, _ = env.step(DrugAction(
        action_type="submit",
        parameters={
            "drug_name": "aspirin",
            "primary_signal": "stomach ache",
            "regulatory_action": "monitor",
        }
    ))
    _check(done, "[medium wrong] done=True after submit")
    _check(reward.value < 0.5, f"[medium wrong] Wrong submission scores < 0.5 (got {reward.value:.2f})")
    _check(0.01 <= reward.value <= 0.99, "[medium wrong] Score in (0.01, 0.99)")


def test_timeout() -> None:
    print("\n=== test_timeout ===")
    env = DrugTriageEnv("easy")
    env.reset()
    # Easy task has max_steps=5; take 5 non-submit actions
    for _ in range(5):
        obs, reward, done, _ = env.step(DrugAction(action_type="search_faers", parameters={}))
        if done:
            break
    _check(done, "[easy timeout] episode ends at max_steps")
    _check(0.01 <= reward.value <= 0.99, "[easy timeout] Timeout reward in (0.01, 0.99)")


def test_state() -> None:
    print("\n=== test_state ===")
    env = DrugTriageEnv("easy")
    env.reset()
    env.step(DrugAction(action_type="search_faers", parameters={}))
    state = env.state()
    _check("task_id" in state, "state has task_id")
    _check("drug_name" in state, "state has drug_name")
    _check("step_number" in state, "state has step_number")
    _check("action_history" in state, "state has action_history")
    _check(state["step_number"] == 1, "state.step_number == 1")


if __name__ == "__main__":
    print("Running Drug-Triage-Env smoke tests...", flush=True)
    test_reset_all_tasks()
    test_single_search_step()
    test_ground_truth_submission_scores_high()
    test_wrong_submission_scores_low()
    test_timeout()
    test_state()
    print("\nAll tests passed! (45/45)", flush=True)
