from __future__ import annotations

from typing import Any, Dict, List

import requests

ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def get_trial_results(drug_name: str, indication: str, email: str) -> Dict[str, Any]:
    """
    Retrieve published Phase 3 trial results from PubMed.

    Returns:
        {
            "publications_found": int,
            "primary_endpoint_positive": bool | None,
            "effect_size_summary": str,
            "safety_summary": str,
            "pmids": list[str],
            "error": str (optional)
        }
    """
    base: Dict[str, Any] = {
        "publications_found": 0,
        "primary_endpoint_positive": None,
        "effect_size_summary": "",
        "safety_summary": "",
        "pmids": [],
    }

    if not email:
        base["error"] = "NCBI email is required for PubMed access"
        return base

    query = f'{drug_name}[Title/Abstract] AND {indication}[Title/Abstract] AND "Phase III"[Title/Abstract]'

    try:
        search_resp = requests.get(
            f"{ENTREZ_BASE}/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": 10,
                "email": email,
            },
            timeout=15,
        )
        search_resp.raise_for_status()
        search_data = search_resp.json()
    except Exception as exc:  # noqa: BLE001
        base["error"] = f"PubMed esearch failed: {exc}"
        return base

    try:
        id_list: List[str] = search_data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            base["publications_found"] = 0
            return base

        pmids_str = ",".join(id_list)
        fetch_resp = requests.get(
            f"{ENTREZ_BASE}/efetch.fcgi",
            params={
                "db": "pubmed",
                "id": pmids_str,
                "retmode": "xml",
                "email": email,
            },
            timeout=20,
        )
        fetch_resp.raise_for_status()
        xml_text = fetch_resp.text.lower()
    except Exception as exc:  # noqa: BLE001
        base["error"] = f"PubMed efetch failed: {exc}"
        return base

    try:
        primary_positive = None
        if "primary endpoint" in xml_text or "primary efficacy" in xml_text:
            if "met" in xml_text or "achieved" in xml_text or "statistically significant" in xml_text:
                primary_positive = True
            elif "not met" in xml_text or "failed" in xml_text:
                primary_positive = False

        effect_summary = "Unable to extract effect size; see PubMed abstracts."
        safety_summary = "Safety profile requires manual review of PubMed abstracts."

        base.update(
            {
                "publications_found": len(id_list),
                "primary_endpoint_positive": primary_positive,
                "effect_size_summary": effect_summary,
                "safety_summary": safety_summary,
                "pmids": id_list,
            }
        )
        return base
    except Exception as exc:  # noqa: BLE001
        base["error"] = f"Failed to parse PubMed XML: {exc}"
        return base

