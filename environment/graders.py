"""
Drug-Triage-Env: Deterministic graders for all 3 tasks.

Each grader is:
  - Deterministic (same submission always scores the same)
  - Produces partial credit across multiple sub-criteria
  - Value strictly clamped to (0.01, 0.99)

Rubric summary:
  Easy   (Metformin):   drug_name 0.25 + primary_signal 0.30 + action 0.35 + efficiency +0.09
  Medium (Rofecoxib):   drug_name 0.20 + primary_signal 0.30 + action 0.30 + coverage 0.15 - redundancy
  Hard   (Isotretinoin): drug_name 0.15 + primary 0.25 + secondary 0.15 + action 0.25 + coverage +0.10 - overstep
"""

from __future__ import annotations

import re
from typing import Any

from environment.models import DrugReward, TaskConfig

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize(s: str) -> str:
    """Lowercase, strip whitespace and punctuation for fuzzy matching."""
    return re.sub(r"[^a-z0-9 ]", "", str(s).lower().strip())


def _match_drug_name(submitted: str, accepted: list[str]) -> bool:
    """Return True if the submitted drug name matches any accepted alias."""
    s = _normalize(submitted)
    if not s:
        return False
    return any(s == _normalize(a) or _normalize(a) in s or s in _normalize(a) for a in accepted)


def _match_signal(submitted: str, accepted_terms: list[str]) -> bool:
    """Return True if the submitted signal matches any accepted term (substring or full)."""
    s = _normalize(submitted)
    if not s:
        return False
    return any(_normalize(term) in s or s in _normalize(term) for term in accepted_terms)


def _match_action(submitted: str, accepted: list[str]) -> bool:
    """Return True if the submitted regulatory action matches any accepted form."""
    s = _normalize(submitted)
    if not s:
        return False
    return any(s == _normalize(a) or _normalize(a) in s or s in _normalize(a) for a in accepted)


# ---------------------------------------------------------------------------
# Main Grader class
# ---------------------------------------------------------------------------

class Grader:
    """Grades an agent's submission against the task's ground truth."""

    def grade(
        self,
        task: TaskConfig,
        submission: dict[str, Any],
        action_history: list[str],
    ) -> DrugReward:
        """Return a deterministic reward strictly in (0.01, 0.99)."""
        breakdown: dict[str, float] = {}
        messages: list[str] = []

        if task.difficulty == "easy":
            self._grade_easy(task.ground_truth, submission, action_history, breakdown, messages)
        elif task.difficulty == "medium":
            self._grade_medium(task.ground_truth, submission, action_history, breakdown, messages)
        elif task.difficulty == "hard":
            self._grade_hard(task.ground_truth, submission, action_history, breakdown, messages)
        else:
            breakdown["unknown_difficulty"] = 0.0
            messages.append(f"Unknown difficulty: {task.difficulty}")

        raw = sum(breakdown.values())
        clamped = min(0.99, max(0.01, raw))

        return DrugReward(
            value=clamped,
            breakdown=breakdown,
            message="; ".join(messages) if messages else "No scoring details.",
        )

    # ------------------------------------------------------------------
    # Easy: Metformin — Lactic Acidosis (0.25 + 0.30 + 0.35 + up to 0.09 bonus)
    # ------------------------------------------------------------------

    @staticmethod
    def _grade_easy(
        gt: dict[str, Any],
        sub: dict[str, Any],
        history: list[str],
        bd: dict[str, float],
        msgs: list[str],
    ) -> None:

        # ---- drug_name (0.25) ----
        drug_aliases = ["metformin", "glucophage", "metformin hydrochloride"]
        if _match_drug_name(str(sub.get("drug_name", "")), drug_aliases):
            bd["drug_name"] = 0.25
            msgs.append("Drug name correct — metformin (+0.25)")
        else:
            bd["drug_name"] = 0.0
            msgs.append(f"Drug name incorrect (got '{sub.get('drug_name', '')}', expected 'metformin')")

        # ---- primary_signal (0.30) ----
        signal_aliases = [
            "lactic acidosis", "lacticacidosis", "lactic acid", "lactic acidaemia",
            "metformin associated lactic acidosis",
        ]
        if _match_signal(str(sub.get("primary_signal", "")), signal_aliases):
            bd["primary_signal"] = 0.30
            msgs.append("Primary signal correct — lactic acidosis (+0.30)")
        else:
            bd["primary_signal"] = 0.0
            msgs.append(
                f"Primary signal incorrect (got '{sub.get('primary_signal', '')}', "
                "expected 'lactic acidosis')"
            )

        # ---- regulatory_action (0.35) ----
        action_aliases = [
            "monitor", "monitoring", "regulatory monitoring",
            "enhanced monitoring", "continue monitoring",
            "maintain label", "label update", "surveillance",
        ]
        if _match_action(str(sub.get("regulatory_action", "")), action_aliases):
            bd["regulatory_action"] = 0.35
            msgs.append("Regulatory action correct — monitor (+0.35)")
        else:
            bd["regulatory_action"] = 0.0
            msgs.append(
                f"Regulatory action incorrect (got '{sub.get('regulatory_action', '')}', "
                "expected 'monitor')"
            )

        # ---- efficiency bonus (up to +0.09) ----
        non_submit_steps = [a for a in history if a != "submit"]
        if len(non_submit_steps) <= 2:
            bd["efficiency_bonus"] = 0.09
            msgs.append(f"Efficiency bonus: solved in {len(non_submit_steps)} investigation steps (+0.09)")
        elif len(non_submit_steps) == 3:
            bd["efficiency_bonus"] = 0.05
            msgs.append(f"Partial efficiency bonus: solved in {len(non_submit_steps)} steps (+0.05)")
        else:
            bd["efficiency_bonus"] = 0.0
            msgs.append(f"No efficiency bonus ({len(non_submit_steps)} investigation steps)")

        # ---- early-submit penalty ----
        if history and history[0] == "submit":
            bd["early_submit_penalty"] = -0.10
            msgs.append("Penalty: submitted before any investigation (-0.10)")
        else:
            bd["early_submit_penalty"] = 0.0

    # ------------------------------------------------------------------
    # Medium: Rofecoxib — Myocardial Infarction / Withdraw
    # ------------------------------------------------------------------

    @staticmethod
    def _grade_medium(
        gt: dict[str, Any],
        sub: dict[str, Any],
        history: list[str],
        bd: dict[str, float],
        msgs: list[str],
    ) -> None:

        # ---- drug_name (0.20) ----
        drug_aliases = ["rofecoxib", "vioxx", "rofecoxibum"]
        if _match_drug_name(str(sub.get("drug_name", "")), drug_aliases):
            bd["drug_name"] = 0.20
            msgs.append("Drug name correct — rofecoxib (+0.20)")
        else:
            bd["drug_name"] = 0.0
            msgs.append(
                f"Drug name incorrect (got '{sub.get('drug_name', '')}', expected 'rofecoxib')"
            )

        # ---- primary_signal (0.30) ----
        signal_aliases = [
            "myocardial infarction", "heart attack",
            "acute myocardial infarction", "cardiovascular",
            "thrombotic cardiovascular", "cardiac event", "coronary",
        ]
        if _match_signal(str(sub.get("primary_signal", "")), signal_aliases):
            bd["primary_signal"] = 0.30
            msgs.append("Primary signal correct — myocardial infarction (+0.30)")
        else:
            bd["primary_signal"] = 0.0
            msgs.append(
                f"Primary signal incorrect (got '{sub.get('primary_signal', '')}', "
                "expected 'myocardial infarction')"
            )

        # ---- regulatory_action (0.30) ----
        action_aliases = [
            "withdraw", "withdrawal", "market withdrawal",
            "voluntarily withdrawn", "pulled from market",
            "remove from market", "revoke approval",
        ]
        if _match_action(str(sub.get("regulatory_action", "")), action_aliases):
            bd["regulatory_action"] = 0.30
            msgs.append("Regulatory action correct — withdraw (+0.30)")
        else:
            bd["regulatory_action"] = 0.0
            msgs.append(
                f"Regulatory action incorrect (got '{sub.get('regulatory_action', '')}', "
                "expected 'withdraw')"
            )

        # ---- action coverage bonus (0.15) ----
        # Full bonus: used both key investigation tools; partial for one
        required = {"search_faers", "analyze_signal"}
        history_set = set(history)
        if required.issubset(history_set):
            bd["coverage_bonus"] = 0.15
            msgs.append("Coverage bonus: used search_faers + analyze_signal (+0.15)")
        elif len(required & history_set) == 1:
            bd["coverage_bonus"] = 0.07
            msgs.append(f"Partial coverage: used {required & history_set} (+0.07)")
        else:
            bd["coverage_bonus"] = 0.0
            msgs.append(f"No coverage bonus — missing: {required - history_set}")

        # ---- redundancy penalty (-0.05 per each repeated action, cap -0.15) ----
        redundant = max(0, len(history) - len(set(history)))
        penalty = max(-0.15, -0.05 * redundant)
        bd["redundancy_penalty"] = penalty
        if penalty < 0:
            msgs.append(f"Redundancy penalty ({redundant} repeated actions): {penalty:.2f}")

    # ------------------------------------------------------------------
    # Hard: Isotretinoin — Teratogenicity + Depression / Restrict
    # ------------------------------------------------------------------

    @staticmethod
    def _grade_hard(
        gt: dict[str, Any],
        sub: dict[str, Any],
        history: list[str],
        bd: dict[str, float],
        msgs: list[str],
    ) -> None:

        # ---- drug_name (0.15) ----
        drug_aliases = ["isotretinoin", "accutane", "roaccutane", "13 cis retinoic acid",
                        "claravis", "amnesteem", "sotret", "myorisan"]
        if _match_drug_name(str(sub.get("drug_name", "")), drug_aliases):
            bd["drug_name"] = 0.15
            msgs.append("Drug name correct — isotretinoin (+0.15)")
        else:
            bd["drug_name"] = 0.0
            msgs.append(
                f"Drug name incorrect (got '{sub.get('drug_name', '')}', expected 'isotretinoin')"
            )

        # ---- primary_signal (0.25) ----
        primary_aliases = [
            "teratogenicity", "teratogen", "teratogenic", "birth defect",
            "congenital anomal", "fetal malformation", "congenital defect",
            "embryotoxicity", "fetal toxicity", "category x", "pregnancy risk",
        ]
        if _match_signal(str(sub.get("primary_signal", "")), primary_aliases):
            bd["primary_signal"] = 0.25
            msgs.append("Primary signal correct — teratogenicity (+0.25)")
        else:
            bd["primary_signal"] = 0.0
            msgs.append(
                f"Primary signal incorrect (got '{sub.get('primary_signal', '')}', "
                "expected 'teratogenicity')"
            )

        # ---- secondary_signal (0.15) ----
        secondary_aliases = [
            "depression", "depressive disorder", "psychiatric",
            "mental health", "suicid", "mood disorder", "psychosis",
            "affective disorder", "depressive symptoms",
        ]
        if _match_signal(str(sub.get("secondary_signal", "")), secondary_aliases):
            bd["secondary_signal"] = 0.15
            msgs.append("Secondary signal correct — depression (+0.15)")
        else:
            bd["secondary_signal"] = 0.0
            msgs.append(
                f"Secondary signal incorrect (got '{sub.get('secondary_signal', '')}', "
                "expected 'depression')"
            )

        # ---- regulatory_action (0.25) ----
        action_aliases = [
            "restrict", "restricted", "restriction", "market restriction",
            "rems", "risk evaluation", "ipledge",
            "risk management", "restricted access", "rems program",
            "risk minimisation", "conditional approval",
        ]
        if _match_action(str(sub.get("regulatory_action", "")), action_aliases):
            bd["regulatory_action"] = 0.25
            msgs.append("Regulatory action correct — restrict (REMS) (+0.25)")
        else:
            bd["regulatory_action"] = 0.0
            msgs.append(
                f"Regulatory action incorrect (got '{sub.get('regulatory_action', '')}', "
                "expected 'restrict')"
            )

        # ---- full coverage bonus (+0.10) ----
        required_all = {
            "search_faers", "fetch_label", "analyze_signal",
            "lookup_mechanism", "check_literature",
        }
        history_set = set(history)
        coverage_count = len(required_all & history_set)
        if required_all.issubset(history_set):
            bd["full_coverage_bonus"] = 0.10
            msgs.append("Full coverage bonus: all 5 investigation actions used (+0.10)")
        elif coverage_count >= 3:
            bd["full_coverage_bonus"] = 0.05
            msgs.append(f"Partial coverage ({coverage_count}/5 actions used): +0.05")
        else:
            bd["full_coverage_bonus"] = 0.0
            missing = required_all - history_set
            msgs.append(f"No full coverage bonus — missing: {missing}")

        # ---- overstep penalty (-0.03 per step over 10, cap -0.15) ----
        oversteps = max(0, len(history) - 10)
        penalty = max(-0.15, -0.03 * oversteps)
        bd["overstep_penalty"] = penalty
        if penalty < 0:
            msgs.append(
                f"Overstep penalty ({oversteps} steps over limit): {penalty:.2f}"
            )
