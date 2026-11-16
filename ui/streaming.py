"""D5 bonus: progressively display an answer already returned by the API."""

import re
from collections.abc import Iterator
from time import sleep


def answer_chunks(answer: str, word_delay: float = 0.02, max_duration: float = 1.5) -> Iterator[str]:
    """Keep all whitespace and Markdown; cap the added wait for long answers."""
    chunks = re.findall(r"\S+\s*|\s+", answer)
    pauses = max(len(chunks) - 1, 1)
    delay = max(0.0, min(word_delay, max_duration / pauses))
    for position, chunk in enumerate(chunks):
        if position and delay:
            sleep(delay)
        yield chunk


def display_answer(answer: str, animate: bool = True) -> None:
    """Animate a NEW answer; use animate=False for history and urgent notices."""
    import streamlit as st

    if animate:
        st.write_stream(answer_chunks(answer))
    else:
        st.markdown(answer)
