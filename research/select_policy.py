"""Select the policy using real development data only; freeze before test requests."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from jev_tickets.metrics import summarize


def main():
    target = ROOT / "evaluation/frozen-policy.json"
    if target.exists():
        raise ValueError("Policy already frozen; preserve this experiment and use a new version")
    source = ROOT / "evaluation/real-dev-predictions.jsonl"
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
    expected_ids = {
        json.loads(line)["id"]
        for line in (ROOT / "evaluation/real-manifest.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if json.loads(line)["split"] == "dev"
    }
    candidates = []
    for variant in ("baseline-v1", "focused-v2"):
        records = [r for r in rows if r["variant"] == variant]
        if {r["id"] for r in records} != expected_ids or len(records) != len(expected_ids):
            raise ValueError("Real development predictions incomplete or duplicated")
        for threshold in (0.5, 0.7, 0.8, 0.9, 0.95, 0.98, 0.99, 1.0):
            for evidence in (0, 0.5, 0.8) if variant == "focused-v2" else (0,):
                policy = {
                    "min_probability": threshold,
                    "min_margin": 0.15,
                    "min_evidence": evidence,
                }
                metrics = summarize(records, policy)
                feasible = (
                    metrics["accepted"] >= 50
                    and metrics["accepted_errors"] / metrics["accepted"] <= 0.02
                    and metrics["accepted_error_wilson95"][1] <= 0.05
                )
                candidates.append(
                    {"variant": variant, "policy": policy, "feasible": feasible, "metrics": metrics}
                )
    feasible = [c for c in candidates if c["feasible"]]
    # Maximize usable coverage within the declared development error criterion.
    selected = (
        max(
            feasible,
            key=lambda c: (
                c["metrics"]["accepted"],
                -c["metrics"]["accepted_errors"],
                c["variant"] == "baseline-v1",
            ),
        )
        if feasible
        else max(
            candidates,
            key=lambda c: c["metrics"]["accepted_correct"] - 10 * c["metrics"]["accepted_errors"],
        )
    )
    if not feasible:
        selected["policy"]["automatic_enabled"] = False
    frozen = {
        "variant": selected["variant"],
        "policy": selected["policy"],
        "selected_on": "real development split only",
        "selected_at": datetime.now(timezone.utc).isoformat(),
        "criterion": "maximize accepted cases with >=50 accepted, empirical error <=2%, Wilson95 upper error <=5%; otherwise disable automation",
        "development_metrics": selected["metrics"],
        "criterion_met": bool(feasible),
        "development_predictions_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "prompt_source_sha256": hashlib.sha256(
            (ROOT / "jev_tickets/prompts.py").read_bytes()
        ).hexdigest(),
    }
    target.write_text(json.dumps(frozen, indent=2), encoding="utf-8")
    (ROOT / "evaluation/policy-candidates.json").write_text(
        json.dumps(candidates, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in frozen.items() if k != "development_metrics"}, indent=2))


if __name__ == "__main__":
    main()
