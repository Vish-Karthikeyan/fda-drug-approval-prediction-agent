"""
Extra Credit 

In this assignment, you will create your own AI agent using DSPy and any tools/APIs you choose.

Your agent should:
1. Use DSPy's framework (signatures, modules, etc.)
2. Implement some interesting functionality beyond basic chat
3. Demonstrate your implementation with a working example

You have complete freedom to:
- Choose what your agent does (data analysis, creative generation, etc.)
- Select which APIs or libraries to integrate
- Design the interface and interaction pattern

Some ideas to get you started:
- A research assistant that uses web search
- A creative writing collaborator with style adaptation
- A data analysis agent that processes files
- A multi-step reasoning agent for complex problems
- Something completely different! Be creative!

Complete the TODOs below to build your agent.
"""

import dspy

from fda_approval_agent.config import load_config
from fda_approval_agent.modules.fda_agent import FDAApprovalAgent


CFG = load_config()


def _configure_dspy() -> None:
    lm = dspy.LM(model=CFG.lm_model, api_key=CFG.openai_api_key)
    dspy.configure(lm=lm)


class YourAgentSignature(dspy.Signature):
    """
    Interactive FDA approval prediction assistant.

    The agent helps users reason about the probability that a drug will
    receive FDA approval for a given indication. It should:
    - Accept a string like 'drug=NAME; indication=CONDITION; mechanism=MECHANISM (optional)'.
    - Use tools (ClinicalTrials.gov, openFDA, PubMed, FDA advisory committees)
      via a ReAct loop to gather evidence.
    - Synthesize evidence into an approval probability, key risks, and
      tailwinds, and respond in clear, non-technical language.
    """
    user_input: str = dspy.InputField(
        desc="Free-form question or structured string describing a drug and indication.",
    )
    response: str = dspy.OutputField(
        desc="Answer including approval probability and explanation.",
    )


class YourAgent(dspy.Module):
    """
    Thin wrapper around the FDAApprovalAgent to make it easy to use
    in this extra credit script as a conversational assistant.
    """

    def __init__(self):
        super().__init__()
        self.fda_agent = FDAApprovalAgent(
            ncbi_email=CFG.ncbi_email,
            fda_api_key=CFG.fda_api_key,
        )

    def forward(self, user_input: str):
        """Process user input and generate a response."""
        drug_name = ""
        indication = ""
        mechanism = "unknown"

        parts = [p.strip() for p in user_input.split(";") if p.strip()]
        for part in parts:
            lower = part.lower()
            if lower.startswith("drug=") or lower.startswith("drug ="):
                drug_name = part.split("=", 1)[1].strip()
            elif lower.startswith("indication=") or lower.startswith("indication ="):
                indication = part.split("=", 1)[1].strip()
            elif lower.startswith("mechanism=") or lower.startswith("mechanism ="):
                mechanism = part.split("=", 1)[1].strip()

        if not drug_name or not indication:
            return {
                "response": (
                    "Please provide input in the form "
                    "'drug=NAME; indication=CONDITION; mechanism=MECHANISM (optional)'."
                )
            }

        result = self.fda_agent(drug_name=drug_name, indication=indication, mechanism=mechanism)
        text = (
            f"Estimated approval probability for {drug_name} in {indication}: "
            f"{result.approval_probability:.1%} (confidence: {result.confidence}).\n"
            f"Key risks: {result.key_risks}\n"
            f"Key tailwinds: {result.key_tailwinds}\n"
            f"Summary: {result.executive_summary}"
        )
        return {"response": text}


def run_demo():
    """Demonstration of your agent."""
    _configure_dspy()

    agent = YourAgent()

    print("🤖 Agent Demo")
    print("=" * 50)

    test_inputs = [
        "drug=pembrolizumab; indication=NSCLC; mechanism=PD-1 inhibitor",
        "drug=aducanumab; indication=Alzheimer's disease; mechanism=amyloid beta antibody",
    ]
    
    for user_input in test_inputs:
        print(f"\n📝 User: {user_input}")
        out = agent(user_input=user_input)
        print(f"🤖 Agent: {out['response']}")


if __name__ == "__main__":
    run_demo()