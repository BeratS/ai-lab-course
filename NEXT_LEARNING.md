# Learning Phases

You’ve covered the core. What’s left is depth: what separates “built a RAG demo” from “can run AI systems in production.” Here’s what I’d learn next, in rough order of value for the roles you’re targeting.

## 1. Finish your original goal: the coding agent (about 2 weeks)

This is what you first asked about, and it’s the most distinctive portfolio piece.

Grow your Step 3 agent: add context compaction (summarize old history when it gets long), a skills/ folder with SKILL.md files, and a sandbox per task.
Run it on 20–30 exercises from the Aider polyglot benchmark and report the pass rate, cost, and tokens per language.
Build a small MCP server and connect your agent to it. MCP is quickly becoming standard, and few candidates have built one.

## 2. Cost and performance (about 1 week, high interview value)

Every company running LLMs worries about the bill.

Model routing: use a small, cheap model (Haiku) for grading and query rewriting, and the bigger model only for the final answer. Measure the result with your evals.
Prompt caching: cache long, repeated prompts for big cost and latency savings.
Async and batching: use AsyncAnthropic to run the grader’s calls in parallel, and the Batch API for offline work like evals.

## 3. Production RAG depth (about 2 weeks)

Hybrid search: combine keyword search (BM25) with vector search. It fixes cases where exact terms matter, like product codes and names.
Reranking: retrieve 30 chunks, then rerank down to the best 5.
Real documents: PDFs, tables, and scanned files. Parsing is where real projects struggle.
Metadata filtering (by language, date, or customer) and incremental ingestion instead of rebuilding everything.

## 4. Agents in production

LangGraph persistence and checkpointing: conversations that survive restarts.
Human-in-the-loop: the agent pauses and asks for approval before risky actions.
Security: prompt injection (a document that says “ignore your instructions”), guardrails, and tool permissions. This is a fast-growing concern, and good material to talk about in interviews.

## 5. Cloud and MLOps

Azure: Container Apps, Azure OpenAI, and Azure AI Search. It’s the cloud named in the posting, and the one you know from Endava.
CI/CD with evals: a GitHub Action that runs your eval suite on every pull request and fails if the score drops. Very few candidates show this, and it’s exactly what “evaluation in production” means.
Basic infrastructure-as-code (Bicep or Terraform).

## 6. Fundamentals to talk about confidently

Classical ML: a weekend with scikit-learn (train a classifier, understand train/test splits and precision/recall). It’s enough for the “Scikit-learn, PyTorch” line in postings.
How embeddings and transformers work, at a conceptual level.
Fine-tuning (LoRA): what it is, and especially when not to use it, because RAG or better prompts usually win.

My suggestion for the next month, alongside the accelerator:

Week 1: model routing plus the async grader (quick wins, measurable with your existing evals).
Weeks 2–3: the coding agent on the polyglot benchmark, plus a small MCP server.
Week 4: a GitHub Action running your evals, then the Azure deployment.

After that, your GitHub shows an agent, RAG, evals in CI, tracing, and a cloud deployment, which covers the whole AI engineering stack.

Want to start with model routing? It’s a small change to your Step 5 graph, and your eval suite will show right away whether the cheaper model hurts quality.
