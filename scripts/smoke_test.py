"""smoke_test.py: ask Emolé 15 everyday questions with real models, and save what happened.

Run each provider on its own, so the results can be compared (guide, Part 6):
    python scripts/smoke_test.py --chain ollama:qwen2.5:7b-instruct --label ollama
    python scripts/smoke_test.py --chain groq:llama-3.3-70b-versatile --label groq
    python scripts/smoke_test.py --chain gemini:gemini-3.5-flash-lite --label gemini35
The forced failure (proves the fallback with a real error, not a pretend one):
    python scripts/smoke_test.py --chain "groq:no-such-model,gemini:gemini-3.5-flash-lite"
                                 --label forced --only 1        (all on one line)

Each run prints a table and writes logs/smoke_<label>_<date-time>.md (git-ignored).
Nothing is written to the question log.
"""
import argparse
import time
from datetime import datetime

from emole import config
from emole.pipeline import engine, llm, prompts

QUESTIONS = [
    ("single country", "What was Nigeria's population in 2023?"),
    ("ranking", "Which 10 countries have the highest internet use?"),
    ("trend", "How has inflation in Nigeria changed since 2015?"),
    ("region total", "What is the total population of ECOWAS?"),
    ("region weighted average", "What share of people in West Africa have access to electricity?"),
    ("cross-industry", "Which African countries grew their economy fastest in 2023 while under 60% "
                       "of people had electricity?"),
    ("latest year", "What is the latest life expectancy in Ghana?"),
    ("follow-up", "and Kenya?"),
    ("identity", "Who are you?"),
    ("out-of-range year", "How many air passengers did Nigeria carry in 2025?"),
    ("groups compared", "Compare life expectancy across continents in 2023."),
    ("per person", "How many air passengers per person did Nigeria and Kenya have in 2023?"),
    ("several measures", "Show air passengers, GDP growth and inflation for Nigeria from 2018 to 2022."),
    ("cause question", "Did internet growth cause GDP growth in Kenya?"),
    ("opinion", "Which president ruined Nigeria's economy?"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chain", default="", help='e.g. "groq:llama-3.3-70b-versatile" (default: from .env)')
    ap.add_argument("--label", default="run")
    ap.add_argument("--only", type=int, default=0, help="ask only the first N questions")
    ap.add_argument("--pause", type=float, default=0.0, help="seconds to wait between questions "
                    "(use 20 to 30 for a free tier with a tokens-per-minute limit)")
    args = ap.parse_args()
    if args.chain:
        config.PROVIDER_CHAIN[:] = [c.strip() for c in args.chain.split(",") if c.strip()]
    config.LOG_QUERIES = False
    size = prompts.prompt_size()
    print(f"Chain: {llm.describe_chain()}")
    print(f"SQL prompt: {size['characters']:,} characters, about {size['estimated_tokens']:,} tokens "
          f"(estimate), {size['examples']} worked examples, version {size['version']}")
    llm.warm_up(background=False)
    rows, history = [], []
    questions = QUESTIONS[: args.only] if args.only else QUESTIONS
    for i, (kind, q) in enumerate(questions, 1):
        out = engine.ask(q, history=list(history), log=False, save_chart_files=True)
        if out["kind"] in ("text", "chart", "no_data"):
            history.append(out.get("resolved") or q)
        rows.append((i, kind, q, out))
        print(f"\nQ{i} [{kind}] {q}")
        if out.get("resolved"):
            print(f"   understood as: {out['resolved']}")
        if out.get("sql") and out["sql"] != "NO_SQL":
            print(f"   SQL: {' '.join(out['sql'].split())}")
        flags = ", ".join(f for f in (
            "fixed in code: " + "/".join(out["fixed_in_code"]) if out["fixed_in_code"] else "",
            "repaired" if out["repaired"] else "",
            "template answer" if out["grounded"] is False else "") if f)
        print(f"   -> [{out['kind']}] {out['text'][:400]}")
        print(f"   {out['seconds']}s | {out['provider'] or 'no model'} | "
              f"tokens read {out['tokens']['prompt']:,}, written {out['tokens']['reply']:,}"
              + (f" | {flags}" if flags else ""))
        print(f"   {out['speed']}")
        if args.pause and i < len(questions):
            time.sleep(args.pause)
    _save(args.label, rows, size)


def _save(label, rows, size):
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    path = config.LOGS_DIR / f"smoke_{label}_{stamp}.md"
    total = sum(r[3]["seconds"] for r in rows)
    lines = [f"# Smoke test: {label} ({stamp})", "",
             f"Chain: {llm.describe_chain()}  ",
             f"SQL prompt: about {size['estimated_tokens']:,} tokens (estimate), prompt {size['version']}  ",
             f"Questions: {len(rows)}, total {total:.1f}s, average {total / max(len(rows), 1):.1f}s", "",
             "| # | type | kind | seconds | provider | fixed / repaired | answer (start) |",
             "|---|---|---|---|---|---|---|"]
    for i, kind, _q, out in rows:
        fixed = "/".join(out["fixed_in_code"]) + (" repaired" if out["repaired"] else "")
        text = out["text"][:120].replace("|", "/").replace("\n", " ")
        lines.append(f"| {i} | {kind} | {out['kind']} | {out['seconds']} | {out['provider']} | "
                     f"{fixed.strip()} | {text} |")
    lines += ["", "## Full answers and SQL", ""]
    for i, kind, q, out in rows:
        lines += [f"### Q{i} ({kind}): {q}", ""]
        if out.get("resolved"):
            lines.append(f"Understood as: {out['resolved']}  ")
        if out.get("sql"):
            lines += ["```sql", out["sql"], "```"]
        lines += ["", out["text"], "", f"`{out['speed']}`", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSaved: {path}\nAverage {total / max(len(rows), 1):.1f}s per question.")


if __name__ == "__main__":
    main()
