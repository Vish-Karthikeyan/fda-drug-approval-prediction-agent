import json
from typing import Any, Dict, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"


def _empty_result(error: Optional[str] = None) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "total_studies": 0,
        "phase_3_count": 0,
        "primary_endpoint_met": None,
        "enrollment": 0,
        "sponsor": "",
        "nct_ids": [],
        "completion_date": "",
        "raw_studies": [],
    }
    if error:
        result["error"] = error
    return result


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def search_clinical_trials(drug_name: str, indication: str, phase: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve clinical trial records for a given drug and indication.

    Returns:
        {
            "total_studies": int,
            "phase_3_count": int,
            "primary_endpoint_met": bool | None,
            "enrollment": int,
            "sponsor": str,
            "nct_ids": list[str],
            "completion_date": str,
            "raw_studies": list[dict],
            "error": str (optional)
        }
    """
    params = {
        "query.term": f"{drug_name} {indication}",
        "filter.phase": phase,
        "fields": ",".join(
            [
                "NCTId",
                "Phase",
                "EnrollmentCount",
                "PrimaryOutcomesMeasure",
                "OverallStatus",
                "CompletionDate",
                "LeadSponsorName",
            ]
        ),
        "pageSize": 20,
        "format": "json",
    }

    try:
        response = requests.get(
            BASE_URL,
            params={k: v for k, v in params.items() if v is not None},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:  # noqa: BLE001
        return _empty_result(error=f"ClinicalTrials.gov request failed: {exc}")

    try:
        studies = data.get("studies", [])
        total_studies = data.get("totalStudies", len(studies))

        phase_3_count = 0
        enrollment_total = 0
        nct_ids = []
        completion_date = ""
        sponsor = ""
        primary_endpoint_met: Optional[bool] = None

        for study in studies:
            attrs = study.get("protocolSection", {})
            id_section = attrs.get("identificationModule", {})
            status_section = attrs.get("statusModule", {})
            design_section = attrs.get("designModule", {})
            outcomes_section = attrs.get("outcomesModule", {})

            nct_id = id_section.get("nctId")
            if nct_id:
                nct_ids.append(nct_id)

            phase_value = design_section.get("phases", [])
            if any("Phase 3" in str(p) for p in phase_value):
                phase_3_count += 1

            try:
                enrollment_total += int(design_section.get("enrollmentInfo", {}).get("enrollmentCount", 0))
            except (TypeError, ValueError):
                pass

            if not sponsor:
                sponsor = id_section.get("organisation", "") or id_section.get("organisationFullName", "")

            if not completion_date:
                completion_date = status_section.get("completionDateStruct", {}).get("date", "")

            # Heuristic: check if primary outcome mentions "met" or "achieved"
            primary_measures = outcomes_section.get("primaryOutcomes", [])
            text_blob = json.dumps(primary_measures).lower()
            if "met" in text_blob or "achieved" in text_blob:
                primary_endpoint_met = True

        return {
            "total_studies": int(total_studies),
            "phase_3_count": int(phase_3_count),
            "primary_endpoint_met": primary_endpoint_met,
            "enrollment": int(enrollment_total),
            "sponsor": sponsor,
            "nct_ids": nct_ids,
            "completion_date": completion_date,
            "raw_studies": studies,
        }
    except Exception as exc:  # noqa: BLE001
        return _empty_result(error=f"Failed to parse ClinicalTrials.gov response: {exc}")

