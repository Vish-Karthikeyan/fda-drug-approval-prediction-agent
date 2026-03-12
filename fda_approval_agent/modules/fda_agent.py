from __future__ import annotations

import json
from typing import Any, Dict

import dspy
from dspy.predict import ReAct

from fda_approval_agent.tools.clinical_trials import search_clinical_trials
from fda_approval_agent.tools.open_fda import (
    get_adverse_event_signal,
    get_historical_approvals,
)
from fda_approval_agent.tools.pubmed import get_trial_results
from fda_approval_agent.tools.adcom import get_adcom_vote
from fda_approval_agent.signatures.fda_signatures import (
    ApprovalProbabilityEstimator,
    ComparableApprovalAnalyzer,
    SafetySignalAnalyzer,
    TrialQualityAssessor,
)


class FDAApprovalAgent(dspy.Module):
    """
    DSPy module implementing an FDA drug approval prediction agent.

    It uses a ReAct loop to decide which tools to call (ClinicalTrials.gov, openFDA,
    PubMed, FDA advisory committee scraper), gathers structured evidence, and then
    runs a multi-step reasoning chain to estimate approval probability, key risks, and
    tailwinds.
    """

    def __init__(self, ncbi_email: str | None = None, fda_api_key: str | None = None) -> None:
        super().__init__()

        # Tool registry for the ReAct loop.
        self.tools = {
            "search_clinical_trials": search_clinical_trials,
            "get_adverse_event_signal": lambda drug_name, **_: get_adverse_event_signal(
                drug_name, api_key=fda_api_key
            ),
            "get_historical_approvals": get_historical_approvals,
            "get_trial_results": lambda drug_name, indication, **_: get_trial_results(
                drug_name, indication, email=ncbi_email or ""
            ),
            "get_adcom_vote": get_adcom_vote,
        }

        # Core ReAct agent with access to tools.
        self.react_agent = ReAct(
            signature="drug_name, indication -> gathered_evidence",
            tools=list(self.tools.values()),
            max_iters=8,
        )

        # Structured DSPy reasoning modules.
        self.assess_trial = dspy.ChainOfThought(TrialQualityAssessor)
        self.analyze_safety = dspy.ChainOfThought(SafetySignalAnalyzer)
        self.analyze_precedent = dspy.ChainOfThought(ComparableApprovalAnalyzer)
        self.estimate = dspy.ChainOfThought(ApprovalProbabilityEstimator)

    def forward(self, drug_name: str, indication: str, mechanism: str = "unknown") -> dspy.Prediction:
        # --- Phase 1: ReAct evidence gathering ---
        react_result = self.react_agent(drug_name=drug_name, indication=indication)
        gathered = getattr(react_result, "gathered_evidence", react_result)

        if not isinstance(gathered, str):
            try:
                gathered = json.dumps(gathered, default=str)
            except TypeError:
                gathered = str(gathered)

        # --- Phase 2: Structured reasoning chain ---
        trial_analysis = self.assess_trial(trial_data=gathered, indication=indication)

        safety_analysis = self.analyze_safety(
            faers_data=gathered,
            drug_class=mechanism,
        )

        precedent_analysis = self.analyze_precedent(
            indication=indication,
            mechanism=mechanism,
            historical_approvals=gathered,
        )

        # --- Phase 3: Final synthesis ---
        final = self.estimate(
            trial_quality_analysis=str(trial_analysis),
            safety_analysis=str(safety_analysis),
            precedent_analysis=str(precedent_analysis),
            adcom_vote=gathered,
            pubmed_evidence=gathered,
        )

        # Ensure approval_probability is clipped to [0.0, 1.0].
        try:
            p = float(final.approval_probability)
            p = max(0.0, min(1.0, p))
            final.approval_probability = p
        except Exception:  # noqa: BLE001
            final.approval_probability = 0.5

        return final

