"""
Step 7 — Tracing setup (OpenTelemetry + Phoenix)

Call setup_tracing() BEFORE you create clients or import your app code.
From then on, every Anthropic call and every LangGraph node is recorded
automatically and sent to the Phoenix dashboard at http://localhost:6006
"""
import os

from phoenix.otel import register

# "phoenix" is the service name in docker-compose.yml
PHOENIX_ENDPOINT = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://phoenix:6006/v1/traces")


def setup_tracing(project_name: str = "ai-lab"):
    provider = register(
        project_name=project_name,   # groups traces in the dashboard
        endpoint=PHOENIX_ENDPOINT,
        auto_instrument=True,        # patch Anthropic SDK + LangChain/LangGraph automatically
        batch=True,                  # send spans in the background, in batches
        verbose=False,
    )
    tracer = provider.get_tracer("ai-lab")
    return tracer, provider
