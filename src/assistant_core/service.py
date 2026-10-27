import logging

from assistant_core.errors import InvalidRequest, ProviderError
from assistant_core.models import Intent, Message, Response, Source
from assistant_core.responder import TemplateResponder
from assistant_core.router import route
from assistant_core.tools import parse_credits, tuition

log = logging.getLogger("assistant_core")


class AssistantService:
    """Single entry point for the assistant.

    Every collaborator — settings, knowledge sources and the response
    generator — is injected, so tests can supply fakes and a real AI
    provider can replace the template without editing this class.
    """

    def __init__(self, settings, offices, handbook, responder):
        self.settings = settings
        self.offices = offices
        self.handbook = handbook
        self.responder = responder
        self.fallback = TemplateResponder()

    def handle(self, msg: Message) -> Response:
        """Route one message and turn it into a Response.

        Provider failures never reach the caller: the template fallback
        answers instead and the response is flagged as degraded.
        """
        intent = route(msg.text, self.offices.names)
        if intent is Intent.GREETING:
            return Response(answer="Hello! I can help with offices, fees and rules.", intent=intent)
        if intent is Intent.FEE:
            return self._fee(msg.text)
        if intent is Intent.OFFICE:
            return self._office(msg.text, intent)
        return self._rule(msg.text)

    def _office(self, text: str, intent: Intent) -> Response:
        o = self.offices.find(text)
        if o is None:
            return Response(answer="Sorry, I don't know that yet.", intent=Intent.UNKNOWN)
        return Response(answer=f"{o.name}: room {o.room}, open {o.hours}.", intent=intent)

    def _fee(self, text: str) -> Response:
        try:
            credits, retake = parse_credits(text)
            total = tuition(
                credits,
                retake,
                self.settings.credit_rate_vnd,
                self.settings.retake_multiplier,
                self.settings.max_credits,
            )
        except InvalidRequest as exc:
            log.info("fee request rejected: %s", exc.__class__.__name__)
            return Response(answer=str(exc), intent=Intent.FEE, degraded=True)
        return Response(answer=f"Your tuition is {total:,} VND", intent=Intent.FEE)

    def _rule(self, text: str) -> Response:
        rule = self.handbook.search(text)
        if rule is None:
            return Response(answer="Sorry, I don't know that yet.", intent=Intent.UNKNOWN)
        sources = [Source(id=rule.id, title=rule.title)]
        try:
            return Response(answer=self.responder.explain(text, rule), intent=Intent.RULE, sources=sources)
        except ProviderError:
            log.warning("provider failed; using template fallback")
            answer = self.fallback.explain(text, rule)
            return Response(answer=answer, intent=Intent.RULE, sources=sources, degraded=True)
