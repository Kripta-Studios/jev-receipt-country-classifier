"""Evaluate a fixed cohort against separate metadata and reviewed document labels."""


def summarize_observable(cases):
    """Keep extraction/provider failures in the cohort denominator.

    UNKNOWN is an abstention, OTHER is a country assertion outside the configured
    list. An image review assesses the whole OCR-to-country pipeline; it cannot
    by itself establish whether a mistake originated in OCR or in Jev.
    """
    summary = {}
    for variant in sorted({row["variant"] for row in cases}):
        rows = [r for r in cases if r["variant"] == variant]
        if len({r["id"] for r in rows}) != len(rows):
            raise ValueError("Duplicate case in evaluation cohort")
        ok = [r for r in rows if r["status"] == "ok"]
        visible = [r for r in rows if r["reviewed_image_country"] != "UNKNOWN"]
        unknown = [r for r in rows if r["reviewed_image_country"] == "UNKNOWN"]
        asserted_unknown = [
            r
            for r in ok
            if r["reviewed_image_country"] == "UNKNOWN" and r["candidate"] != "UNKNOWN"
        ]
        summary[variant] = {
            "n": len(rows),
            "successful": len(ok),
            "errors": len(rows) - len(ok),
            "metadata_matches": sum(r["candidate"] == r["metadata_country"] for r in ok),
            "reviewed_image_matches": sum(
                r["candidate"] == r["reviewed_image_country"] for r in ok
            ),
            "image_country_observable": len(visible),
            "observable_correct": sum(
                r["status"] == "ok" and r["candidate"] == r["reviewed_image_country"]
                for r in visible
            ),
            "observable_abstentions": sum(
                r["status"] == "ok" and r["candidate"] == "UNKNOWN" for r in visible
            ),
            "observable_wrong_country": sum(
                r["status"] == "ok"
                and r["candidate"] not in ("UNKNOWN", r["reviewed_image_country"])
                for r in visible
            ),
            "image_country_unobservable": len(unknown),
            "reasonable_abstentions": sum(
                r["status"] == "ok" and r["candidate"] == "UNKNOWN" for r in unknown
            ),
            "unsupported_country_assertions": len(asserted_unknown),
            "unsupported_metadata_matches": sum(
                r["candidate"] == r["metadata_country"] for r in asserted_unknown
            ),
            "unsupported_probability_at_least_0_9": sum(
                r.get("probability", 0) >= 0.9 for r in asserted_unknown
            ),
        }
    return summary
