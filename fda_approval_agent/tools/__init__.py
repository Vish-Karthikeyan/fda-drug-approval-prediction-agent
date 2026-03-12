"""
Tool package for FDA approval prediction agent.

Each tool wraps an external data source (ClinicalTrials.gov, openFDA, PubMed, FDA
advisory committee records) and exposes a Python function with a stable, structured
dictionary output. All tools must catch errors and return an ``{"error": ...}`` entry
instead of raising in production.
"""

