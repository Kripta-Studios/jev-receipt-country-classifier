"""Country decisions, literal evidence baseline, and explicit review routing."""

import re

from .prompts import make_payload

# Deliberately narrow baseline: no brand/headquarters, language, or shared currency guesses.
PATTERNS = {
    "ES": [r"\b(?:ESPAÑA|ESPANA|SPAIN)\b", r"\+34[\s(\d]", r"\bCIF\s*[:.]?\s*[A-Z]\s*\d{7,8}\b"],
    "FR": [r"\bFRANCE\b", r"\+33[\s(\d]", r"\bSIRET\b", r"\bSIREN\b"],
    "DE": [r"\bDEUTSCHLAND\b", r"\bGERMANY\b", r"\+49[\s(\d]", r"\bDE\s*\d{9}\b"],
    "IT": [
        r"\bITALIA\b",
        r"\bITALY\b",
        r"\+39[\s(\d]",
        r"\b(?:P\.?\s*IVA|PARTITA IVA)\s*[:.]?\s*\d{11}\b",
    ],
    "GB": [r"\bUNITED KINGDOM\b", r"\+44[\s(\d]", r"\bGB\s*\d{9}\b", r"\bGBP\b"],
    "US": [r"\bUNITED STATES\b", r"\bUSA\b", r"\bUS\s*\$", r"\bUSD\b"],
    "CA": [r"\bCANADA\b", r"\bCAD\b", r"\b(?:GST\s*[/&]\s*HST|TPS\s*[/&]\s*TVQ)\b"],
}


def literal_evidence(text):
    evidence = []
    for i, line in enumerate(text.splitlines(), 1):
        for country, patterns in PATTERNS.items():
            if any(re.search(pattern, line, re.I) for pattern in patterns):
                evidence.append({"country": country, "line_number": i, "quote": line})
    return evidence


def rule_baseline(text):
    evidence = literal_evidence(text)
    candidates = sorted({r["country"] for r in evidence})
    return {"country": candidates[0] if len(candidates) == 1 else "UNKNOWN", "evidence": evidence}


def route(answer, evidence_probability=None, policy=None):
    policy = policy or {"min_probability": 0.9, "min_margin": 0.15, "min_evidence": 0}
    choice = answer["choice"]
    probs = answer["probabilities"]
    ordered = sorted(probs.values(), reverse=True)
    margin = ordered[0] - ordered[1] if len(ordered) > 1 else ordered[0]
    reason = None
    if policy.get("automatic_enabled") is False:
        reason = "automation_not_validated"
    elif choice == "UNKNOWN":
        reason = "insufficient_evidence"
    elif choice == "OTHER":
        reason = "outside_configured_countries"
    elif probs[choice] < policy["min_probability"] or margin < policy["min_margin"]:
        reason = "uncertain_distribution"
    elif policy.get("min_evidence", 0) > 0 and (
        evidence_probability is None or evidence_probability < policy["min_evidence"]
    ):
        reason = "weak_location_evidence"
    return {
        "country": choice if reason is None else None,
        "candidate": choice,
        "status": "classified" if reason is None else "review",
        "review_reason": reason,
        "probability": probs[choice],
        "margin": margin,
        "confidence": answer["confidence"],
        "probabilities": probs,
        "location_evidence_probability": evidence_probability,
    }


def classify(text, client, variant="focused-v2", policy=None, countries=None):
    if not text.strip():
        return {
            "country": None,
            "candidate": "UNKNOWN",
            "status": "review",
            "review_reason": "empty_extraction",
            "network_attempts": 0,
        }
    result = client.evaluate(make_payload(text, variant, countries))
    answers = result["response"]["answers"]
    decision = route(answers["country"], answers.get("location_evidence", {}).get("noul"), policy)
    return {
        **decision,
        "variant": variant,
        "model": result["response"]["model"],
        "literal_evidence": literal_evidence(text),
        "usage": result["response"]["usage"],
        "request_sha256": result["request_sha256"],
        "cache_hit": result["cache_hit"],
        "network_attempts": result["network_attempts"],
        "elapsed_s": result["elapsed_s"],
    }
