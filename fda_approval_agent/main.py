import dspy

from fda_approval_agent.config import load_config
from fda_approval_agent.modules.fda_agent import FDAApprovalAgent
from fda_approval_agent.optimization.optimizer import (
    build_ground_truth_dataset,
    run_optimizer,
)


def main() -> None:
    cfg = load_config()

    if not cfg.openai_api_key:
        print("WARNING: OPENAI_API_KEY not configured; DSPy calls will likely fail.")

    lm = dspy.LM(model=cfg.lm_model, api_key=cfg.openai_api_key)
    dspy.configure(lm=lm)

    agent: dspy.Module = FDAApprovalAgent(
        ncbi_email=cfg.ncbi_email,
        fda_api_key=cfg.fda_api_key,
    )

    if cfg.run_optimizer:
        dataset = build_ground_truth_dataset()
        if dataset:
            train, test = dataset[:80], dataset[80:]
            agent = run_optimizer(agent, train)

            # Simple evaluation loop
            correct = 0
            for ex in test:
                pred = agent(
                    drug_name=ex.drug_name,
                    indication=ex.indication,
                    mechanism=ex.mechanism,
                )
                correct += int(
                    float(pred.approval_probability) >= 0.5
                    and bool(ex.approved)
                    or float(pred.approval_probability) < 0.5
                    and not bool(ex.approved),
                )
            if test:
                print(f"Held-out accuracy on {len(test)} examples: {correct / len(test):.3f}")
        else:
            print("Optimizer requested but dataset build returned no examples.")

    print("\n" + "=" * 60)
    print("DEMO CASE 1: Pembrolizumab (Keytruda) -- NSCLC")
    print("=" * 60)
    result = agent(drug_name="pembrolizumab", indication="NSCLC", mechanism="PD-1 inhibitor")
    print(f"Approval Probability: {result.approval_probability:.1%}")
    print(f"Confidence: {result.confidence}")
    print(f"Key Risks: {result.key_risks}")
    print(f"Key Tailwinds: {result.key_tailwinds}")
    print(f"Summary: {result.executive_summary}")

    print("\n" + "=" * 60)
    print("DEMO CASE 2: Aducanumab -- Alzheimer's Disease")
    print("=" * 60)
    result = agent(
        drug_name="aducanumab",
        indication="Alzheimer's disease",
        mechanism="amyloid beta antibody",
    )
    print(f"Approval Probability: {result.approval_probability:.1%}")
    print(f"Confidence: {result.confidence}")
    print(f"Key Risks: {result.key_risks}")
    print(f"Key Tailwinds: {result.key_tailwinds}")
    print(f"Summary: {result.executive_summary}")


if __name__ == "__main__":
    main()

