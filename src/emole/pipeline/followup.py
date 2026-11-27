"""followup.py: understand follow-up questions in the same chat.

  "What was Nigeria's GDP growth in 2020?"   ->  answered
  "and Ghana?"                               ->  rewritten as
  "What was Ghana's GDP growth in 2020?"

The rewritten question is shown to the user ("Understood as: ..."), so nothing is hidden.
To keep it fast and safe:
- Only messages that LOOK like follow-ups are rewritten (short, or starting with
  "and", "what about", "same for", or pointing back with "that", "those", "it").
- The rewrite may only use numbers (years, amounts) that appear in the message or in
  the earlier questions. A new number means the model made something up, so the
  original message is kept.
"""
import re

from emole import config
from emole.pipeline import llm
from emole.pipeline.prompts import build_followup_messages

CUES = re.compile(
    r"^\s*(and|but|also|so|now|then|what about|how about|what of|same for|same but|only|instead|"
    r"add|remove|drop|compare (it|that|them)|make it|show (it|that|them)|in \d{4}|for \d{4})\b"
    r"|\b(it|that|those|these|them|same|previous|above|instead|again|as well|too)\b",
    re.IGNORECASE)
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def looks_like_followup(question: str) -> bool:
    return bool(CUES.search(question)) or len(question.split()) <= 4


def resolve(question: str, history: list) -> str:
    """history: earlier questions in this chat, oldest first (already resolved)."""
    if not history or not looks_like_followup(question):
        return question
    earlier = history[-config.MAX_HISTORY_TURNS:]
    try:
        out = llm.chat(build_followup_messages(earlier, question), temperature=0.0, max_tokens=80)
    except Exception:
        return question
    out = out.strip().strip('"').strip()
    if not out or len(out) > 300 or "\n" in out or "SELECT" in out.upper():
        return question
    allowed = set(NUM.findall(question + " " + " ".join(earlier)))
    if any(n not in allowed for n in NUM.findall(out)):      # invented a number: do not trust it
        return question
    return out
