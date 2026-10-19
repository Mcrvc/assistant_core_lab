"""Command-line interface for assistant_core."""

import logging
import sys
import time

from pydantic import ValidationError

from assistant_core.config import load_settings
from assistant_core.errors import AssistantError
from assistant_core.knowledge import Handbook, OfficeDirectory
from assistant_core.logging_setup import setup_logging
from assistant_core.models import Message
from assistant_core.responder import StubLLMResponder
from assistant_core.service import AssistantService

log = logging.getLogger("assistant_core")


def build_service() -> AssistantService:
    """Build and initialize AssistantService with runtime dependencies."""
    settings = load_settings()
    setup_logging(settings.log_level)
    offices = OfficeDirectory.from_csv(settings.data_dir / "offices.csv")
    handbook = Handbook.from_json(settings.data_dir / "handbook.json")
    responder = StubLLMResponder()
    return AssistantService(settings, offices, handbook, responder)


def run_one(service: AssistantService, text: str) -> None:
    """Execute single query, log JSON metadata to stderr, print answer to stdout."""
    start = time.perf_counter()
    msg = Message(text=text)
    response = service.handle(msg)
    latency_ms = round((time.perf_counter() - start) * 1000, 1)

    log.info(
        "handled",
        extra={
            "intent": response.intent.value,
            "latency_ms": latency_ms,
            "session": msg.session_id,
            "degraded": response.degraded,
        },
    )
    print(response.answer)


def main() -> None:
    """CLI entrypoint supporting one-shot argument or interactive prompt."""
    service = build_service()
    if len(sys.argv) > 1:
        run_one(service, " ".join(sys.argv[1:]))
        return

    print("assistant ready")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        if line.lower() == "quit":
            break
        try:
            run_one(service, line)
        except (AssistantError, ValidationError) as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()
