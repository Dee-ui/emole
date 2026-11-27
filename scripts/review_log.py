"""review_log.py: list the questions Emolé struggled with, so they become test questions.

Run:  python scripts/review_log.py
Shows answers you marked /bad, errors, questions that needed a model repair, answers that
failed a sentence check, and how often each instant fix and each provider was used.
"""
from collections import Counter

from emole.pipeline import query_log


def main():
    entries = query_log.read_all()
    asked = [e for e in entries if "kind" in e]
    bad = [e for e in entries if e.get("feedback") == "bad"]
    print(f"{len(asked)} questions logged, {len(bad)} marked /bad")
    print("Answer types:", dict(Counter(e["kind"] for e in asked)))
    print("Providers:", dict(Counter(e.get("provider") or "none" for e in asked)))
    print("Instant fixes:", dict(Counter(f for e in asked for f in e.get("fixed_in_code") or [])))
    sections = [
        ("Marked /bad by you", bad),
        ("Ended in an error", [e for e in asked if e["kind"] == "error"]),
        ("Every model was busy", [e for e in asked if e["kind"] == "busy"]),
        ("Needed a model repair", [e for e in asked if e.get("repaired")]),
        ("Sentence failed a check (template used)", [e for e in asked if e.get("grounded") is False]),
    ]
    for title, rows in sections:
        print(f"\n=== {title} ({len(rows)}) ===")
        for e in rows[-15:]:
            print(f"- {e['question']}")
            if e.get("sql"):
                print(f"    SQL: {' '.join(str(e['sql']).split())[:180]}")
            for c in e.get("checks") or []:
                print(f"    check: {c[:160]}")


if __name__ == "__main__":
    main()
