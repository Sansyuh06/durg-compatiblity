"""
Drug-Triage-Env: Task definitions.

Three tasks of increasing difficulty, each targeting a real drug with a
historically documented serious adverse event signal from FDA FAERS.
"""

from __future__ import annotations

from environment.models import TaskConfig


TASKS: list[TaskConfig] = [
    # ------------------------------------------------------------------ EASY
    TaskConfig(
        task_id="easy",
        name="Metformin — Lactic Acidosis Signal",
        description=(
            "Investigate METFORMIN, a widely-prescribed biguanide antidiabetic, "
            "for a known serious adverse event signal that is well-characterized "
            "in the FDA FAERS database. Query FAERS for adverse event reports, "
            "review the FDA label, and determine: (1) the primary safety signal, "
            "and (2) the appropriate regulatory action. "
            "Submit your findings as: drug_name, primary_signal, regulatory_action."
        ),
        difficulty="easy",
        drug_name="METFORMIN",
        ground_truth={
            "drug_name": "metformin",
            "primary_signal": "lactic acidosis",
            "regulatory_action": "monitor",
        },
        max_steps=5,
    ),

    # ---------------------------------------------------------------- MEDIUM
    TaskConfig(
        task_id="medium",
        name="Rofecoxib (Vioxx) — Cardiovascular Crisis",
        description=(
            "Investigate ROFECOXIB (Vioxx), a COX-2 selective NSAID, for a "
            "critical cardiovascular safety signal identified in post-marketing "
            "surveillance. The APPROVE trial (2004) confirmed a 1.92x elevated "
            "relative risk of serious thrombotic cardiovascular events. "
            "Query FAERS, analyze the signal strength (PRR/ROR), review the "
            "mechanism, and determine the correct regulatory action. "
            "Submit: drug_name, primary_signal, regulatory_action."
        ),
        difficulty="medium",
        drug_name="ROFECOXIB",
        ground_truth={
            "drug_name": "rofecoxib",
            "primary_signal": "myocardial infarction",
            "regulatory_action": "withdraw",
        },
        max_steps=8,
    ),

    # ------------------------------------------------------------------ HARD
    TaskConfig(
        task_id="hard",
        name="Isotretinoin (Accutane) — Multi-Signal Triage",
        description=(
            "Investigate ISOTRETINOIN, a severe acne treatment with iPLEDGE REMS, "
            "for two concurrent serious adverse event signals requiring complex "
            "regulatory decision-making: a near-certain teratogenic risk and an "
            "emerging psychiatric/depression signal. "
            "Use all available investigation tools. Determine the primary AND "
            "secondary signals, and whether market restriction (existing REMS), "
            "withdrawal, or enhanced monitoring is sufficient. "
            "Submit: drug_name, primary_signal, secondary_signal, regulatory_action."
        ),
        difficulty="hard",
        drug_name="ISOTRETINOIN",
        ground_truth={
            "drug_name": "isotretinoin",
            "primary_signal": "teratogenicity",
            "secondary_signal": "depression",
            "regulatory_action": "restrict",
        },
        max_steps=12,
    ),
]


def get_task(task_id: str) -> TaskConfig:
    """Look up a task by ID.

    Raises:
        ValueError: If *task_id* does not match any defined task.
    """
    for task in TASKS:
        if task.task_id == task_id:
            return task
    valid_ids = ", ".join(t.task_id for t in TASKS)
    raise ValueError(f"Task '{task_id}' not found. Valid IDs: {valid_ids}")
