"""
Step 8 — Your RAG graph as a real HTTP API (FastAPI)

Endpoints:
  GET  /health        is the service up?
  POST /ask           question in, answer + sources out (JSON)
  POST /ask/stream    same, but streams each graph step live (Server-Sent Events)
  GET  /docs          interactive API docs, generated automatically

Run (dev):  docker compose --profile rag --profile obs --profile api up -d --build
Then open:  http://localhost:8000/docs
"""
import json
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent

# 1. Tracing first (optional), so every request shows up in Phoenix
if os.getenv("TRACING") == "1":
    sys.path.insert(0, str(ROOT / "step7"))
    from tracing import setup_tracing
    setup_tracing("ai-lab-api")

# 2. Reuse the Step 5 graph unchanged
sys.path.insert(0, str(ROOT / "step5"))
import graph_rag  # noqa: E402

API_KEY = os.getenv("API_KEY")  # if set, clients must send it in the X-API-Key header
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")


# ---------- Request / response shapes (Pydantic again) ----------

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500, examples=["How much is shipping to Kosovo?"])


class Source(BaseModel):
    file: str
    preview: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    attempts: int
    trace: list[str]
    seconds: float


# ---------- App setup ----------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up at startup (remember the cold start in Step 6?):
    # load the embedding model and open the DB connection BEFORE the first user arrives
    graph_rag.embed(["warmup"])
    graph_rag.get_conn()
    print("Warm-up done, ready for requests")
    yield


app = FastAPI(title="Studio Lumi RAG API", version="1.0", lifespan=lifespan)

# Let a browser frontend (e.g. Next.js on localhost:3000) call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def check_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def start_state(question: str) -> dict:
    return {"question": question, "search_query": "", "chunks": [], "relevant": [],
            "answer": "", "attempts": 0, "trace": []}


def to_sources(chunks: list) -> list[Source]:
    return [Source(file=c["source"], preview=c["content"][:150]) for c in chunks]


# ---------- Endpoints ----------

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse, dependencies=[Depends(check_api_key)])
def ask(req: AskRequest) -> AskResponse:
    # A plain "def" (not async): FastAPI runs it in a thread pool,
    # so a slow LLM call doesn't block other requests
    t0 = time.perf_counter()
    try:
        final = graph_rag.app.invoke(start_state(req.question))
    except Exception as e:
        # Log the details for you, return a clean error to the client
        print(f"ERROR in /ask: {type(e).__name__}: {e}")
        raise HTTPException(status_code=502, detail="The AI service failed, please try again")
    return AskResponse(
        answer=final["answer"],
        sources=to_sources(final["relevant"]),
        attempts=final["attempts"],
        trace=final["trace"],
        seconds=round(time.perf_counter() - t0, 2),
    )


@app.post("/ask/stream", dependencies=[Depends(check_api_key)])
def ask_stream(req: AskRequest) -> StreamingResponse:
    """Server-Sent Events: the frontend can show 'Searching... Checking sources...' live."""

    def events():
        relevant, answer = [], ""
        try:
            for update in graph_rag.app.stream(start_state(req.question), stream_mode="updates"):
                for node, changes in update.items():
                    relevant = changes.get("relevant", relevant)
                    answer = changes.get("answer", answer)
                    yield f"data: {json.dumps({'type': 'step', 'node': node, 'message': changes['trace'][-1]})}\n\n"
            done = {"type": "answer", "answer": answer,
                    "sources": [s.model_dump() for s in to_sources(relevant)]}
            yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n"
        except Exception as e:
            print(f"ERROR in /ask/stream: {type(e).__name__}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': 'The AI service failed'})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
