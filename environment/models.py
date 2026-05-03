"""
Drug-Triage-Env: Pydantic v2 typed models.

Defines the complete data contract for the pharmacovigilance triage environment.
All classes imported by the rest of the package; this module imports nothing else
from the environment package to avoid circular imports.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DrugObservation(BaseModel):
    """What the pharmacovigilance agent sees after each action."""

    model_config = ConfigDict(strict=False)

    drug_name: str
    step_number: int = 0
    action_history: list[str] = Field(default_factory=list)
    current_output: dict[str, Any] = Field(default_factory=dict)
    available_actions: list[str] = Field(
        default_factory=lambda: [
            "search_faers",
            "fetch_label",
            "analyze_signal",
            "lookup_mechanism",
            "check_literature",
            "submit",
        ]
    )
    episode_done: bool = False


class DrugAction(BaseModel):
    """An action the pharmacovigilance agent wants to take.

    action_type options:
        search_faers      — Query FDA FAERS adverse event reports
        fetch_label       — Retrieve official FDA drug labeling
        analyze_signal    — Run disproportionality analysis (PRR/ROR/IC)
        lookup_mechanism  — Look up the drug's pharmacological mechanism
        check_literature  — Search published safety literature
        submit            — Submit final signal assessment and recommendation
    """

    model_config = ConfigDict(strict=False)

    action_type: Literal[
        "search_faers",
        "fetch_label",
        "analyze_signal",
        "lookup_mechanism",
        "check_literature",
        "submit",
    ]
    parameters: dict[str, Any] = Field(default_factory=dict)


class DrugReward(BaseModel):
    """Reward returned after each step, with a human-readable breakdown.

    Value is strictly clamped to the open interval (0.01, 0.99) to
    guard against edge-case leakage at 0.0 or 1.0.
    """

    model_config = ConfigDict(strict=False)

    value: float = Field(gt=0.0, lt=1.0, default=0.01)
    breakdown: dict[str, float] = Field(default_factory=dict)
    message: str = ""

    @field_validator("value", mode="before")
    @classmethod
    def clamp_value(cls, v: float) -> float:
        """Strictly enforce (0.01, 0.99) — never touch 0.0 or 1.0."""
        return min(0.99, max(0.01, float(v)))


class TaskConfig(BaseModel):
    """Definition of a single graded pharmacovigilance task."""

    model_config = ConfigDict(strict=False)

    task_id: str
    name: str
    description: str
    difficulty: Literal["easy", "medium", "hard"]
    drug_name: str
    ground_truth: dict[str, Any]
    max_steps: int = 10
