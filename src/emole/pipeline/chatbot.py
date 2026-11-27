"""chatbot.py: talk to Emolé in the terminal. Run:  python scripts/chat.py

Commands you can type:
  /sql       show or hide the SQL
  /speed     show or hide the "[speed]" line (where the time went, which provider answered)
  /providers show the provider chain and whether each key is set (never the key itself)
  /good      mark the last answer as right   (saved to logs/queries.jsonl)
  /bad       mark the last answer as wrong   (these become test questions in Step 3)
  exit       leave
"""
from emole import config
from emole.pipeline import catalog, engine, llm, prompts, query_log

WELCOME = (f"\nHi, {prompts.INTRODUCTION}\n"
           "Ask me about any country's economy, energy, health, internet use or air travel,\n"
           "over time and across regions. Commands: /sql, /speed, /providers, /good, /bad, exit\n")


def show(result: dict, show_sql: bool, show_speed: bool) -> None:
    if result.get("resolved"):
        print(f"   [understood as] {result['resolved']}")
    if show_sql and result.get("sql") and result["sql"] != "NO_SQL":
        tags = []
        if result.get("fixed_in_code"):
            tags.append("fixed in code: " + ", ".join(result["fixed_in_code"]))
        if result.get("repaired"):
            tags.append("repaired by the model")
        tag = f" ({'; '.join(tags)})" if tags else ""
        print(f"   [SQL{tag}] {' '.join(result['sql'].split())}")
    if result.get("grounded") is False:
        print("   [the model's sentence failed a check, so a safe template answer is shown]")
    print("Emolé:", result["text"])
    df = result.get("df")
    if df is not None and len(df) > 1 and result["kind"] in ("text", "chart"):
        print(df.head(12).to_string(index=False))
        if len(df) > 12:
            print(f"   ... {len(df) - 12} more rows")
    if result.get("chart") and result["chart"].get("png"):
        print(f"   Chart: {result['chart']['png']}")
        print(f"          {result['chart']['html']} (interactive)")
    if show_speed and config.SPEED_LOG:
        print("  ", result.get("speed", ""))


def main() -> None:
    print(WELCOME)
    print("Mode:", config.EMOLE_MODE, "| Providers:", llm.describe_chain())
    print(catalog.data_summary(), "\n")
    llm.warm_up(background=True)
    show_sql, show_speed, last, history = config.SHOW_SQL, True, None, []
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEmolé: Goodbye!")
            break
        if not question:
            continue
        low = question.lower()
        if low in ("exit", "quit"):
            print("Emolé: Goodbye!")
            break
        if low == "/sql":
            show_sql = not show_sql
            print(f"   SQL display is now {'ON' if show_sql else 'OFF'}")
            continue
        if low == "/speed":
            show_speed = not show_speed
            print(f"   Speed line is now {'ON' if show_speed else 'OFF'}")
            continue
        if low == "/providers":
            print("  ", llm.describe_chain())
            continue
        if low in ("/good", "/bad"):
            if last:
                query_log.write({"feedback": low[1:], "question": last["question"], "sql": last["sql"]})
                print("   Thanks, noted.")
            continue
        last = engine.ask(question, history=history)
        if last["kind"] in ("text", "chart", "no_data"):
            history.append(last.get("resolved") or question)
        show(last, show_sql, show_speed)


if __name__ == "__main__":
    main()
