"""
Drug-Triage-Env: Action handler.

Loads pre-cached fixture JSON at startup and routes agent actions
to the appropriate data source. Never makes live HTTP requests —
all data is deterministic and reproducible.
"""

from __future__ import annotations

import json
import logging as _logging
from pathlib import Path
from typing import Any

from environment.models import DrugAction

_log = _logging.getLogger(__name__)

_FIXTURES_DIR = Path(__file__).parent / "fixtures"

_KNOWN_DRUGS = ["METFORMIN", "ROFECOXIB", "ISOTRETINOIN"]


class ActionHandler:
    """Dispatches agent actions to pre-cached FDA FAERS fixture data."""

    def __init__(self) -> None:
        self.fixtures: dict[str, dict[str, Any]] = {}
        for drug in _KNOWN_DRUGS:
            fixture_path = _FIXTURES_DIR / f"{drug}.json"
            if not fixture_path.exists():
                _log.warning(f"Missing fixture file: {fixture_path}. Expected fixture for {drug}.")
                continue
            try:
                with open(fixture_path, encoding="utf-8") as fh:
                    self.fixtures[drug] = json.load(fh)
            except FileNotFoundError as exc:
                _log.warning(f"Failed to read {fixture_path}: {exc}")
                continue

        # Dispatch table — no if/elif chains
        self._dispatch_map: dict[str, Any] = {
            "search_faers": self._search_faers,
            "fetch_label": self._fetch_label,
            "analyze_signal": self._analyze_signal,
            "lookup_mechanism": self._lookup_mechanism,
            "check_literature": self._check_literature,
            "submit": self._submit,
        }

    # ------------------------------------------------------------------
    # Individual action handlers
    # ------------------------------------------------------------------

    def _search_faers(self, drug_name: str, **_: Any) -> dict[str, Any]:
        """Query FDA FAERS adverse event database."""
        fixture = self.fixtures.get(drug_name)
        if fixture is None:
            return {"error": f"No FAERS data found for {drug_name}"}
        data = dict(fixture["faers_data"])
        return {
            "source": "FDA FAERS",
            "query": drug_name,
            "data": data,
            "hint": "Review the top_adverse_events list carefully — the primary signal is there.",
        }

    def _fetch_label(self, drug_name: str, **_: Any) -> dict[str, Any]:
        """Retrieve official FDA drug labeling / prescribing information."""
        fixture = self.fixtures.get(drug_name)
        if fixture is None:
            return {"error": f"No label data found for {drug_name}"}
        data = dict(fixture["label_data"])
        return {
            "source": "FDA DailyMed / SPL",
            "query": drug_name,
            "data": data,
            "hint": "The black_box_warning field contains the most serious safety concerns.",
        }

    def _analyze_signal(self, drug_name: str, **_: Any) -> dict[str, Any]:
        """Run disproportionality analysis — PRR, ROR, IC025, EB05."""
        fixture = self.fixtures.get(drug_name)
        if fixture is None:
            return {"error": f"No signal analysis data found for {drug_name}"}
        data = dict(fixture["signal_analysis"])
        return {
            "source": "Disproportionality Analysis (MGPS + PRR)",
            "query": drug_name,
            "data": data,
            "interpretation_guide": {
                "PRR > 2 + chi2 > 4": "Signal detected",
                "PRR > 5": "Strong signal",
                "PRR > 8": "Critical signal",
                "IC025 > 0": "Signal detected (Bayesian)",
                "signal_strength_CRITICAL": "Requires immediate regulatory action",
            },
        }

    def _lookup_mechanism(self, drug_name: str, **_: Any) -> dict[str, Any]:
        """Look up the drug's pharmacological mechanism of action."""
        fixture = self.fixtures.get(drug_name)
        if fixture is None:
            return {"error": f"No mechanism data found for {drug_name}"}
        data = dict(fixture["mechanism_data"])
        return {
            "source": "PharmGKB / DrugBank",
            "query": drug_name,
            "data": data,
            "hint": "Understanding the mechanism helps explain why the adverse event occurs.",
        }

    def _check_literature(self, drug_name: str, **_: Any) -> dict[str, Any]:
        """Search published safety literature and regulatory precedents."""
        fixture = self.fixtures.get(drug_name)
        if fixture is None:
            return {"error": f"No literature data found for {drug_name}"}
        data = dict(fixture["literature_data"])
        return {
            "source": "PubMed / regulatory database",
            "query": drug_name,
            "data": data,
            "hint": "regulatory_precedent describes what actions were actually taken historically.",
        }

    @staticmethod
    def _submit(answer: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
        """Record the agent's final submission."""
        if answer is None:
            answer = {}
        return {**answer, "submitted": True, "source": "agent_submission"}

    # ------------------------------------------------------------------
    # Public dispatcher
    # ------------------------------------------------------------------

    def dispatch(self, action: DrugAction, drug_name: str) -> dict[str, Any]:
        """Route an action to the correct handler.

        Raises:
            ValueError: If *action.action_type* is not recognised.
        """
        handler = self._dispatch_map.get(action.action_type)
        if handler is None:
            raise ValueError(
                f"Unknown action type: '{action.action_type}'. "
                f"Valid types: {list(self._dispatch_map.keys())}"
            )

        if action.action_type == "submit":
            return handler(answer=action.parameters)
        return handler(drug_name=drug_name)
