from typing import Protocol

from assistant_core.errors import ProviderError


class Responder(Protocol):
    def explain(self, question: str, rule_text: str) -> str: ...


class TemplateResponder:
    def explain(self, question: str, rule_text: str) -> str:
        return rule_text


class StubLLMResponder:
    def __init__(self, fail: bool = False):
        self.fail = fail

    def explain(self, question: str, rule_text: str) -> str:
        if self.fail:
            raise RuntimeError("stub provider unavailable")
        return f"Based on: {rule_text}"


def make_responder(provider: str) -> Responder:
    if provider == "stub":
        return StubLLMResponder()
    if provider == "template":
        return TemplateResponder()
    raise ProviderError(f"unknown provider {provider!r}")

