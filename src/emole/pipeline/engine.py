"""engine.py: Emolé's ONE front door: ask(question, history) -> answer.

The terminal chat, the evaluator (Step 3) and the website (Step 4) all call this same
function, so a fix here helps everywhere and test scores measure what users get.

The steps, in order:
  0. Follow-up     "and Ghana?" is rewritten into a full question from the chat history
                   (shown as "Understood as: ...").
  1. Quick chat    greetings, thanks and "who are you" are answered by code.
  2. Guards        no model call when we already know the answer is "no":
                     - a place name that matches nothing       -> "I don't recognise ..."
                     - a year outside every measure's years     -> "The latest for X is YEAR"
  3. Write SQL     the model gets the question plus NAME HINTS (exact codes from names.py)
                   and writes ONE query, or NO_SQL for chat.
  4. Check + run   code checks the SQL (checks.py). Certain problems are fixed instantly
                   in code; anything else goes back to the model ONCE with the reason.
                   Hard checks must pass; soft checks only ask while a repair is left.
                   The query then runs read-only (executor.py).
  5. Empty guard   no rows, or only empty values -> "I found no matching data" + the years
                   each measure really has.
  6. Text or chart decided by the question's words and the result's shape.
  7. Sentence      quick fixed sentence, or the model's sentence after its checks
                   (responder.py), then the notes added by CODE: group coverage, the
                   aviation caveat and the latest-year note (notes.py).
"""
import re
import time

from emole import config
from emole.pipeline import (
    catalog,
    checks,
    executor,
    followup,
    llm,
    names,
    nl_to_sql,
    notes,
    query_log,
    responder,
    visualizer,
)
from emole.pipeline.columns import COLUMNS, columns_in

YEAR = re.compile(r"\b(19\d{2}|20\d{2})\b")
BUSY_TEXT = ("I'm getting a lot of questions right now and every model I use is busy. Please try "
             "again in a minute.")


def _blank(df) -> bool:
    return df is None or len(df) == 0 or bool(df.isna().all().all())


def year_guard(question: str):
    """A reply (no model call) when the question asks only for years no measure has."""
    years = sorted({int(y) for y in YEAR.findall(question)})
    if not years:
        return None
    facts = catalog.get_facts()
    if all(y < facts["year_min"] or y > facts["year_max"] for y in years):
        return (f"I have data from {facts['year_min']} to {facts['year_max']} only, so I can't answer "
                f"for {', '.join(map(str, years))}.")
    cols = columns_in(question)
    if not cols:
        return None
    out = []
    for c in cols:
        meta = catalog.column(c)
        if all(y > meta["latest_year"] or y < meta["first_year"] for y in years):
            label = COLUMNS[c]["label"]
            out.append(f"The latest year I have for {label} is {meta['latest_year']} "
                       f"(the data runs from {meta['first_year']}).")
    if out and len(out) == len(cols):
        return " ".join(out) + " Ask me for that year instead?"
    return None


def ask(question: str, history: list = None, phrase: bool = True, log: bool = True,
        save_chart_files: bool = True) -> dict:
    """Answer one question. history = earlier questions in this chat, oldest first.
    phrase=False skips the sentence and the chart (the evaluator only needs the SQL and the rows).

    Returns a dict: kind ('text' | 'chart' | 'chat' | 'no_data' | 'unknown_name' | 'busy' | 'error'),
    text, sql, df, chart, notes, resolved, repaired, fixed_in_code, grounded, provider, seconds."""
    t0 = time.time()
    bookmark = llm.mark()
    original = question
    out = {"question": original, "resolved": None, "kind": "error", "text": "", "sql": None, "df": None,
           "chart": None, "notes": [], "repaired": False, "fixed_in_code": [], "checks": [],
           "grounded": None, "provider": "", "seconds": 0.0}

    def finish():
        calls = llm.calls_since(bookmark)
        out["seconds"] = round(time.time() - t0, 2)
        out["provider"] = llm.last_provider(calls)
        out["tokens"] = {"prompt": sum(c["prompt_tokens"] for c in calls),
                         "reply": sum(c["reply_tokens"] for c in calls)}
        out["speed"] = llm.summary(calls, out["seconds"])
        if log:
            query_log.write({k: out[k] for k in ("question", "resolved", "kind", "sql", "repaired",
                                                  "fixed_in_code", "checks", "grounded", "provider",
                                                  "tokens", "seconds")} | {"mode": config.EMOLE_MODE})
        return out

    try:
        # 0. Follow-up -> full question
        question = followup.resolve(question, history or [])
        if question != original:
            out["resolved"] = question

        # 1. Greetings, thanks, "who are you": code answers
        if responder.is_quick_chat(question):
            out["kind"], out["text"] = "chat", responder.chat_answer(question)
            return finish()

        # 2. Guards
        res = names.resolve(question)
        if res.unknown:
            out["kind"], out["text"] = "unknown_name", names.unknown_reply(res)
            return finish()
        guard = year_guard(question)
        if guard:
            out["kind"], out["text"] = "no_data", guard
            return finish()

        # 3. Write SQL
        hints = names.hints_text(res)
        sql = nl_to_sql.generate_sql(question, hints)
        out["sql"] = sql
        if sql == "NO_SQL":
            out["kind"] = "chat"
            out["text"] = responder.chat_answer(question) if phrase else ""
            return finish()

        # 4. Check, fix, run, repair
        df, shown = None, ""
        for attempt in range(config.SQL_REPAIR_ATTEMPTS + 1):
            last = attempt >= config.SQL_REPAIR_ATTEMPTS
            out["sql"], fixed = checks.apply_instant_fixes(question, out["sql"])
            out["fixed_in_code"] += [f for f in fixed if f not in out["fixed_in_code"]]
            problem = checks.hard_problem(question, res, out["sql"])
            if not problem and not last:
                problem = checks.soft_problem(question, out["sql"])
            shown = problem or ""
            if not problem:
                try:
                    df = executor.run_sql(out["sql"])
                    break
                except Exception as e:
                    shown = str(e).splitlines()[0][:300]
                    problem = shown
            out["checks"].append(shown)
            if attempt < config.SQL_REPAIR_ATTEMPTS:
                out["sql"] = nl_to_sql.repair_sql(question, hints, out["sql"], problem)
                out["repaired"] = True
                if out["sql"] == "NO_SQL":
                    break
        if df is None:
            out["text"] = ("I couldn't turn that into a working query. Try naming the country or "
                           f"group, the measure and the year. (Last problem: {shown})")
            return finish()
        out["df"] = df

        # 5. Empty guard
        used = checks.metric_columns(out["sql"])
        if _blank(df):
            out["kind"] = "no_data"
            cover = " ".join(catalog.coverage_sentence(c) for c in used[:3])
            out["text"] = ("I found no matching data for that. " + cover).strip()
            return finish()
        out["notes"] = notes.all_notes(question, out["sql"], df, res)
        if df.attrs.get("truncated"):
            out["notes"].append(f"Showing the first {executor.MAX_ROWS:,} rows only.")
        if not phrase:
            out["kind"] = visualizer.decide_output(question, df)
            return finish()

        # 6. Text or chart, 7. sentence
        out["kind"] = visualizer.decide_output(question, df)
        reply = responder.answer(question, df)
        out["grounded"] = reply["grounded"]
        text = reply["text"]
        if out["kind"] == "chart":
            out["chart"] = visualizer.build_chart(question, df, save_files=save_chart_files)
            text += out["chart"]["note"]
        out["text"] = " ".join([text.strip()] + out["notes"]).strip()
        return finish()

    except llm.AllProvidersBusy as e:
        out["kind"] = "busy"
        out["text"] = (BUSY_TEXT if config.EMOLE_MODE == "public"
                       else f"{e} Is Ollama running? Start the Ollama app and ask again.")
        out["checks"].append(str(e))
        return finish()
    except catalog.DatabaseOutOfDate as e:
        out["text"] = str(e)
        return finish()
