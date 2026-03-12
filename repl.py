import sys

import dspy

from fda_approval_agent.config import load_config
from fda_approval_agent.modules.fda_agent import FDAApprovalAgent


def configure_dspy() -> tuple[dict, FDAApprovalAgent]:
    """Configure DSPy LM backend and return (cfg_dict, agent)."""
    cfg = load_config()

    if not cfg.openai_api_key:
        print("WARNING: OPENAI_API_KEY not configured; the agent may not work.", file=sys.stderr)

    lm = dspy.LM(model=cfg.lm_model, api_key=cfg.openai_api_key)
    dspy.configure(lm=lm)

    agent = FDAApprovalAgent(
        ncbi_email=cfg.ncbi_email,
        fda_api_key=cfg.fda_api_key,
    )
    return cfg.__dict__, agent


def pretty_print_result(drug_name: str, indication: str, result) -> None:
    """Nicely format the agent's prediction to the terminal."""
    print("\n" + "=" * 60)
    print(f"Results for {drug_name} in {indication}")
    print("=" * 60)
    try:
        prob = float(result.approval_probability)
    except Exception:  # noqa: BLE001
        prob = 0.5
    print(f"Estimated approval probability: {prob:.1%}")
    print(f"Confidence: {getattr(result, 'confidence', 'unknown')}")
    print(f"Key risks: {getattr(result, 'key_risks', [])}")
    print(f"Key tailwinds: {getattr(result, 'key_tailwinds', [])}")
    print(f"Summary: {getattr(result, 'executive_summary', '')}")
    print()


def _looks_like_question(text: str) -> bool:
    """Heuristic: detect when the user is asking a general question, not naming a drug."""
    if "?" in text:
        return True
    # Very long, multi-word phrases are unlikely to be a single drug or indication.
    return len(text.split()) > 6


def _is_general_chat(text: str) -> bool:
    """
    Heuristic to catch conversational / non-domain tokens like 'hello', 'hi', etc.

    This is intentionally conservative: we only reject very short, common
    greetings or filler words so we do not block real entities.
    """
    normalized = text.strip().lower()
    common_chat_words = {
        "hello",
        "hi",
        "hey",
        "yo",
        "thanks",
        "thank you",
        "ok",
        "okay",
        "yes",
        "no",
        "maybe",
        "sure",
    }
    # Single short word that is clearly conversational.
    if " " not in normalized and normalized in common_chat_words:
        return True

    # Common question words / pronouns signal general chat, not domain terms.
    chat_markers = {"how", "what", "who", "why", "where", "you", "doing", "going"}
    tokens = set(normalized.split())
    if tokens & chat_markers:
        return True

    return False


def main() -> None:
    _, agent = configure_dspy()

    print("🤖 FDA Drug Approval Prediction REPL")
    print("=" * 60)
    print("This terminal agent uses DSPy + ReAct to reason about the")
    print("probability that a drug will receive FDA approval.")
    print()
    print("Instructions:")
    print("- This REPL expects *real* drug and indication names, e.g.:")
    print("  Drug name: pembrolizumab")
    print("  Indication: non-small cell lung cancer (NSCLC)")
    print("  Mechanism: PD-1 inhibitor")
    print("- Type 'quit' at any prompt to exit.")
    print()

    while True:
        drug_name = input("Drug name (or 'quit'): ").strip()
        if not drug_name or drug_name.lower() == "quit":
            break

        if _looks_like_question(drug_name):
            print(
                "That looks like a question, not a drug name.\n"
                "Please enter a specific drug name (e.g., 'pembrolizumab')."
            )
            continue

        if _is_general_chat(drug_name):
            print(
                f"'{drug_name}' looks like a general chat message, not a drug name.\n"
                "This agent is specialized for FDA drug approval prediction, not open-ended conversation.\n"
                "Please enter a specific drug name (e.g., 'pembrolizumab')."
            )
            continue

        indication = input("Indication / condition: ").strip()
        if not indication or indication.lower() == "quit":
            break

        if _looks_like_question(indication):
            print(
                "That looks like a question, not a medical indication.\n"
                "Please enter a disease/condition (e.g., 'non-small cell lung cancer')."
            )
            continue

        if _is_general_chat(indication):
            print(
                f"'{indication}' looks like general conversation, not a medical indication.\n"
                "This agent is meant to analyze specific drug–indication pairs for FDA approval.\n"
                "Please enter a disease/condition (e.g., 'non-small cell lung cancer')."
            )
            continue

        mechanism = input("Mechanism of action (optional, Enter to skip): ").strip()
        if not mechanism:
            mechanism = "unknown"
        if mechanism.lower() == "quit":
            break

        if mechanism != "unknown" and _is_general_chat(mechanism):
            print(
                f"'{mechanism}' does not look like a mechanism of action.\n"
                "Mechanisms are phrases like 'PD-1 inhibitor' or 'amyloid beta antibody'.\n"
                "You can either enter a valid mechanism or just press Enter to skip."
            )
            continue

        print("\nThinking with tools and evidence... (this may take a moment)\n")
        try:
            result = agent(
                drug_name=drug_name,
                indication=indication,
                mechanism=mechanism,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Error while calling the agent: {exc}", file=sys.stderr)
            continue

        pretty_print_result(drug_name, indication, result)

    print("\nGoodbye! 👋")


if __name__ == "__main__":
    main()

