import dspy


class TrialQualityAssessor(dspy.Signature):
    """
    Assess the clinical trial design quality and endpoint strength
    for an FDA submission candidate.
    """

    trial_data: str = dspy.InputField(
        desc="Structured JSON summary of clinical trial records",
    )
    indication: str = dspy.InputField(
        desc="Medical indication being studied (e.g. NSCLC, T2DM)",
    )

    quality_score: float = dspy.OutputField(
        desc="Trial quality score from 0.0 (poor) to 1.0 (excellent)",
    )
    primary_endpoint_strength: str = dspy.OutputField(
        desc="Assessment of primary endpoint: 'strong' | 'moderate' | 'weak'",
    )
    enrollment_adequacy: str = dspy.OutputField(
        desc="Whether enrollment size is sufficient for statistical power",
    )
    reasoning: str = dspy.OutputField(
        desc="Step-by-step reasoning chain for the quality assessment",
    )


class SafetySignalAnalyzer(dspy.Signature):
    """
    Identify and classify adverse event patterns from FAERS data,
    benchmarked against the drug class baseline.
    """

    faers_data: str = dspy.InputField(
        desc="Structured adverse event report summary from openFDA FAERS",
    )
    drug_class: str = dspy.InputField(
        desc="Pharmacological class of the drug for baseline comparison",
    )

    safety_concerns: list[str] = dspy.OutputField(
        desc="List of specific adverse event concerns identified",
    )
    class_comparison: str = dspy.OutputField(
        desc="How the safety profile compares to the drug class baseline",
    )
    severity: str = dspy.OutputField(
        desc="Overall severity: 'low' | 'medium' | 'high' | 'black_box'",
    )
    fda_action_risk: str = dspy.OutputField(
        desc="Likelihood FDA will require label restrictions or REMS",
    )


class ComparableApprovalAnalyzer(dspy.Signature):
    """
    Analyze precedent set by historically approved or rejected drugs
    in the same therapeutic area.
    """

    indication: str = dspy.InputField(
        desc="Target medical indication",
    )
    mechanism: str = dspy.InputField(
        desc="Mechanism of action of the drug under review",
    )
    historical_approvals: str = dspy.InputField(
        desc="JSON list of comparable drugs with their FDA outcomes",
    )

    precedent_strength: str = dspy.OutputField(
        desc="'strong' | 'moderate' | 'weak' -- how clear a path exists",
    )
    approval_rate_context: str = dspy.OutputField(
        desc="Historical approval rate for this drug class / indication",
    )
    key_differences: list[str] = dspy.OutputField(
        desc="Ways the current drug differs from historical comparables",
    )
    analogous_approvals: list[str] = dspy.OutputField(
        desc="Drug names most analogous to current candidate",
    )


class ApprovalProbabilityEstimator(dspy.Signature):
    """
    Synthesize all upstream signals into a final calibrated approval
    probability with supporting rationale.
    """

    trial_quality_analysis: str = dspy.InputField(
        desc="Output from TrialQualityAssessor module",
    )
    safety_analysis: str = dspy.InputField(
        desc="Output from SafetySignalAnalyzer module",
    )
    precedent_analysis: str = dspy.InputField(
        desc="Output from ComparableApprovalAnalyzer module",
    )
    adcom_vote: str = dspy.InputField(
        desc="Advisory committee vote result, or 'No adcom held'",
    )
    pubmed_evidence: str = dspy.InputField(
        desc="Summary of published clinical trial result literature",
    )

    approval_probability: float = dspy.OutputField(
        desc="Estimated probability of FDA approval, between 0.0 and 1.0",
    )
    confidence: str = dspy.OutputField(
        desc="Confidence in estimate: 'low' | 'medium' | 'high'",
    )
    key_risks: list[str] = dspy.OutputField(
        desc="Top 3-5 factors that could lead to rejection or delay",
    )
    key_tailwinds: list[str] = dspy.OutputField(
        desc="Top 3-5 factors supporting approval",
    )
    executive_summary: str = dspy.OutputField(
        desc="2-3 sentence plain-English summary for a non-technical reader",
    )

