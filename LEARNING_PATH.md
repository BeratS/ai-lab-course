# AI Lab — Learning Path to AI Engineer

A hands-on lab for learning Python AI engineering step by step: LLM calls, structured output, agents and tool use, RAG, LangGraph, evals, observability and deployment. Everything runs in Docker.

---

## 1. Setup (once)

**Requirements:** Docker Desktop (Windows/macOS) or Docker Engine (Linux), plus VS Code.

```bash
# In the ai-lab folder, on your machine
cp .env.example .env              # then put your real ANTHROPIC_API_KEY in .env
docker compose up -d --build      # build and start the container
```

Get an API key at https://console.anthropic.com. Never commit `.env`.

---

## 2. Everyday commands

> **Rule:** `docker ...` commands run on **your machine**.
> `python ...` and `uv ...` commands run **inside the container**.

### On your machine

| What | Command |
|---|---|
| Start the lab | `docker compose up -d` |
| Rebuild after adding packages | `docker compose up -d --build` |
| Run a script | `docker compose exec app python main.py` |
| Open a shell inside the container | `docker compose exec app bash` |
| Add a package | `docker compose exec app uv add <package>` |
| Start the vector DB (Step 4+) | `docker compose --profile rag up -d` |
| See running containers | `docker compose ps` |
| See logs | `docker compose logs -f` |
| Stop everything | `docker compose down` |
| Stop and delete DB data | `docker compose down -v` |

### Inside the container (prompt looks like `root@...:/app#`)

| What | Command |
|---|---|
| Run a script | `python main.py` |
| Add a package | `uv add <package>` |
| Run tests | `uv run pytest` |
| Leave the container | `exit` |

---

## 3. VS Code setup

**Simple:** open the `ai-lab` folder in VS Code, edit files, and run scripts in the terminal with `docker compose exec app python <file>.py`.

**Recommended (autocomplete inside the container):**
1. Install the **Dev Containers** extension (Microsoft).
2. Make sure the lab is running: `docker compose up -d`.
3. `Ctrl+Shift+P` → **Dev Containers: Attach to Running Container…** → `ai-lab`.
4. In the new window: **File → Open Folder** → `/app`.
5. Install the **Python** extension in that window.
6. `Ctrl+Shift+P` → **Python: Select Interpreter** → `/opt/venv/bin/python`.

The terminal in that window is already inside the container: just run `python main.py`.

---

## 4. The learning path

Each step is small and runnable. Keep each step in its own folder (`step1/`, `step2/`, …) so you can look back at what you built.

### Step 1 — First LLM call and chat loop ✅ *code ready in `main.py`*
- **Goal:** call the model, build a chat loop, understand that the model has no memory.
- **Key idea:** every call resends the whole `messages` list. That list *is* the context.
- **Exercises:**
  1. Chat 5–6 turns and watch `tokens in` grow.
  2. Change the `system` prompt (e.g. "Answer only in Albanian, max 2 sentences").
  3. Keep only the last 6 messages (`messages = messages[-6:]`) and see what the model forgets.

### Step 2 — Structured output with Pydantic
- **Goal:** get typed Python objects back instead of free text.
- **Learn:** Pydantic models, JSON schemas, validation, retry on bad output.
- **Packages:** `uv add pydantic`
- **Mini project:** extract structured data (name, date, amount) from messy text such as an invoice or email.

### Step 3 — Tool calling: the agent loop by hand
- **Goal:** build your own agent loop without frameworks.
- **Learn:** tool definitions, the loop (model → tool call → run tool → result back → repeat), stop conditions, step limits, error handling.
- **Mini project:** an agent with `read_file`, `write_file` and `run_python` tools.
- **Reference:** read the source of a small open-source agent like mini-swe-agent.

### Step 4 — RAG basics
- **Goal:** answer questions over your own documents.
- **Learn:** loading documents, chunking strategies, embeddings, vector search with pgvector, putting retrieved chunks into the prompt.
- **Start the DB:** `docker compose --profile rag up -d`
  (from inside the container: host `db`, user `ai`, password `ai`, database `ailab`)
- **Packages:** `uv add psycopg[binary] pgvector` plus an embeddings provider
- **Mini project:** Q&A over a folder of PDFs or Markdown files (curriculum documents in Albanian/Macedonian are a great fit).

### Step 5 — RAG as a LangGraph workflow
- **Goal:** turn the RAG pipeline into a graph with clear steps and state.
- **Learn:** LangGraph nodes, edges, state, conditional routing (e.g. rewrite query → retrieve → grade → answer).
- **Packages:** `uv add langgraph langchain-anthropic`

### Step 6 — Evals
- **Goal:** measure whether your system actually works, instead of guessing.
- **Learn:** test datasets, pass/fail checks, LLM-as-judge, RAG metrics (retrieval accuracy, faithfulness), comparing models and prompts.
- **Bonus:** run your Step 3 agent on a subset of the Aider *polyglot* benchmark (Exercism exercises in several languages). Track pass rate, cost and tokens.
- **Tools to look at:** pytest, Inspect, promptfoo.

### Step 7 — Observability
- **Goal:** see every LLM call, tool call, token count and latency.
- **Learn:** tracing, debugging bad answers, cost monitoring.
- **Tools:** Langfuse or OpenTelemetry.

### Step 8 — Deploy
- **Goal:** ship it like a production service.
- **Learn:** FastAPI endpoint, streaming responses, Dockerfile for production, deploy to a cloud (Azure or AWS), basic monitoring.
- **Packages:** `uv add fastapi uvicorn`

### Extra topics (alongside the steps)
- **Context engineering:** system prompts, tool descriptions, trimming tool output, compacting long history, memory.
- **Agent skills:** a `skills/` folder where each skill has a `SKILL.md`; the agent sees short descriptions and loads full instructions only when needed.
- **MCP:** build a small MCP server (e.g. exposing a database) and connect your agent to it.
- **Classical ML basics:** a simple Scikit-learn model, enough to discuss in interviews.

---

## 5. Progress checklist

- [ ] Step 1 — First LLM call and chat loop
- [ ] Step 2 — Structured output with Pydantic
- [ ] Step 3 — Tool calling and the agent loop
- [ ] Step 4 — RAG basics with pgvector
- [ ] Step 5 — RAG with LangGraph
- [ ] Step 6 — Evals (+ polyglot benchmark subset)
- [ ] Step 7 — Observability with Langfuse
- [ ] Step 8 — Deploy with FastAPI + Docker + cloud
- [ ] Extra — Context engineering experiments
- [ ] Extra — Skills folder + MCP server
- [ ] Publish on GitHub with results and a short write-up

---

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| `docker: command not found` inside the container | Normal — exit the container first (`exit`), then run `docker` commands on your machine |
| `docker: command not found` on your machine | Install Docker Desktop and make sure it is running |
| `anthropic` underlined red in VS Code | Attach VS Code to the container (Section 3) and select `/opt/venv/bin/python` |
| A newly added package is missing after restart | Run `docker compose up -d --build` |
| Authentication error from the API | Check `ANTHROPIC_API_KEY` in `.env`, then `docker compose up -d` again |
| Port 5432 already in use | Another Postgres is running; stop it or change the port in `docker-compose.yml` |

## Trace Tool: https://agentgateway.dev/