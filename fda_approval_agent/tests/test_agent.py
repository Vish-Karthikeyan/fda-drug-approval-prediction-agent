import dspy

from fda_approval_agent.config import load_config
from fda_approval_agent.modules.fda_agent import FDAApprovalAgent


def test_agent_runs_and_probability_in_range():
    cfg = load_config()
    lm = dspy.LM(model=cfg.lm_model, api_key=cfg.openai_api_key)
    dspy.configure(lm=lm)

    agent = FDAApprovalAgent(
        ncbi_email=cfg.ncbi_email,
        fda_api_key=cfg.fda_api_key,
    )
    result = agent(
        drug_name="pembrolizumab",
        indication="NSCLC",
        mechanism="PD-1 inhibitor",
    )
    assert 0.0 <= float(result.approval_probability) <= 1.0

