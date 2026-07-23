#!/usr/bin/env python3
"""Score a practice candidate for experiment eligibility.

This score is triage evidence, never an adoption decision.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SOURCE_POINTS = {"S": 25, "A": 20, "B": 12, "C": 5}


def bounded_int(data: dict, key: str, low: int = 0, high: int = 5) -> int:
    value = data.get(key)
    if not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f"{key} must be an integer from {low} to {high}.")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", help="Candidate JSON file.")
    args = parser.parse_args()

    path = Path(args.candidate)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        tier = str(data.get("source_tier", "")).upper()
        if tier not in SOURCE_POINTS:
            raise ValueError("source_tier must be S, A, B, or C.")

        reproducibility = bounded_int(data, "reproducibility")
        evidence = bounded_int(data, "evidence")
        relevance = bounded_int(data, "relevance")
        reversibility = bounded_int(data, "reversibility")
        automation = bounded_int(data, "automation_value")
        risk = bounded_int(data, "risk")

        raw = (
            SOURCE_POINTS[tier]
            + reproducibility * 4
            + evidence * 4
            + relevance * 3
            + reversibility * 2
            + automation * 2
        )
        score = round(raw * (1 - 0.08 * risk), 1)

        if score >= 75 and risk <= 2:
            recommendation = "ELIGIBLE_FOR_CONTROLLED_EXPERIMENT"
        elif score >= 55:
            recommendation = "KEEP_AS_CANDIDATE"
        else:
            recommendation = "REJECT_OR_REVISIT"

        result = {
            "name": data.get("name", path.stem),
            "score": score,
            "recommendation": recommendation,
            "warning": "This score does not authorize adoption. Run experiments and skill evals.",
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
