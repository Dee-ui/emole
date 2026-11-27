"""llm.py: the ONE place that talks to a language model, through a chain of providers.

Every other file calls chat(messages, ...) and gets text back. Which model answers is
decided here, from the provider chain (config.PROVIDER_CHAIN, or the mode's default):

  local / team mode:  ollama:qwen2.5:7b-instruct          (your laptop)
  public mode:        groq:...  ->  gemini:...  ->  gemini:...  (free hosted models)

How the chain works, in plain words:
  1. Try the first provider that is not "resting" after an error. Resting providers are
     tried last instead of never, so a single-provider chain (local Ollama) is retried as
     soon as you fix the problem, and a demo with every provider resting still tries.
  2. If it says "too many requests" (HTTP 429), is out of daily quota, is too slow, or
     its server fails, mark it cooling down for a minute and try the next one.
  3. If its key is wrong or the model name does not exist, mark it cooling down for
     ten minutes (it will not fix itself) and print one warning naming the provider
     and the error number, never the key.
  4. If every provider fails, raise AllProvidersBusy. Step 4's website turns that into
     the polite "the demo is full today" message.

Every call is recorded (provider, model, tokens read and written, seconds), so the
terminal can print a "[speed]" line and the question log can say who answered.
"""
import os
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass

from emole import config

# Which file made the call -> a friendly step name for the timing report.
_ROLES = {"nl_to_sql": "SQL", "responder": "answer", "followup": "follow-up"}

CALLS = deque(maxlen=500)          # the most recent calls, newest last
_counter = 0
_lock = threading.Lock()
_cooldown = {}                     # "provider:model" -> time.time() when it may be tried again
_warned = set()
_clients = {}


class ProviderError(Exception):
    """One provider failed. kind: 'busy' (try again soon) or 'broken' (fix the settings)."""

    def __init__(self, message: str, kind: str = "busy", retry_after: float = None):
        super().__init__(message)
        self.kind = kind
        self.retry_after = retry_after


class AllProvidersBusy(RuntimeError):
    """Every provider in the chain failed or is cooling down."""

    def __init__(self, attempts: list):
        self.attempts = attempts
        detail = "; ".join(f"{a['provider']}: {a['error']}" for a in attempts) or "no provider configured"
        super().__init__(f"No model could answer right now ({detail}).")


class MissingKey(ProviderError):
    def __init__(self, provider: str, key_env: str):
        super().__init__(f"{key_env} is not set in .env (needed for {provider})", kind="broken")


@dataclass
class Link:
    provider: str
    model: str

    @property
    def name(self) -> str:
        return f"{self.provider}:{self.model}"


# ---------------------------------------------------------------------------
# THE CHAIN
# ---------------------------------------------------------------------------
def chain() -> list:
    """The providers to try, in order, as Link objects."""
    if config.EMOLE_MODE not in config.MODES:
        raise ValueError(f"EMOLE_MODE must be one of {', '.join(config.MODES)}, not {config.EMOLE_MODE!r}")
    entries = config.PROVIDER_CHAIN or config.DEFAULT_CHAINS[config.EMOLE_MODE]
    links = []
    for entry in entries:
        provider, _, model = entry.partition(":")
        provider, model = provider.strip().lower(), model.strip()
        if provider not in config.PROVIDERS or not model:
            raise ValueError(f"Provider chain entry {entry!r} must look like 'groq:<model name>'. "
                             f"Known providers: {', '.join(config.PROVIDERS)}")
        links.append(Link(provider, model))
    return links


def describe_chain() -> str:
    """'groq:llama-3.3-70b-versatile (key set) -> gemini:... (KEY MISSING)', never the key."""
    parts = []
    for link in chain():
        spec = config.PROVIDERS[link.provider]
        status = ""
        if spec.get("key_env"):
            status = " (key set)" if os.environ.get(spec["key_env"]) else " (KEY MISSING in .env)"
        wait = _cooldown.get(link.name, 0) - time.time()
        if wait > 0:
            status += f" (resting {wait:.0f}s)"
        parts.append(link.name + status)
    return " -> ".join(parts)


def reset_cooldowns() -> None:
    _cooldown.clear()


# ---------------------------------------------------------------------------
# SENDERS: one per kind of provider. Each returns (text, usage dict).
# ---------------------------------------------------------------------------
def _send_ollama(link, messages, temperature, max_tokens, stop):
    import ollama
    spec = config.PROVIDERS[link.provider]
    client = _clients.get("ollama")
    if client is None:
        client = _clients["ollama"] = ollama.Client(host=spec["host"], timeout=config.LLM_TIMEOUT_SEC)
    options = {"temperature": temperature, "num_ctx": config.LLM_NUM_CTX}
    if max_tokens:
        options["num_predict"] = max_tokens
    if stop:
        options["stop"] = stop
    if config.LLM_NUM_THREAD:
        options["num_thread"] = config.LLM_NUM_THREAD
    extra = {"think": False} if link.model.startswith("qwen3") else {}
    try:
        resp = client.chat(model=link.model, messages=messages, options=options,
                           keep_alive=config.LLM_KEEP_ALIVE, **extra)
    except Exception as e:
        text = str(e).lower()
        if "timed out" in text or "timeout" in type(e).__name__.lower():
            raise ProviderError(f"took longer than {config.LLM_TIMEOUT_SEC}s") from e
        if "not found" in text and "model" in text:
            raise ProviderError(f"model {link.model} is not pulled (run: ollama pull {link.model})",
                                kind="broken") from e
        if "connect" in text or "refused" in text:
            raise ProviderError("Ollama is not running (start the Ollama app)") from e
        raise ProviderError(f"{type(e).__name__}: {str(e)[:120]}") from e

    def field(name):
        try:
            return resp[name]
        except Exception:
            return getattr(resp, name, None)

    ns = lambda v: round((v or 0) / 1e9, 2)          # noqa: E731  (Ollama reports nanoseconds)
    usage = {"prompt_tokens": field("prompt_eval_count") or 0, "reply_tokens": field("eval_count") or 0,
             "load_s": ns(field("load_duration")), "prompt_s": ns(field("prompt_eval_duration")),
             "reply_s": ns(field("eval_duration"))}
    return field("message")["content"].strip(), usage


def _send_openai(link, messages, temperature, max_tokens, stop):
    import openai
    spec = config.PROVIDERS[link.provider]
    key = os.environ.get(spec["key_env"], "").strip()
    if not key:
        raise MissingKey(link.provider, spec["key_env"])
    client = _clients.get(link.provider)
    if client is None:
        client = _clients[link.provider] = openai.OpenAI(
            api_key=key, base_url=spec["base_url"], timeout=config.HOSTED_TIMEOUT_SEC,
            max_retries=0)                       # the chain decides what to do next, not the client
    kwargs = {"model": link.model, "messages": messages}
    if spec.get("temperature", True):
        kwargs["temperature"] = temperature
    if max_tokens:
        kwargs["max_tokens"] = max(max_tokens, config.HOSTED_MIN_TOKENS)
    if stop:
        kwargs["stop"] = stop
    try:
        resp = client.chat.completions.create(**kwargs)
    except openai.RateLimitError as e:          # 429: too many requests, or out of quota
        raise ProviderError("too many requests or out of free quota (429)",
                            retry_after=_retry_after(e)) from e
    except (openai.APITimeoutError, openai.APIConnectionError) as e:
        raise ProviderError(f"no answer within {config.HOSTED_TIMEOUT_SEC}s or no connection") from e
    except openai.InternalServerError as e:
        raise ProviderError(f"server error ({e.status_code})") from e
    except (openai.AuthenticationError, openai.PermissionDeniedError) as e:
        raise ProviderError(f"key refused ({e.status_code}): check {spec['key_env']} in .env",
                            kind="broken") from e
    except openai.NotFoundError as e:
        raise ProviderError(f"model {link.model!r} not found (404)", kind="broken") from e
    except openai.APIStatusError as e:          # 400 and other refusals
        raise ProviderError(f"request refused ({e.status_code})", kind="broken") from e
    text = (resp.choices[0].message.content or "").strip() if resp.choices else ""
    if not text:
        raise ProviderError("empty reply")
    u = resp.usage
    usage = {"prompt_tokens": getattr(u, "prompt_tokens", 0) or 0,
             "reply_tokens": getattr(u, "completion_tokens", 0) or 0}
    return text, usage


def _retry_after(error) -> float:
    try:
        return float(error.response.headers.get("retry-after"))
    except Exception:
        return None


SENDERS = {"ollama": _send_ollama, "openai": _send_openai}


# ---------------------------------------------------------------------------
# THE ONE FUNCTION EVERYTHING CALLS
# ---------------------------------------------------------------------------
def chat(messages, temperature=0.0, max_tokens=None, stop=None, role=None) -> str:
    """Send messages to the first provider that answers. Returns the reply text.
    Raises AllProvidersBusy when nobody could answer."""
    if role is None:                              # name the step after the file that called us
        caller = sys._getframe(1).f_globals.get("__name__", "")
        role = _ROLES.get(caller.rsplit(".", 1)[-1], caller.rsplit(".", 1)[-1] or "model")
    attempts = []
    now = time.time()
    links = chain()
    links = ([lk for lk in links if _cooldown.get(lk.name, 0) <= now]          # ready first,
             + [lk for lk in links if _cooldown.get(lk.name, 0) > now])        # resting last
    for link in links:
        sender = SENDERS[config.PROVIDERS[link.provider]["kind"]]
        t0 = time.time()
        try:
            text, usage = sender(link, messages, temperature, max_tokens, stop)
        except ProviderError as e:
            rest = config.ERROR_COOLDOWN_SEC if e.kind == "broken" else (
                e.retry_after or config.RATE_LIMIT_COOLDOWN_SEC)
            _cooldown[link.name] = time.time() + rest
            attempts.append({"provider": link.name, "error": str(e)})
            if e.kind == "broken" and link.name not in _warned:
                _warned.add(link.name)
                print(f"[providers] {link.name} skipped: {e}", file=sys.stderr)
            continue
        _record(role, link, usage, time.time() - t0, attempts)
        return text
    raise AllProvidersBusy(attempts)


def _record(role, link, usage, wall, attempts):
    global _counter
    entry = {"role": role, "provider": link.provider, "model": link.model,
             "thread": threading.get_ident(), "wall_s": round(wall, 2),
             "prompt_tokens": usage.get("prompt_tokens", 0), "reply_tokens": usage.get("reply_tokens", 0),
             "load_s": usage.get("load_s", 0), "prompt_s": usage.get("prompt_s", 0),
             "reply_s": usage.get("reply_s", 0), "skipped": [a["provider"] for a in attempts]}
    with _lock:
        _counter += 1
        entry["n"] = _counter
        CALLS.append(entry)
    if link.provider == "ollama" and entry["prompt_tokens"] >= config.LLM_NUM_CTX * 0.85:
        print(f"[speed] WARNING: the {role} prompt used {entry['prompt_tokens']:,} of "
              f"{config.LLM_NUM_CTX:,} context tokens. Raise LLM_NUM_CTX in config.py.")


def mark() -> int:
    """A bookmark: calls made after this number belong to the current question."""
    with _lock:
        return _counter


def calls_since(bookmark: int, this_thread_only: bool = True) -> list:
    me = threading.get_ident()
    with _lock:
        return [c for c in CALLS if c["n"] > bookmark and (not this_thread_only or c["thread"] == me)]


def summary(calls: list, total_s: float) -> str:
    """[speed] 3.1s total | SQL groq:llama-3.3-70b-versatile 1.2s (read 5,210, wrote 61) | ..."""
    parts, model_s = [], 0.0
    for c in calls:
        model_s += c["wall_s"]
        load = f", LOADING {c['load_s']}s" if c.get("load_s", 0) >= 1 else ""
        skipped = f", after skipping {', '.join(c['skipped'])}" if c["skipped"] else ""
        parts.append(f"{c['role']} {c['provider']}:{c['model']} {c['wall_s']}s (read "
                     f"{c['prompt_tokens']:,}, wrote {c['reply_tokens']:,}{load}{skipped})")
    if not calls:
        parts.append("no model call (answered in code)")
    other = max(total_s - model_s, 0)
    return f"[speed] {total_s:.1f}s total | " + " | ".join(parts) + f" | other {other:.1f}s"


def last_provider(calls: list) -> str:
    """Which provider wrote the SQL (or the last call), for the log."""
    sql = [c for c in calls if c["role"] == "SQL"]
    c = (sql or calls or [None])[-1]
    return f"{c['provider']}:{c['model']}" if c else ""


def warm_up(background: bool = True) -> None:
    """Ollama only: load the model and read the long SQL prompt once at start, so the
    first real question is fast. The SQL prompt goes LAST, so it stays in Ollama's memory."""
    if not config.LLM_WARM_UP or not any(link.provider == "ollama" for link in chain()):
        return

    def run():
        t0 = time.time()
        try:
            from emole.pipeline.prompts import build_answer_messages, build_sql_messages
            chat(build_answer_messages("How many people live in Nigeria?", " population\n1"),
                 max_tokens=1, role="warm-up answer")
            chat(build_sql_messages("How many people live in Nigeria?", "NAME HINTS: none"),
                 max_tokens=1, role="warm-up SQL")
            print(f"[speed] model loaded and SQL prompt read in {time.time() - t0:.1f}s")
        except Exception as e:                    # never stop the program over a warm-up
            print(f"[speed] warm-up skipped ({e})")
    if background:
        threading.Thread(target=run, daemon=True).start()
    else:
        run()
