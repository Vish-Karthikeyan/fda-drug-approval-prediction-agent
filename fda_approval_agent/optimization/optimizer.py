from __future__ import annotations

from typing import List

import dspy
import requests

from fda_approval_agent.tools.open_fda import APPROVAL_URL


def build_ground_truth_dataset(limit: int = 120) -> List[dspy.Example]:
    """
    Fetch historical PDUFA decisions from openFDA and structure
    them as DSPy training examples.

    Each example: drug_name, indication, mechanism -> approved (bool)
    """
    examples: List[dspy.Example] = []

    params = {
        "search": "application_type:nda",
        "limit": limit,
    }

    try:
        resp = requests.get(APPROVAL_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return examples

    for record in data.get("results", []):
        brand_names = record.get("products", []) or record.get("product_names", [])
        brand_name = None
        if isinstance(brand_names, list) and brand_names:
            first = brand_names[0]
            if isinstance(first, dict):
                brand_name = first.get("brand_name") or first.get("brandName")
            else:
                brand_name = str(first)

        applications = record.get("applications", [])
        indication = ""
        mechanism = ""
        approved = False

        for app in applications:
            for product in app.get("products", []):
                indication = indication or product.get("indication", "")
            for action in app.get("actions", []):
                action_type = action.get("action_type", "")
                if action_type == "AP":
                    approved = True

        if not brand_name:
            continue

        examples.append(
            dspy.Example(
                drug_name=brand_name,
                indication=indication or "unknown",
                mechanism=mechanism or "unknown",
                approved=approved,
            ),
        )

    return examples


def approval_accuracy(pred: dspy.Prediction, example: dspy.Example) -> float:
    """
    Optimization metric: binary accuracy of approval prediction.
    Converts probability to binary at 0.5 threshold.
    """
    predicted = float(pred.approval_probability) >= 0.5
    return float(predicted == bool(example.approved))


def run_optimizer(agent: dspy.Module, train_set: List[dspy.Example]) -> dspy.Module:
    from dspy.teleprompt import BootstrapFewShot

    optimizer = BootstrapFewShot(
        metric=approval_accuracy,
        max_bootstrapped_demos=4,
        max_labeled_demos=8,
    )
    return optimizer.compile(agent, trainset=train_set)

