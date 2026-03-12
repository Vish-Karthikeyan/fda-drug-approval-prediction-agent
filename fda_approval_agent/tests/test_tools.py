from fda_approval_agent.tools.clinical_trials import search_clinical_trials
from fda_approval_agent.tools.open_fda import (
    get_adverse_event_signal,
    get_historical_approvals,
)
from fda_approval_agent.tools.pubmed import get_trial_results
from fda_approval_agent.tools.adcom import get_adcom_vote


def test_search_clinical_trials_basic_structure():
    result = search_clinical_trials("aspirin", "pain", phase=None)
    assert isinstance(result, dict)
    for key in [
        "total_studies",
        "phase_3_count",
        "primary_endpoint_met",
        "enrollment",
        "sponsor",
        "nct_ids",
        "completion_date",
        "raw_studies",
    ]:
        assert key in result


def test_open_fda_adverse_event_signal_structure():
    result = get_adverse_event_signal("aspirin")
    assert isinstance(result, dict)
    for key in [
        "total_reports",
        "serious_reports",
        "death_reports",
        "top_reactions",
        "severity_estimate",
    ]:
        assert key in result


def test_open_fda_historical_approvals_structure():
    result = get_historical_approvals("pain", "unknown")
    assert isinstance(result, dict)
    for key in [
        "approved_count",
        "rejected_count",
        "approval_rate",
        "comparable_drugs",
        "median_review_months",
    ]:
        assert key in result


def test_pubmed_trial_results_handles_missing_email():
    result = get_trial_results("aspirin", "pain", email="")
    assert isinstance(result, dict)
    assert "error" in result


def test_adcom_vote_structure():
    result = get_adcom_vote("aspirin")
    assert isinstance(result, dict)
    for key in [
        "adcom_held",
        "votes_for",
        "votes_against",
        "votes_abstain",
        "recommendation",
        "source_url",
    ]:
        assert key in result

