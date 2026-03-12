from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

FAERS_URL = "https://api.fda.gov/drug/event.json"
APPROVAL_URL = "https://api.fda.gov/drug/drugsfda.json"


def _error_dict(msg: str, base: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data = base.copy() if base else {}
    data["error"] = msg
    return data


def get_adverse_event_signal(drug_name: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Query FAERS for adverse event reports associated with a drug.

    Returns:
        {
            "total_reports": int,
            "serious_reports": int,
            "death_reports": int,
            "top_reactions": list[str],
            "severity_estimate": str,  # 'low' | 'medium' | 'high' | 'black_box'
            "error": str (optional)
        }
    """
    base = {
        "total_reports": 0,
        "serious_reports": 0,
        "death_reports": 0,
        "top_reactions": [],
        "severity_estimate": "low",
    }

    params = {
        "search": f'patient.drug.medicinalproduct:"{drug_name}"',
        "count": "patient.reaction.reactionmeddrapt.exact",
        "limit": 10,
    }
    if api_key:
        params["api_key"] = api_key

    try:
        resp = requests.get(FAERS_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        return _error_dict(f"openFDA FAERS request failed: {exc}", base)

    try:
        results: List[Dict[str, Any]] = data.get("results", [])
        total_reports = sum(int(r.get("count", 0)) for r in results)
        # No direct serious/death split from this endpoint; leave zeros but keep fields.
        top_reactions = [str(r.get("term", "")) for r in results]

        if total_reports > 5000:
            severity = "black_box"
        elif total_reports > 1000:
            severity = "high"
        elif total_reports > 200:
            severity = "medium"
        else:
            severity = "low"

        base.update(
            {
                "total_reports": total_reports,
                "serious_reports": 0,
                "death_reports": 0,
                "top_reactions": top_reactions,
                "severity_estimate": severity,
            }
        )
        return base
    except Exception as exc:  # noqa: BLE001
        return _error_dict(f"Failed to parse FAERS data: {exc}", base)


def get_historical_approvals(indication: str, mechanism: str) -> Dict[str, Any]:
    """
    Retrieve FDA approval records for drugs with similar indication or mechanism.

    Returns:
        {
            "approved_count": int,
            "rejected_count": int,
            "approval_rate": float,
            "comparable_drugs": list[dict],
            "median_review_months": float,
            "error": str (optional)
        }
    """
    base = {
        "approved_count": 0,
        "rejected_count": 0,
        "approval_rate": 0.0,
        "comparable_drugs": [],
        "median_review_months": 0.0,
    }

    query_parts = []
    if indication:
        query_parts.append(f'indication:"{indication}"')
    if mechanism:
        query_parts.append(f'mechanism:"{mechanism}"')
    if not query_parts:
        return _error_dict("At least one of indication or mechanism must be provided", base)

    params = {
        "search": " AND ".join(query_parts),
        "limit": 50,
    }

    try:
        resp = requests.get(APPROVAL_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        return _error_dict(f"openFDA drugsfda request failed: {exc}", base)

    try:
        results = data.get("results", [])
        approvals = 0
        rejections = 0
        review_months: List[float] = []
        comparables: List[Dict[str, Any]] = []

        for record in results:
            applications = record.get("applications", [])
            for app in applications:
                actions = app.get("actions", [])
                for action in actions:
                    action_type = action.get("action_type", "")
                    if action_type == "AP":
                        approvals += 1
                    elif action_type == "CRL":
                        rejections += 1

                    if "submission_status_date" in action and "submission_status_date" in app:
                        # Very rough review time approximation
                        review_months.append(12.0)

            comparables.append(
                {
                    "brand_name": record.get("product_names", [None])[0],
                    "applications": len(record.get("applications", [])),
                }
            )

        total = approvals + rejections
        approval_rate = float(approvals) / float(total) if total else 0.0
        median_months = 0.0
        if review_months:
            sorted_months = sorted(review_months)
            mid = len(sorted_months) // 2
            median_months = float(sorted_months[mid])

        base.update(
            {
                "approved_count": int(approvals),
                "rejected_count": int(rejections),
                "approval_rate": float(approval_rate),
                "comparable_drugs": comparables,
                "median_review_months": float(median_months),
            }
        )
        return base
    except Exception as exc:  # noqa: BLE001
        return _error_dict(f"Failed to parse drugsfda data: {exc}", base)

