import re
from typing import Tuple

TOPIC_RE = re.compile(r'\btopic\s*:\s*(.+?)(;|$)', re.I)
STANCE_RE = re.compile(r'\bstance\s*:\s*(.+?)(;|$)', re.I)

def extract_topic_stance(text: str) -> Tuple[str, str]:
    """
    Agente simple:
    - Primero intenta extracción por regex 'Topic:'/'Stance:'
    - Si no, usa heurística: topic = primeras 10–12 palabras; stance = texto restante
    (Puedes mejorarlo invocando un LLM extractor si lo deseas)
    """
    topic, stance = None, None
    if not text:
        return "general debate", "bot's position"
    m1 = TOPIC_RE.search(text)
    m2 = STANCE_RE.search(text)
    if m1:
        topic = m1.group(1).strip()
    if m2:
        stance = m2.group(1).strip()
    if not topic or not stance:
        words = text.strip().split()
        topic = topic or " ".join(words[:12]) or "general debate"
        stance = stance or "bot's position"
    return topic[:128], stance[:128]
