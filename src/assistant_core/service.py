import logging

from assistant_core.errors import InvalidRequest, ProviderError
from assistant_core.guard import PRIVATE_REPLY, is_private_request
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

    def __init__(self, settings, offices, handbook, responder, rag=None):
        self.settings = settings
        self.offices = offices
        self.handbook = handbook
        self.responder = responder
        self.fallback = TemplateResponder()
        self.rag = rag

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
        if self.rag is not None:
            if is_private_request(text):
                return Response(answer=PRIVATE_REPLY, intent=Intent.UNKNOWN, path="abstain")
            return self.rag.answer(text)
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


def build_service(settings) -> AssistantService:
    """Assemble an AssistantService from settings (single wiring point)."""
    from assistant_core.knowledge import Handbook, OfficeDirectory
    from assistant_core.llm import make_llm
    from assistant_core.rag.answerer import RagAnswerer
    from assistant_core.rag.chunker import load_folder
    from assistant_core.rag.index import make_index
    from assistant_core.responder import make_responder
    from assistant_core.tools import run_tool_call

    d = settings.data_dir
    offices = OfficeDirectory.from_csv(d / "offices.csv")
    handbook = Handbook.from_json(d / "handbook.json")
    responder_name = settings.llm_provider if settings.llm_provider in ("stub", "template") else "template"
    rag = None
    if settings.kb_dir.exists():
        chunks = load_folder(settings.kb_dir)
        if chunks:
            index = make_index(settings.retrieval_kind, chunks)
            llm = (
                None
                if settings.llm_provider == "template"
                else make_llm(
                    settings.llm_provider,
                    settings.llm_model,
                    settings.llm_base_url,
                    settings.llm_api_key,
                    settings.llm_timeout_s,
                )
            )

            def tool_runner(raw: str) -> str | None:
                return run_tool_call(raw, settings.credit_rate_vnd, settings.retake_multiplier, settings.max_credits)

            rag = RagAnswerer(
                index,
                llm,
                settings.retrieval_min_score,
                prompt_version=settings.prompt_version,
                tool_runner=tool_runner,
            )
    return AssistantService(settings, offices, handbook, make_responder(responder_name), rag)
