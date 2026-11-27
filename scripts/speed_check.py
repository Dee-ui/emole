"""speed_check.py: measure where Emolé's time goes, then say what to fix.

Run (Ollama running, or keys set for hosted providers):
    python scripts/speed_check.py
    python scripts/speed_check.py --chain groq:llama-3.3-70b-versatile --note "groq first try"

It asks four questions in one chat (a question, a follow-up, a chart, the first question
again) and prints, for every model call: the provider, seconds spent loading the model
(Ollama), how many prompt tokens were read and how many were written. Then a short
diagnosis in plain words. Nothing is written to your logs.
"""
import argparse
import json
import os
import time
import urllib.request

from emole import config
from emole.pipeline import engine, llm, prompts

QUESTIONS = [
    "What was Nigeria's population in 2023?",
    "and Ghana?",
    "Show internet use in Nigeria and Ghana since 2010 as a line chart.",
    "What was Nigeria's population in 2023?",
]


def ollama_info():
    host = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
    host = host if host.startswith("http") else "http://" + host
    try:
        with urllib.request.urlopen(host.rstrip("/") + "/api/version", timeout=5) as r:
            return json.loads(r.read().decode("utf-8")).get("version", "unknown")
    except Exception:
        return "not reachable"


def print_calls(calls):
    for c in calls:
        load = f"LOAD {c['load_s']:>5}s  " if c.get("load_s", 0) >= 1 else "             "
        rate = c["reply_tokens"] / c["reply_s"] if c.get("reply_s") else 0
        speed = f" ({rate:.1f} tok/s)" if rate else ""
        print(f"      {c['role']:<14} {c['provider']:<7} {c['wall_s']:>6}s  {load}read "
              f"{c['prompt_tokens']:>6,} tok   wrote {c['reply_tokens']:>4} tok{speed}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chain", default="")
    ap.add_argument("--note", default="")
    args = ap.parse_args()
    if args.chain:
        config.PROVIDER_CHAIN[:] = [c.strip() for c in args.chain.split(",") if c.strip()]
    config.LOG_QUERIES = False
    print("=" * 78)
    print(f"Emolé speed check  {time.strftime('%Y-%m-%d %H:%M')}  {args.note}")
    print("=" * 78)
    print(f"Mode {config.EMOLE_MODE} | chain {llm.describe_chain()}")
    if any(link.provider == "ollama" for link in llm.chain()):
        print(f"Ollama version {ollama_info()} | context {config.LLM_NUM_CTX:,} | "
              f"keep loaded {config.LLM_KEEP_ALIVE}")
    s = prompts.prompt_size()
    print(f"SQL prompt about {s['estimated_tokens']:,} tokens (estimate), {s['examples']} examples")

    print("\nStep A: warm-up (Ollama only)")
    mark, t0 = llm.mark(), time.time()
    llm.warm_up(background=False)
    print_calls(llm.calls_since(mark))
    print(f"      warm-up took {time.time() - t0:.1f}s")

    print("\nStep B: the questions, in one chat")
    history, all_calls, totals = [], [], []
    for i, q in enumerate(QUESTIONS, 1):
        out = engine.ask(q, history=list(history), log=False, save_chart_files=False)
        calls = [c for c in llm.CALLS if c["n"] > mark]
        mark = llm.mark()
        all_calls += calls
        totals.append(out["seconds"])
        print(f"\n  Q{i}: {q}")
        if out.get("resolved"):
            print(f"      understood as: {out['resolved']}")
        print(f"      -> [{out['kind']}] {out['text'][:110]}")
        print(f"      TOTAL {out['seconds']:.1f}s")
        print_calls(calls)
        if out["kind"] in ("text", "chart", "no_data"):
            history.append(out.get("resolved") or q)

    print(f"\nAverage per question: {sum(totals) / len(totals):.1f}s "
          f"(slowest {max(totals):.1f}s, fastest {min(totals):.1f}s)")
    print("\nDIAGNOSIS")
    reloads = [c for c in all_calls if c.get("load_s", 0) >= 1]
    if reloads:
        print(f"- Ollama LOADED the model again {len(reloads)} time(s). Close other AI apps; "
              "check OLLAMA_KEEP_ALIVE.")
    big = [c for c in all_calls
           if c["provider"] == "ollama" and c["prompt_tokens"] >= config.LLM_NUM_CTX * 0.85]
    if big:
        print("- A prompt nearly filled Ollama's context. Raise LLM_NUM_CTX in config.py.")
    skipped = [c for c in all_calls if c["skipped"]]
    if skipped:
        print(f"- {len(skipped)} call(s) fell back to the next provider: {skipped[0]['skipped']}.")
    if not (reloads or big or skipped):
        print("- No problems found.")


if __name__ == "__main__":
    main()
