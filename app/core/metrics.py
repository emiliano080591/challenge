import time
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI
from prometheus_client import Counter, Histogram

CHAT_REQUESTS = Counter(
    "kopi_chat_requests_total",
    "Total de requests a /chat por resultado",
    labelnames=("status",),
)

CHAT_PAYLOAD_BYTES = Histogram(
    "kopi_chat_payload_bytes",
    "Tamaño del payload JSON de entrada (bytes)",
    buckets=(128, 256, 512, 1_024, 2_048, 4_096, 8_192, 16_384),
)

CHAT_RESPONSE_CHARS = Histogram(
    "kopi_chat_response_chars",
    "Tamaño (chars) del último mensaje devuelto",
    buckets=(50, 100, 200, 400, 800, 1600, 3200),
)

CONVERSATIONS_STARTED = Counter(
    "kopi_conversations_started_total",
    "Conversaciones nuevas iniciadas",
)

MESSAGES_TOTAL = Counter(
    "kopi_messages_total",
    "Mensajes registrados por rol",
    labelnames=("role",),
)

OPENAI_REQUESTS = Counter(
    "kopi_openai_requests_total",
    "Llamadas a OpenAI por estado",
    labelnames=("status", "error_type"),
)

OPENAI_LATENCY = Histogram(
    "kopi_openai_latency_seconds",
    "Latencia de llamadas a OpenAI",
    buckets=(0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)

OPENAI_TOKENS = Counter(
    "kopi_openai_tokens_total",
    "Tokens usados en llamadas a OpenAI",
    labelnames=("kind",),  # prompt|completion|total
)


def setup_metrics(app: FastAPI) -> None:
    # HTTP metrics (requests, latency, por endpoint/status)
    Instrumentator().instrument(app).expose(app, include_in_schema=False, endpoint="/metrics")


class Timer:
    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.elapsed = time.perf_counter() - self.t0
