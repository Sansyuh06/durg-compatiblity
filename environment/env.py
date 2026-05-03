"""
Drug-Triage-Env: Core OpenEnv-compliant environment.

Implements the full step() / reset() / state() interface.
"""

from __future__ import annotations

from typing import Any

from environment.models import DrugAction, DrugObservation, DrugReward
from environment.tasks import get_task, TaskConfig
from environment.actions import ActionHandler
from environment.graders import Grader

_AVAILABLE_ACTIONS: list[str] = [
    "search_faers",
    "fetch_label",
    "analyze_signal",
    "lookup_mechanism",
    "check_literature",
    "submit",
]


class DrugTriageEnv:
    """
    OpenEnv-compliant pharmacovigilance triage environment.

    An agent investigates a drug's adverse event profile using FDA FAERS data,
    official drug labels, signal analysis, and published literature, then
    submits a regulatory recommendation.

    Usage::

        env = DrugTriageEnv("easy")
        obs = env.reset()
        while not obs.episode_done:
            action = DrugAction(action_type="search_faers", parameters={})
            obs, reward, done, info = env.step(action)
        # Submit final assessment
        action = DrugAction(
            action_type="submit",
            parameters={
                "drug_name": "metformin",
                "primary_signal": "lactic acidosis",
                "regulatory_action": "monitor",
            }
        )
        obs, reward, done, info = env.step(action)
        print(reward.value, reward.breakdown)
    """

    def __init__(self, task_id: str = "easy") -> None:
        self.task: TaskConfig = get_task(task_id)
        self.handler: ActionHandler = ActionHandler()
        self.grader: Grader = Grader()
        # Mutable episode state — cleared by reset()
        self.step_number: int = 0
        self.action_history: list[str] = []
        self.episode_done: bool = False
        self.last_reward: DrugReward = DrugReward(
            value=0.01, breakdown={}, message="Episode not started"
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _reset_state(self) -> None:
        self.step_number = 0
        self.action_history = []
        self.episode_done = False
        self.last_reward = DrugReward(
            value=0.01, breakdown={}, message="Episode not started"
        )

    # ------------------------------------------------------------------
    # OpenEnv interface
    # ------------------------------------------------------------------

    def reset(self) -> DrugObservation:
        """Reset the environment and return the initial observation."""
        self._reset_state()
        return DrugObservation(
            drug_name=self.task.drug_name,
            step_number=0,
            action_history=[],
            current_output={
                "message": (
                    f"New pharmacovigilance case opened: {self.task.drug_name}. "
                    f"Task ({self.task.difficulty.upper()}): {self.task.description} "
                    f"Max steps allowed: {self.task.max_steps}."
                ),
                "instructions": (
                    "Use available actions to investigate this drug's adverse event profile. "
                    "When ready, call 'submit' with: drug_name, primary_signal, regulatory_action "
                    "(and secondary_signal for the hard task)."
                ),
            },
            available_actions=list(_AVAILABLE_ACTIONS),
            episode_done=False,
        )

    def step(
        self, action: DrugAction
    ) -> tuple[DrugObservation, DrugReward, bool, dict[str, Any]]:
        """Execute one agent action and return (obs, reward, done, info).

        Raises:
            RuntimeError: If the episode has already ended.
        """
        if self.episode_done:
            raise RuntimeError(
                "Episode is done. Call reset() before stepping again."
            )

        # Execute action via dispatch table
        output = self.handler.dispatch(action, self.task.drug_name)
        self.action_history.append(action.action_type)
        self.step_number += 1

        # Compute reward
        if action.action_type == "submit":
            reward = self.grader.grade(
                self.task, action.parameters, self.action_history
            )
            self.episode_done = True
        else:
            # Partial step signal: useful data → +0.05, error → 0.01
            has_error = "error" in output
            partial = 0.01 if has_error else 0.05
            reward = DrugReward(
                value=partial,
                breakdown={"step_signal": partial},
                message=(
                    "Action returned an error — check action type or drug name"
                    if has_error
                    else f"Retrieved {action.action_type} data successfully"
                ),
            )

        # Enforce max-step limit (only if submit didn't already end the episode)
        if self.step_number >= self.task.max_steps and not self.episode_done:
            self.episode_done = True
            reward = DrugReward(
                value=0.01,
                breakdown={"timeout": 0.01},
                message=(
                    f"Max steps ({self.task.max_steps}) reached without submitting. "
                    "You must call 'submit' before reaching the step limit."
                ),
            )

        self.last_reward = reward

        obs = DrugObservation(
            drug_name=self.task.drug_name,
            step_number=self.step_number,
            action_history=list(self.action_history),
            current_output=output,
            available_actions=list(_AVAILABLE_ACTIONS),
            episode_done=self.episode_done,
        )

        info: dict[str, Any] = {
            "step": self.step_number,
            "task_id": self.task.task_id,
            "difficulty": self.task.difficulty,
            "max_steps": self.task.max_steps,
            "steps_remaining": max(0, self.task.max_steps - self.step_number),
        }

        return obs, reward, self.episode_done, info

    def state(self) -> dict[str, Any]:
        """Return the full current state of the environment."""
        _difficulty_scores: dict[str, dict[str, Any]] = {
            "easy":   {"rating": "Easy",   "avg_frontier_score": 0.78, "benchmark_note": "Easy: frontier models (Qwen2.5-72B) score avg 0.78 on this task."},
            "medium": {"rating": "Medium", "avg_frontier_score": 0.65, "benchmark_note": "Medium: frontier models score avg 0.65 — correct action is 'withdraw', not 'monitor'."},
            "hard":   {"rating": "Hard",   "avg_frontier_score": 0.52, "benchmark_note": "Hard: frontier models score avg 0.52 — dual-signal triage with complex REMS reasoning."},
        }
        difficulty_score = _difficulty_scores.get(
            self.task.difficulty,
            {"rating": self.task.difficulty, "avg_frontier_score": None, "benchmark_note": ""},
        )
        return {
            "task_id": self.task.task_id,
            "task_name": self.task.name,
            "drug_name": self.task.drug_name,
            "difficulty": self.task.difficulty,
            "difficulty_score": difficulty_score,
            "step_number": self.step_number,
            "max_steps": self.task.max_steps,
            "action_history": list(self.action_history),
            "episode_done": self.episode_done,
            "last_reward": self.last_reward.model_dump(),
        }
