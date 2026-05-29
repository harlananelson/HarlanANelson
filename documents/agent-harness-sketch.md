# Claude API Agent Harness — Design Sketch

## Why

Claude Code's `auto` mode is restricted to Team/Enterprise/API plans. On Pro/Max,
you're stuck with `acceptEdits` + manual allow rules. Building your own harness on
the API gives you:

- Full auto-mode equivalent (your code, your safety rules)
- Model routing (Haiku for reads, Sonnet for work, Opus for reasoning)
- Prompt caching (90% savings on repeated project context)
- No permission system you don't control
- Cost visibility per session

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  User CLI    │────▶│  Agent Loop  │────▶│ Anthropic   │
│  (prompt)    │     │  (Python)    │◀────│ API         │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────┴───────┐
                    │  Tool Router │
                    └──────┬───────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────▼──┐    ┌─────▼────┐   ┌─────▼────┐
     │File I/O │    │  Bash    │   │  Search  │
     │Read/    │    │subprocess│   │glob/grep │
     │Write/   │    │          │   │          │
     │Edit     │    └────┬─────┘   └──────────┘
     └─────────┘         │
                  ┌──────▼──────┐
                  │ Hook Layer  │
                  │(your existing│
                  │ hooks)      │
                  └─────────────┘
```

## Minimal Implementation

### 1. Tool Definitions

```python
TOOLS = [
    {
        "name": "read_file",
        "description": "Read file contents",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "offset": {"type": "integer", "description": "Start line (0-indexed)"},
                "limit": {"type": "integer", "description": "Max lines to read"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "edit_file",
        "description": "Replace old_string with new_string in a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_string": {"type": "string"},
                "new_string": {"type": "string"}
            },
            "required": ["path", "old_string", "new_string"]
        }
    },
    {
        "name": "bash",
        "description": "Execute a bash command",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout": {"type": "integer", "default": 120}
            },
            "required": ["command"]
        }
    },
    {
        "name": "glob",
        "description": "Find files matching a glob pattern",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string"}
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "grep",
        "description": "Search file contents with regex",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string"},
                "glob": {"type": "string"}
            },
            "required": ["pattern"]
        }
    }
]
```

### 2. Tool Execution

```python
import subprocess, pathlib, fnmatch, re

def execute_tool(name: str, inputs: dict) -> str:
    """Execute a tool and return its output as a string."""

    if name == "read_file":
        p = pathlib.Path(inputs["path"])
        lines = p.read_text().splitlines()
        offset = inputs.get("offset", 0)
        limit = inputs.get("limit", len(lines))
        selected = lines[offset:offset + limit]
        return "\n".join(f"{i+offset+1}\t{line}" for i, line in enumerate(selected))

    elif name == "write_file":
        p = pathlib.Path(inputs["path"])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(inputs["content"])
        return f"Wrote {len(inputs['content'])} bytes to {inputs['path']}"

    elif name == "edit_file":
        p = pathlib.Path(inputs["path"])
        text = p.read_text()
        if inputs["old_string"] not in text:
            return f"ERROR: old_string not found in {inputs['path']}"
        count = text.count(inputs["old_string"])
        if count > 1:
            return f"ERROR: old_string found {count} times — must be unique"
        text = text.replace(inputs["old_string"], inputs["new_string"], 1)
        p.write_text(text)
        return f"Edited {inputs['path']}"

    elif name == "bash":
        timeout = inputs.get("timeout", 120)
        result = subprocess.run(
            inputs["command"], shell=True, capture_output=True,
            text=True, timeout=timeout, cwd=WORKING_DIR
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        if result.returncode != 0:
            output += f"\nExit code: {result.returncode}"
        return output[:50000]  # truncate very long output

    elif name == "glob":
        base = pathlib.Path(inputs.get("path", WORKING_DIR))
        matches = sorted(base.glob(inputs["pattern"]))
        return "\n".join(str(m) for m in matches[:200])

    elif name == "grep":
        cmd = ["rg", "--no-heading", inputs["pattern"]]
        if "glob" in inputs:
            cmd.extend(["--glob", inputs["glob"]])
        cmd.append(inputs.get("path", WORKING_DIR))
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout[:50000]

    return f"Unknown tool: {name}"
```

### 3. Agent Loop

```python
import anthropic

client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var

def load_system_prompt():
    """Load CLAUDE.md + project context as cached system prompt."""
    parts = []
    for path in ["~/.claude/CLAUDE.md", "CLAUDE.md"]:
        p = pathlib.Path(path).expanduser()
        if p.exists():
            parts.append(p.read_text())
    return "\n---\n".join(parts)

def run_agent(user_prompt: str, model: str = "claude-sonnet-4-6"):
    system = load_system_prompt()
    messages = [{"role": "user", "content": user_prompt}]
    total_input_tokens = 0
    total_output_tokens = 0

    while True:
        response = client.messages.create(
            model=model,
            max_tokens=8192,
            system=[{
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"}  # 5-min cache
            }],
            tools=TOOLS,
            messages=messages,
        )

        # Track costs
        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens

        # Print any text output
        for block in response.content:
            if hasattr(block, "text"):
                print(block.text)

        # Done?
        if response.stop_reason == "end_turn":
            print(f"\n--- Tokens: {total_input_tokens} in / {total_output_tokens} out ---")
            return

        # Execute tool calls
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  [tool] {block.name}({block.input})")

                # --- Hook layer: run pre-tool-use checks ---
                if not check_hooks(block.name, block.input):
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "DENIED by hook layer",
                        "is_error": True
                    })
                    continue

                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
```

### 4. Hook Layer (reuse your existing hooks)

```python
import json

def check_hooks(tool_name: str, tool_input: dict) -> bool:
    """Run your existing hook scripts as pre-tool-use gates."""

    # Permission gate (your existing hook)
    env = {
        "TOOL_NAME": tool_name,
        "TOOL_INPUT": json.dumps(tool_input),
        **os.environ
    }
    result = subprocess.run(
        ["/home/harlan/projects/asksage/.venv/bin/python",
         "/home/harlan/.claude/hooks/permission-gate.py"],
        env=env, capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        print(f"  [DENIED] {tool_name}: {result.stdout}")
        return False

    # Pre-push gate for git push
    if tool_name == "bash" and tool_input.get("command", "").startswith("git push"):
        result = subprocess.run(
            ["/home/harlan/.claude/hooks/pre-push-gate.sh"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"  [DENIED] git push: {result.stdout}")
            return False

    return True
```

### 5. Model Routing

```python
def choose_model(task_description: str) -> str:
    """Route to the cheapest model that can handle the task."""
    # Simple heuristic — could use a classifier later
    lower = task_description.lower()

    if any(w in lower for w in ["read", "list", "find", "search", "glob", "grep"]):
        return "claude-haiku-4-5-20251001"  # $1/$5 per MTok

    if any(w in lower for w in ["architect", "design", "complex", "refactor", "debug"]):
        return "claude-opus-4-6"  # $5/$25 per MTok

    return "claude-sonnet-4-6"  # $3/$15 per MTok — default
```

### 6. Cost Tracking

```python
import csv, datetime

MODEL_COSTS = {
    "claude-opus-4-6":          (5.00, 25.00),   # per MTok
    "claude-sonnet-4-6":        (3.00, 15.00),
    "claude-haiku-4-5-20251001": (1.00, 5.00),
}

def log_session(model, input_tokens, output_tokens, cached_tokens=0):
    input_cost, output_cost = MODEL_COSTS[model]
    # Cached tokens cost 10% of input
    effective_input = (input_tokens - cached_tokens) + (cached_tokens * 0.1)
    cost = (effective_input * input_cost + output_tokens * output_cost) / 1_000_000

    with open("~/.claude/session-costs.csv", "a") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.datetime.now().isoformat(),
            model, input_tokens, output_tokens, cached_tokens,
            f"${cost:.4f}"
        ])
    return cost
```

## Cost Comparison

Assuming daily usage pattern similar to current Max 5x (~50% weekly budget):

| Scenario | Monthly Cost | Auto Mode |
|----------|-------------|-----------|
| Max 5x (current) | $100 | No |
| API Sonnet-heavy | ~$100-200 | Yes |
| API Sonnet + caching | ~$60-120 | Yes |
| API Sonnet + Haiku routing | ~$40-80 | Yes |
| API with batch (non-interactive) | ~$30-60 | N/A |

With aggressive caching + model routing, you could match or beat your Max 5x cost
while getting full autonomy.

## What's Missing vs Claude Code

- **Streaming** — add `stream=True` for real-time output
- **Subagents** — spawn parallel agent loops for independent tasks
- **MCP integration** — connect your ontograph, pico-dag servers
- **Context compression** — summarize old messages when approaching 200K tokens
- **IDE integration** — VS Code extension or Positron panel

These are all addable incrementally. Start with the core loop, use it for a week,
then decide what's worth building next.

## Getting Started

```bash
# 1. Get an API key from console.anthropic.com
export ANTHROPIC_API_KEY="sk-ant-..."

# 2. Install the SDK
pip install anthropic

# 3. Run the harness
python agent.py "Read the _quarto.yml and add a new page to the navbar"
```
