"""nl_to_sql.py: turn a question (plus its NAME HINTS) into one SQL string, or NO_SQL."""
import re

from emole import config
from emole.pipeline import llm
from emole.pipeline.prompts import build_repair_messages, build_sql_messages


def clean(text: str) -> str:
    """Remove markdown fences, 'SQL:' labels and comment lines if a model added them."""
    text = re.sub(r"```[a-zA-Z]*", "", text or "").replace("```", "")
    text = re.sub(r"^\s*(sql|query)\s*:\s*", "", text.strip(), flags=re.I)
    lines = [ln for ln in text.splitlines() if not ln.strip().startswith("--")]
    return "\n".join(lines).strip()


def _ask(messages) -> str:
    sql = clean(llm.chat(messages, temperature=0.0, max_tokens=config.MAX_SQL_TOKENS))
    if sql.upper().startswith("NO_SQL"):
        return "NO_SQL"
    return sql


def generate_sql(question: str, hints: str) -> str:
    return _ask(build_sql_messages(question, hints))


def repair_sql(question: str, hints: str, bad_sql: str, problem: str) -> str:
    """Second chance: show the model its SQL and exactly what is wrong."""
    return _ask(build_repair_messages(question, hints, bad_sql, problem))
