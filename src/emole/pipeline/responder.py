"""responder.py: turn a SQL result into a sentence, and PROVE it is honest.

Four checks on every sentence the model writes:
  number check     every number in the sentence must appear in the result (or the
                   question). One stray number and the sentence is thrown away.
  full sentence    at least three real words, never a bare number.
  no causation     words that make one measure the cause of another ("caused", "led to",
                   "because of", "due to", "drove", "resulted in" ...) are not allowed,
                   because the data shows what moved together, not why (decision E-25).
  no verdicts      blame, praise or political judgement words are not allowed.
A failed sentence gets ONE rewrite with the reason; if that fails too, a plain
template sentence built by code is used instead.

Quick answers: a result that is one value for one country and one year gets a fixed,
correct sentence from columns.py with no model call at all.
"""
import re
from datetime import date, datetime

import pandas as pd

from emole import config
from emole.pipeline import catalog, llm
from emole.pipeline.columns import COLUMNS
from emole.pipeline.prompts import INTRODUCTION, build_answer_messages, chat_system_prompt

_NUM = re.compile(r"(?<![\w.])-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.])-?\d+(?:\.\d+)?")
CAUSAL = re.compile(
    r"\b(caus(e|ed|es|ing)|led to|lead to|leads to|leading to|because of|due to|drove|drive[sn]?|"
    r"driven by|driving|resulted in|results in|result of|as a result|thanks to|owing to|"
    r"contribut(ed|es|ing) to|fuell?ed|triggered|boosted by|attributable to|responsible for|"
    r"impact of|effect of)\b", re.I)
VERDICT = re.compile(r"\b(fault|blame[sd]?|corrupt\w*|incompeten\w*|mismanag\w*|ruin(ed|s)?|"
                     r"(good|bad|great|terrible|failed) (government|leadership|president|policy))\b", re.I)
ANALYTIC = re.compile(r"\b(change|changed|grow|grew|growth in|increase|decrease|rise|rose|fall|fell|"
                      r"compare|compared|versus|vs|rank|average|share of|difference|than|per person|"
                      r"per capita|why|cause|trend)\b", re.I)
IDENTITY_COLUMNS = {"country", "iso3", "year", "group_name"}


# ---------------------------------------------------------------------------
# numbers
# ---------------------------------------------------------------------------
def numbers_in(text: str) -> list:
    out = []
    for tok in _NUM.findall(str(text)):
        clean = tok.replace(",", "")
        out.append((float(clean), len(clean.split(".")[1]) if "." in clean else 0))
    return out


def _allowed(question: str, df, extra_text: str = "") -> list:
    allowed = [v for v, _ in numbers_in(question + " " + extra_text)] + [float(len(df))]
    for col in df.columns:
        info = COLUMNS.get(str(col).replace("_per_person", ""))
        if info:
            allowed += [v for v, _ in numbers_in(info["sentence"])]
        for v in df[col].dropna().tolist():
            if isinstance(v, bool):
                continue
            if isinstance(v, (int, float)):
                allowed.append(float(v))
            elif isinstance(v, (pd.Timestamp, datetime, date)):
                allowed += [float(v.year), float(v.month), float(v.day)]
            else:
                allowed += [x for x, _ in numbers_in(v)]
    for c in df.columns:                                  # units such as "per 1,000 live births"
        base = str(c).replace("_per_person", "").replace("_year", "")
        if base in catalog.get_facts()["columns"]:
            allowed += [v for v, _ in numbers_in(catalog.column(base)["unit"])]
    return allowed + [abs(a) for a in allowed]


def is_grounded(answer: str, question: str, df, extra_text: str = "") -> bool:
    allowed = _allowed(question, df, extra_text)
    for value, decimals in numbers_in(answer):
        if not any(round(a, decimals) == value for a in allowed):
            return False
    return True


def is_full_sentence(text: str) -> bool:
    first = re.split(r"(?<=[.!?])\s", text.strip())[0]
    return len(re.findall(r"[A-Za-z]{2,}", first)) >= 3


def sentence_problem(text: str, question: str, df) -> str:
    """'' when the sentence passes every check, else the reason (shown to the model)."""
    if not is_grounded(text, question, df):
        return "It contains a number that is not in RESULT. Copy the numbers exactly."
    if not is_full_sentence(text):
        return "Write a complete sentence that says what was measured, where and when."
    m = CAUSAL.search(text)
    if m:
        return (f"Do not say one measure caused another (you wrote \"{m.group(0)}\"). Describe the "
                "numbers side by side only.")
    m = VERDICT.search(text)
    if m:
        return f"Give no opinion or verdict (you wrote \"{m.group(0)}\"). Report the numbers only."
    return ""


# ---------------------------------------------------------------------------
# formatting
# ---------------------------------------------------------------------------
def _plain(v):
    return v.item() if hasattr(v, "item") and not isinstance(v, (str, bytes)) else v


def fmt(v, decimals: int = 2) -> str:
    v = _plain(v)
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return "no value"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, (pd.Timestamp, datetime, date)):
        return v.strftime("%d %b %Y")
    if isinstance(v, float):
        if v.is_integer() and abs(v) >= 1000:
            return f"{v:,.0f}"
        return f"{v:,.{decimals}f}"
    if isinstance(v, int):
        return f"{v:,}" if abs(v) >= 10000 or not 1900 <= v <= 2100 else str(v)
    return str(v)


def _decimals(col: str) -> int:
    info = COLUMNS.get(str(col).replace("_per_person", ""))
    if str(col).endswith("_per_person"):
        return 4
    return info["decimals"] if info else 2


def label(col) -> str:
    c = str(col)
    if c.endswith("_per_person"):
        return COLUMNS.get(c[:-11], {}).get("label", c[:-11]) + " per person"
    if c.endswith("_year") and c[:-5] in COLUMNS:
        return COLUMNS[c[:-5]]["label"] + " year"
    if c in COLUMNS:
        return COLUMNS[c]["label"]
    return c.replace("_", " ")


def df_to_text(df, max_rows: int = 30) -> str:
    view = df.head(max_rows).copy()
    for c in view.columns:
        if pd.api.types.is_numeric_dtype(view[c]) and c != "year" and not str(c).endswith("_year"):
            view[c] = view[c].map(lambda v, c=c: fmt(v, min(_decimals(c), 2) if _decimals(c) else 0))
    return view.to_string(index=False)


def template_answer(df) -> str:
    """The plain, always-correct fallback built by code."""
    def cells(row):
        return ", ".join(f"{label(c)}: {fmt(v, _decimals(c))}" for c, v in row.items() if c != "iso3")
    if len(df) == 1:
        return "Here is what the data shows: " + cells(df.iloc[0]) + "."
    lines = ["Here is what the data shows:"]
    for _, row in df.head(15).iterrows():
        lines.append("  - " + cells(row))
    if len(df) > 15:
        lines.append(f"  ...and {len(df) - 15:,} more rows (all of them are in the table and CSV).")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# quick answers: one country, one year, one measure
# ---------------------------------------------------------------------------
def quick_answer(question: str, df):
    if len(df) != 1 or ANALYTIC.search(question):
        return None
    measures = [c for c in df.columns if c not in IDENTITY_COLUMNS]
    if len(measures) != 1 or measures[0] not in COLUMNS or not {"country", "year"} <= set(df.columns):
        return None
    col = measures[0]
    row = df.iloc[0]
    value, year = _plain(row[col]), _plain(row["year"])
    if value is None or pd.isna(value) or pd.isna(year):
        return None
    info = COLUMNS[col]
    return info["sentence"].format(place=row["country"], value=fmt(float(value), info["decimals"]),
                                   year=int(year))


# ---------------------------------------------------------------------------
# the answer
# ---------------------------------------------------------------------------
def answer(question: str, df) -> dict:
    """{'text': ..., 'grounded': True/False, 'quick': True/False, 'rewrites': n}"""
    if config.QUICK_ANSWERS:
        text = quick_answer(question, df)
        if text and is_grounded(text, question, df):
            return {"text": text, "grounded": True, "quick": True, "rewrites": 0}
    messages = build_answer_messages(question, df_to_text(df))
    for attempt in range(2):
        try:
            text = llm.chat(messages, temperature=0.2, max_tokens=config.MAX_ANSWER_TOKENS)
        except Exception:
            break
        problem = sentence_problem(text, question, df)
        if not problem:
            return {"text": text, "grounded": True, "quick": False, "rewrites": attempt}
        messages = messages + [{"role": "assistant", "content": text},
                               {"role": "user", "content": f"Rewrite it. {problem}"}]
    return {"text": template_answer(df), "grounded": False, "quick": False, "rewrites": 1}


GREETING = re.compile(r"^\s*(hi|hello|hey|good (morning|afternoon|evening)|greetings)\b[\s,!.]*"
                      r"(emol[eé]|immy|there)?[\s!.?]*$", re.I)
WHO = re.compile(r"\b(who|what) (are|r) (you|u)\b|\byour name\b|\bintroduce yourself\b|"
                 r"\bwho is (emol[eé]|immy)\b|\bwhat is (emol[eé]|immy)\b|\bare you (emol[eé]|immy)\b", re.I)
THANKS = re.compile(r"^\s*(thanks|thank you|thx|cheers|great|ok(ay)?|nice)\b[\s\w!.,]*$", re.I)


def _thanks(question: str) -> bool:
    return bool(THANKS.match(question)) and len(question.split()) <= 4


OPINION = re.compile(
    r"\b(who|which \w+)\b.*\b(ruin(ed|s)?|destroy(ed|s)?|to blame|at fault|is corrupt|"
    r"(the )?(best|worst|better|good|bad) (president|leader|government|party|policy|minister))"
    r"|\b(your|you'?re) (opinion|view|verdict)\b|\bwhat do you think (of|about)\b", re.I)
OPINION_REPLY = ("I report the numbers side by side and don't give opinions or verdicts. I can show "
                 "you the figures for any country, group or year you're interested in.")


def chat_answer(question: str) -> str:
    """Non-data message. Greetings and identity questions are answered by code (no model call)."""
    if OPINION.search(question):
        return OPINION_REPLY
    if WHO.search(question):
        return f"{INTRODUCTION} {catalog.data_summary()}"
    if GREETING.match(question):
        return "Hello! " + f"{INTRODUCTION} Ask me about any country's economy, energy, health or travel."
    if _thanks(question):
        return "You're welcome. Ask me anything else about the countries in my data."
    try:
        text = llm.chat([{"role": "system", "content": chat_system_prompt()},
                         {"role": "user", "content": question}],
                        temperature=0.3, max_tokens=config.MAX_ANSWER_TOKENS)
    except Exception:
        text = ""
    facts = pd.DataFrame({"facts": [catalog.facts_text()]})
    if text and is_grounded(text, question, facts) and not CAUSAL.search(text) and not VERDICT.search(text):
        return text
    if re.search(r"\b(opinion|blame|ruin|fault|best president|worst|corrupt|should)\b", question, re.I):
        return OPINION_REPLY
    return f"{INTRODUCTION} {catalog.data_summary()}"


def is_quick_chat(question: str) -> bool:
    """True for messages that never need SQL: greetings, thanks, who-are-you."""
    return bool(GREETING.match(question) or WHO.search(question) or _thanks(question)
                or OPINION.search(question))
