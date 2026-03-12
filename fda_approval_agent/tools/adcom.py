from __future__ import annotations

from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup


def get_adcom_vote(drug_name: str) -> Dict[str, Any]:
    """
    Attempt to retrieve advisory committee vote for this drug.

    Returns:
        {
            "adcom_held": bool,
            "votes_for": int | None,
            "votes_against": int | None,
            "votes_abstain": int | None,
            "recommendation": str | None,  # 'favorable' | 'unfavorable' | 'mixed'
            "source_url": str | None,
            "error": str (optional)
        }
    """
    base: Dict[str, Any] = {
        "adcom_held": False,
        "votes_for": None,
        "votes_against": None,
        "votes_abstain": None,
        "recommendation": None,
        "source_url": None,
    }

    search_url = "https://www.fda.gov/advisory-committees/advisory-committee-calendar"
    try:
        resp = requests.get(search_url, timeout=20)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        base["error"] = f"Failed to fetch FDA adcom calendar: {exc}"
        return base

    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True).lower()
        if drug_name.lower() in text:
            base["adcom_held"] = True
            base["source_url"] = search_url

            # Heuristic recommendation guess based on nearby words.
            recommendation: Optional[str] = None
            if "vote" in text:
                if "unanimous" in text or "favorable" in text or "approve" in text:
                    recommendation = "favorable"
                elif "against" in text or "not approve" in text:
                    recommendation = "unfavorable"
                else:
                    recommendation = "mixed"

            base["recommendation"] = recommendation

        return base
    except Exception as exc:  # noqa: BLE001
        base["error"] = f"Failed to parse FDA adcom page: {exc}"
        return base

