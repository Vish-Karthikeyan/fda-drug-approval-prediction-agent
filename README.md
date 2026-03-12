# FDA Approval Prediction Agent

This project implements an interactive **FDA drug approval prediction agent** using **DSPy** and the **ReAct ** paradigm.

The agent:
- Uses DSPy Signatures and Modules (`ReAct`, `ChainOfThought`).
- Calls multiple tools (ClinicalTrials.gov, openFDA, PubMed, FDA AdCom calendar).
- Produces an **approval probability**, **key risks/tailwinds**, and a short **executive summary**.

---

## Environment & Installation

1. **Python version**: Python 3.10+ recommended.

2. **Install dependencies** (from the project root):

```bash
pip install -r requirements.txt
```

3. **Environment variables / API keys**

Preferred: create a `.env` file (git-ignored) in the project root:

```bash
OPENAI_API_KEY=sk-...
FDA_API_KEY=...          # optional, for higher openFDA rate limits
NCBI_EMAIL=you@email.com
NCBI_API_KEY=...         # optional
RUN_OPTIMIZER=false      # set true to run DSPy optimizer (slower, more tokens)
DSPY_LM_MODEL=openai/gpt-4o
```

---

## Project Structure

- `extra_credit.py` – Course assignment entry; defines:
  - `YourAgentSignature`: describes an FDA approval prediction assistant.
  - `YourAgent`: thin wrapper around the core FDA agent.
  - `run_demo()`: demonstrates the agent on two historical cases.

- `fda_approval_agent/`
  - `config.py` – Loads configuration (API keys, model name, optimizer flag).
  - `main.py` – Standalone demo entrypoint for the FDA approval agent.
  - `tools/`
    - `clinical_trials.py` – ClinicalTrials.gov search wrapper.
    - `open_fda.py` – openFDA FAERS & historical approvals tools.
    - `pubmed.py` – PubMed (NCBI Entrez) trial evidence retrieval.
    - `adcom.py` – FDA Advisory Committee vote lookup (web-scraping based).
  - `signatures/`
    - `fda_signatures.py` – All DSPy Signatures (`TrialQualityAssessor`, `SafetySignalAnalyzer`, `ComparableApprovalAnalyzer`, `ApprovalProbabilityEstimator`).
  - `modules/`
    - `fda_agent.py` – `FDAApprovalAgent` module using DSPy `ReAct` + reasoning chain.
  - `data/`
    - `ground_truth.json` – Placeholder for cached dataset (not required to run).
    - `cache/` – For any future response caching.
  - `optimization/`
    - `optimizer.py` – Ground-truth dataset builder and DSPy optimizer (`BootstrapFewShot`).
  - `tests/`
    - `test_tools.py` – Structural tests for all tools and error-handling behavior.
    - `test_agent.py` – End-to-end agent test verifying approval probability is in \[0.0, 1.0\].

---

## How to Run the Agent

### 1. Interactive Terminal REPL (`repl.py`)

From the project root:

```bash
python repl.py
```

This starts a conversational, terminal-side agent:
- You are prompted for **drug name**, **indication**, and optional **mechanism of action**.
- The agent uses DSPy + ReAct with all tools (ClinicalTrials.gov, openFDA, PubMed, AdCom).
- It prints:
  - Estimated approval probability.
  - Confidence.
  - Key risks and key tailwinds.
  - A short executive summary.

Type `quit` at any prompt to exit the REPL.

---

### 2. Extra Credit Demo (`extra_credit.py`)

From the project root:

```bash
python extra_credit.py
```

What it does:
- Configures DSPy with the model specified in `.env` (or defaults).
- Creates an instance of `YourAgent` (which wraps `FDAApprovalAgent`).
- Runs two demo inputs:
  - `drug=pembrolizumab; indication=NSCLC; mechanism=PD-1 inhibitor`
  - `drug=aducanumab; indication=Alzheimer's disease; mechanism=amyloid beta antibody`
- Prints a conversational response including:
  - Estimated approval probability.
  - Confidence level.
  - Key risks and tailwinds.
  - Executive summary.

You can modify `test_inputs` in `run_demo()` or import `YourAgent` elsewhere to ask your own queries. The expected input format is:

```text
drug=DRUG_NAME; indication=CONDITION; mechanism=MECHANISM (optional)
```

### 3. Core FDA Agent Demo (`fda_approval_agent/main.py`)

From the project root:

```bash
python -m fda_approval_agent.main
```

This:
- Loads config and configures DSPy.
- Optionally builds a small ground-truth dataset and runs the DSPy optimizer if `RUN_OPTIMIZER=true`.
- Runs two historical examples (Keytruda approval, Aducanumab rejection).
- Prints:
  - `Approval Probability`
  - `Confidence`
  - `Key Risks`
  - `Key Tailwinds`
  - `Summary`

---

## Running Tests

From the project root:

```bash
pytest
```

This will:
- Verify each tool returns a correctly structured dictionary and handles API errors without uncaught exceptions.
- Check that the `FDAApprovalAgent` pipeline runs end-to-end and that `approval_probability` is in \[0.0, 1.0\].

Note: Tests may perform real network calls to public APIs (ClinicalTrials.gov, openFDA, PubMed, FDA.gov), so they require internet access.

---

## Notes & Limitations
- API response formats can evolve; parsing heuristics are designed to be robust but may not capture all edge cases.
- Some quantities (e.g., median review time) are approximated with simple heuristics to keep the implementation compact.
