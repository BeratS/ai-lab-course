"""
Step 3 — The agent loop, written by hand (no frameworks)

The model asks for tools, your code runs them, sends back the results,
and repeats until the model says it's done.

Run:  docker compose exec app python step3/agent.py
  or: docker compose exec app python step3/agent.py "your task here"
"""
import os
import json
import subprocess
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
MAX_STEPS = 15                 # safety: never loop forever
MAX_TOOL_OUTPUT = 4000      # context engineering: trim long outputs

# The agent can only touch files inside this folder
WORKSPACE = (Path(__file__).parent / "workspace").resolve()
WORKSPACE.mkdir(exist_ok=True)

SYSTEM = """You are a careful Python coding agent.
You work only inside the workspace folder, using the tools you are given.
Work in small steps: write code, run it, read the output, fix errors.
When the task is finished and tested, reply with a short summary and stop calling tools."""


# ---------- 1. The tools: plain Python functions ----------

def safe_path(path: str) -> Path:
    """Block paths like ../../etc/passwd from escaping the workspace."""
    p = (WORKSPACE / path).resolve()
    if not p.is_relative_to(WORKSPACE):
        raise ValueError(f"Path {path!r} is outside the workspace")
    return p


def list_files() -> str:
    files = [str(p.relative_to(WORKSPACE)) for p in WORKSPACE.rglob("*") if p.is_file()]
    return "\n".join(sorted(files)) or "(workspace is empty)"


def read_file(path: str) -> str:
    return safe_path(path).read_text()


def write_file(path: str, content: str) -> str:
    p = safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Wrote {len(content)} characters to {path}"


def run_python(path: str) -> str:
    result = subprocess.run(
        [sys.executable, str(safe_path(path))],
        cwd=WORKSPACE, capture_output=True, text=True, timeout=30,
    )
    output = (result.stdout + result.stderr).strip() or "(no output)"
    if len(output) > MAX_TOOL_OUTPUT:
        half = MAX_TOOL_OUTPUT // 2
        output = output[:half] + "\n... (middle trimmed) ...\n" + output[-half:]
    return f"Exit code: {result.returncode}\n{output}"

def search_in_files(text: str) -> str:
    matches = []
    for p in sorted(WORKSPACE.rglob("*")):
        if not p.is_file():
            continue
        try:
            lines = p.read_text().splitlines()
        except UnicodeDecodeError:      # skip binary files like .pyc
            continue
        for n, line in enumerate(lines, start=1):
            if text.lower() in line.lower():
                matches.append(f"{p.relative_to(WORKSPACE)}:{n}: {line.strip()}")

    if not matches:
        return f"No matches for {text!r}"
    if len(matches) > 50:                # context engineering: don't flood the model
        return "\n".join(matches[:50]) + f"\n... ({len(matches) - 50} more matches trimmed)"
    return "\n".join(matches)

TOOL_FUNCTIONS = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "run_python": run_python,
    "search_in_files": search_in_files,   # ← new
}


# ---------- 2. Tool descriptions: what the model sees ----------

TOOLS = [
    {
        "name": "list_files",
        "description": "List all files in the workspace.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_file",
        "description": "Read a text file from the workspace.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path relative to the workspace"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Create or overwrite a file in the workspace with the full content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path relative to the workspace"},
                "content": {"type": "string", "description": "The complete file content"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "run_python",
        "description": "Run a Python file from the workspace. Returns exit code, stdout and stderr.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path relative to the workspace"}},
            "required": ["path"],
        },
    },
    {
        "name": "search_in_files",
        "description": "Search all workspace files for a piece of text (case-insensitive). "
                       "Returns matching lines as file:line: content. "
                       "Use this to find where something is defined or used, "
                       "instead of reading every file.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "The text to search for"}},
            "required": ["text"],
        },
    },
]


# ---------- 3. The agent loop ----------

def run_agent(task: str) -> None:
    messages = [{"role": "user", "content": task}]
    tokens_in = tokens_out = 0

    for step in range(1, MAX_STEPS + 1):
        print(f"\n--- step {step} ---")
        response = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )
        tokens_in += response.usage.input_tokens
        tokens_out += response.usage.output_tokens

        # Always keep the model's full answer in the history
        messages.append({"role": "assistant", "content": response.content})

        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"[model] {block.text}")

        # No tool requested -> the model is done
        if response.stop_reason != "tool_use":
            print(f"\nDone in {step} steps. Tokens in: {tokens_in}, out: {tokens_out}")
            return

        # Run every tool the model asked for, collect the results
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"[tool]  {block.name}({json.dumps(block.input)[:150]})")
            try:
                result = TOOL_FUNCTIONS[block.name](**block.input)
                is_error = False
            except Exception as e:
                result = f"Error: {type(e).__name__}: {e}"
                is_error = True
            print(f"[result] {result[:200]}")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
                "is_error": is_error,
            })

        # Tool results go back as a "user" message, then we loop
        messages.append({"role": "user", "content": tool_results})

    print(f"\nStopped: reached the {MAX_STEPS}-step limit. Tokens in: {tokens_in}, out: {tokens_out}")


if __name__ == "__main__":
    default_task = (
        "Create calculator.py with functions add, subtract, multiply and divide "
        "(divide must raise ValueError on division by zero). "
        "Then create test_calculator.py that tests them with plain assert statements "
        "and prints 'ALL TESTS PASSED'. Run the tests and fix any failures."
    )
    task = " ".join(sys.argv[1:]) or default_task
    print(f"Task: {task}")
    run_agent(task)