"""The provider chain: fall back on busy providers, rest them, and never print a key."""
import httpx
import openai
import pytest

from emole import config
from emole.pipeline import llm


class Fake:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), 0

    def __call__(self, link, messages, temperature, max_tokens, stop):
        self.calls += 1
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r, {"prompt_tokens": 100, "reply_tokens": 5}


@pytest.fixture
def two_fakes(monkeypatch):
    first, second = Fake([]), Fake([])
    for name, fake in (("first", first), ("second", second)):
        monkeypatch.setitem(config.PROVIDERS, name, {"kind": name})
        monkeypatch.setitem(llm.SENDERS, name, fake)
    monkeypatch.setattr(config, "PROVIDER_CHAIN", ["first:a", "second:b"])
    llm.reset_cooldowns()
    yield first, second
    llm.reset_cooldowns()


def test_busy_first_provider_falls_back_and_rests(two_fakes):
    first, second = two_fakes
    first.replies = [llm.ProviderError("too many requests (429)")]
    second.replies = ["SELECT 1", "SELECT 2"]
    mark = llm.mark()
    assert llm.chat([{"role": "user", "content": "hi"}]) == "SELECT 1"
    call = llm.calls_since(mark)[-1]
    assert call["provider"] == "second" and call["skipped"] == ["first:a"]
    assert llm.chat([{"role": "user", "content": "hi"}]) == "SELECT 2"   # first is resting now
    assert first.calls == 1 and "resting" in llm.describe_chain()


def test_a_resting_provider_is_still_tried_last(two_fakes):
    first, second = two_fakes
    first.replies = [llm.ProviderError("Ollama is not running"), "SELECT 9"]
    second.replies = [llm.ProviderError("429"), llm.ProviderError("429")]
    with pytest.raises(llm.AllProvidersBusy):
        llm.chat([{"role": "user", "content": "hi"}])
    # both are resting now; the next question still tries them, and the first one is back
    assert llm.chat([{"role": "user", "content": "hi"}]) == "SELECT 9"


def test_all_providers_busy(two_fakes):
    first, second = two_fakes
    first.replies = [llm.ProviderError("429")]
    second.replies = [llm.ProviderError("timeout")]
    with pytest.raises(llm.AllProvidersBusy) as err:
        llm.chat([{"role": "user", "content": "hi"}])
    assert len(err.value.attempts) == 2


def test_mode_default_chains(monkeypatch):
    monkeypatch.setattr(config, "PROVIDER_CHAIN", [])
    monkeypatch.setattr(config, "EMOLE_MODE", "local")
    assert [lk.provider for lk in llm.chain()] == ["ollama"]
    monkeypatch.setattr(config, "EMOLE_MODE", "public")
    assert [lk.provider for lk in llm.chain()] == ["groq", "gemini", "gemini"]
    monkeypatch.setattr(config, "PROVIDER_CHAIN", ["nonsense"])
    with pytest.raises(ValueError):
        llm.chain()


def test_missing_key_is_named_never_printed(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(config, "PROVIDER_CHAIN", ["groq:some-model"])
    llm.reset_cooldowns()
    assert "KEY MISSING" in llm.describe_chain()
    with pytest.raises(llm.AllProvidersBusy, match="GROQ_API_KEY is not set"):
        llm.chat([{"role": "user", "content": "hi"}])
    pretend = "pretend-value-" + "123456"
    monkeypatch.setenv("GROQ_API_KEY", pretend)
    llm.reset_cooldowns()
    assert pretend not in llm.describe_chain() and "(key set)" in llm.describe_chain()


class FakeOpenAI:
    """Stands in for openai.OpenAI; records the request and raises or answers."""
    last = {}

    def __init__(self, **kwargs):
        self.chat = self
        self.completions = self
        FakeOpenAI.client = kwargs

    def create(self, **kwargs):
        FakeOpenAI.last = kwargs
        if FakeOpenAI.error:
            raise FakeOpenAI.error
        msg = type("M", (), {"content": "SELECT 1"})
        usage = type("U", (), {"prompt_tokens": 50, "completion_tokens": 3})
        return type("R", (), {"choices": [type("C", (), {"message": msg})], "usage": usage})


def _status_error(cls, code):
    resp = httpx.Response(code, request=httpx.Request("POST", "https://example.invalid"))
    return cls("refused", response=resp, body=None)


@pytest.fixture
def fake_openai(monkeypatch):
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    monkeypatch.setenv("GEMINI_API_KEY", "pretend-value-for-tests")
    monkeypatch.setattr(llm, "_clients", {})
    llm.reset_cooldowns()
    FakeOpenAI.error = None
    yield FakeOpenAI
    llm.reset_cooldowns()


def test_gemini_request_shape(fake_openai, monkeypatch):
    monkeypatch.setattr(config, "PROVIDER_CHAIN", ["gemini:gemini-3.5-flash-lite"])
    assert llm.chat([{"role": "user", "content": "q"}], temperature=0.0, max_tokens=400) == "SELECT 1"
    sent = fake_openai.last
    assert "temperature" not in sent                       # Gemini 3 guidance: leave it at default
    assert sent["max_tokens"] == config.HOSTED_MIN_TOKENS  # room for thinking before the SQL
    assert fake_openai.client["max_retries"] == 0          # the chain decides, not the client


@pytest.mark.parametrize("cls,code,kind", [(openai.RateLimitError, 429, "busy"),
                                           (openai.AuthenticationError, 401, "broken"),
                                           (openai.NotFoundError, 404, "broken"),
                                           (openai.InternalServerError, 503, "busy")])
def test_http_errors_become_busy_or_broken(fake_openai, cls, code, kind):
    fake_openai.error = _status_error(cls, code)
    link = llm.Link("gemini", "gemini-3.5-flash-lite")
    with pytest.raises(llm.ProviderError) as err:
        llm._send_openai(link, [{"role": "user", "content": "q"}], 0.0, 10, None)
    assert err.value.kind == kind
