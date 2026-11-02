# PromptForge

System prompt generator for LLM agents with JSON export for APIs (OpenAI, Anthropic, universal format).

Read this in [Russian](README.md)

## Features

- **Interactive wizard** for creating agent configuration with step-by-step prompts
- **Deterministic rendering** — same config → same `sha256` and prompt version
- **Validation** of configuration before generation (tool names, parameter ranges, required fields)
- **Variable substitution** `{{key}}` in prompt text
- **Three export formats**: OpenAI, Anthropic, universal raw
- **Few-shot examples** — inline in system prompt or as separate messages
- **Atomic file writing** via `tempfile` + `os.replace`
- **Django integration** via management command

## Requirements

- Python ≥ 3.10
- Optional:
  - `PyYAML` — for loading YAML configs
  - `tiktoken` — for accurate token estimation (otherwise heuristic)

```bash
pip install pyyaml tiktoken
```

## Project Structure

```
promptforge/
├── __init__.py          # public API
├── __main__.py          # CLI entry point
├── models.py            # configuration models (dataclasses)
├── builder.py           # system prompt assembly
├── exporters.py         # JSON export for APIs
├── interactive.py       # interactive wizard
├── sample.py            # reference configuration
└── cli.py               # CLI commands
```

## Quick Start

### 1. Create Agent Configuration

```bash
# Interactive wizard (default)
python -m promptforge init -o agent.config.json

# From ready template (no prompts)
python -m promptforge init -o agent.config.json --template

# Force non-interactive (for CI/CD)
python -m promptforge init -o agent.config.json --non-interactive

# Overwrite existing file
python -m promptforge init -o agent.config.json --force

# Without preview before saving
python -m promptforge init -o agent.config.json --no-preview
```

### 2. Validate Configuration

```bash
python -m promptforge validate -c agent.config.json
# OK: django-code-reviewer v1.0.0+a1b2c3d4, ~1234 tokens, 9 sections.
```

### 3. Preview Prompt Text

```bash
python -m promptforge preview -c agent.config.json --var django_version=5.1
```

### 4. Build JSON Payload for API

```bash
# For OpenAI
python -m promptforge build -c agent.config.json -f openai -o build/agent.json

# For Anthropic
python -m promptforge build -c agent.config.json -f anthropic -o build/agent.claude.json

# Universal format
python -m promptforge build -c agent.config.json -f raw -o build/agent.raw.json

# With prompt metadata
python -m promptforge build -c agent.config.json -f openai -o build/agent.json --meta build/agent.meta.json

# Without few-shot examples
python -m promptforge build -c agent.config.json -f openai -o build/agent.json --no-examples
```

## Interactive Wizard

The `init` command launches a step-by-step wizard by default. `Ctrl+C` at any step aborts the process without saving the file.

### Example Dialog

```
$ python -m promptforge init -o my_agent.json

=== PromptForge: Agent Creation Wizard ===
Press Ctrl+C at any step to abort without saving.

=== Basic Information ===
? Agent name (latin/digits/_/-) [a-zA-Z0-9_-]: django-reviewer
? Version  (default: '1.0.0'): 
? Agent role e.g. 'Senior Django Developer': Senior Python/Django Engineer
? Agent goal 1–3 sentences
  Multi-line input. Empty line to finish.
  │ Find defects and vulnerabilities in code
  │ and suggest fixes.
  │ 
? Target audience (optional): backend middle+ developers
? Communication tone (optional)
  Enter one item per line. Empty line to finish.
  #1 professional
  #2 concise
  #3 

=== Context and Tasks ===
? Project context (optional)
  #1 Stack: Python {{python_version}}, Django {{django_version}}
  #2 
? Agent tasks
  #1 Check ORM queries for N+1
  #2 Find security issues
  #3 
? Workflow (optional)
  #1 Determine code purpose
  #2 Compile list of findings
  #3 
? Rules (optional)
  #1 Each finding includes file path
  #2 
? Prohibitions (optional)
  #1 invent file contents you haven't seen
  #2 
? Behavior on uncertainty (optional)
  │ If data is insufficient, ask a clarifying question.
  │ 

=== Language and Style ===
? Response language [ru, en, de, fr, es, kk] (default: 'ru'): en

=== Tools (function calling) ===
? Add tools? [Y/n]: y
? Tool name [a-zA-Z0-9_-]: get_file
? Tool description: Read file from repository
? Parameters JSON Schema {"type":"object","properties":{...},"required":[...]}
  │ {"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}
  │ 
? Enable strict mode? [y/N]: y
? Add another tool? [y/N]: n

=== Few-shot Examples ===
? Add dialog examples? [Y/n]: y
--- Example #1 ---
? User message
  │ Check this code: for order in Order.objects.all(): print(order.user.email)
  │ 
? Assistant response
  │ **major — N+1 query.** Use select_related('user').
  │ 
? Add another example? [y/N]: n
? Embed examples in system prompt (inline)? [y/N]: n

=== Response Format ===
? Response format [markdown, json, text] (default: 'markdown'): markdown
? Additional format instructions (optional)
  #1 Structure: Findings → Fixes → Summary
  #2 

=== Template Variables ===
? Set variables? [y/N]: y
? Variable name (empty to finish): django_version
? Value for variable {{django_version}}: 5.1
? Another variable? [y/N]: y
? Variable name (empty to finish): python_version
? Value for variable {{python_version}}: 3.12
? Another variable? [y/N]: n

=== Model Parameters ===
? Model name  (default: 'gpt-4.1-mini'): 
? Temperature [0.0..2.0] (default: '0.2'): 
? Top-p (empty to skip): 
? Max tokens  (default: '2048'): 
? Token limit parameter [max_tokens, max_completion_tokens] (default: 'max_tokens'): 
? Cache system prompt (Anthropic cache_control)? [y/N]: n

=== Configuration Preview ===
{
  "name": "django-reviewer",
  "version": "1.0.0",
  "role": "Senior Python/Django Engineer",
  "goal": "Find defects and vulnerabilities in code\nand suggest fixes.",
  ...
}
? Save this config? [Y/n/edit]: y
Configuration created: my_agent.json
```

### Wizard Features

- **Auto-detection**: if `stdin` is not a TTY (pipe, CI), template is used automatically
- **Real-time validation**: each field is validated immediately — errors trigger re-prompt, not crash
- **Multi-line input**: for `goal`, `fallback`, examples — empty line finishes block
- **Pre-save editing**: `edit` response opens JSON in `$EDITOR`
- **Localized responses**: accepts `y/n/yes/no`

## Configuration Format

Configuration is JSON (or YAML with PyYAML) with the following structure:

```json
{
  "name": "django-code-reviewer",
  "version": "1.0.0",
  "role": "Senior Python/Django engineer performing code review",
  "goal": "Find defects and suggest fixes.",
  
  "language": "en",
  "audience": "backend developers middle+ level",
  "tone": ["professional", "concise"],
  
  "context": [
    "Project stack: Python {{python_version}}, Django {{django_version}}."
  ],
  "tasks": [
    "Check ORM query correctness.",
    "Find security issues."
  ],
  "workflow": [
    "Determine code purpose.",
    "Compile list of findings.",
    "Suggest fixes."
  ],
  "rules": [
    "Each finding includes file path."
  ],
  "prohibitions": [
    "invent file contents you haven't seen"
  ],
  "fallback": "If data is insufficient, ask a clarifying question.",
  
  "tools": [
    {
      "name": "get_file",
      "description": "Read file contents from repository.",
      "parameters": {
        "type": "object",
        "properties": {
          "path": {"type": "string", "description": "File path"}
        },
        "required": ["path"],
        "additionalProperties": false
      },
      "strict": true
    }
  ],
  "tools_policy": "Read file with get_file tool before making conclusions.",
  
  "examples": [
    {
      "user": "Check: for order in Order.objects.all(): print(order.user.email)",
      "assistant": "**major — N+1 query.** Use select_related('user')."
    }
  ],
  "inline_examples": false,
  
  "output": {
    "format": "markdown",
    "instructions": [
      "Structure: Findings → Fixes → Summary."
    ],
    "schema": null,
    "schema_name": "code_review"
  },
  
  "variables": {"python_version": "3.12", "django_version": "5.0"},
  
  "model": "gpt-4.1-mini",
  "temperature": 0.2,
  "top_p": null,
  "max_tokens": 2048,
  "token_param": "max_tokens",
  "cache_system_prompt": false,
  "metadata": {"owner": "backend-team"}
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Agent name: latin, digits, `_`, `-` (1–64 chars) |
| `role` | string | Agent role |
| `goal` | string | Agent goal |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `version` | string | `"1.0.0"` | Configuration version |
| `language` | string | `"ru"` | Response language (`ru`, `en`, `de`, `fr`, `es`, `kk`) |
| `audience` | string | `""` | Target audience |
| `tone` | list[string] | `[]` | Communication tone |
| `context` | list[string] | `[]` | Project context |
| `tasks` | list[string] | `[]` | Agent tasks |
| `workflow` | list[string] | `[]` | Workflow steps |
| `rules` | list[string] | `[]` | Rules |
| `prohibitions` | list[string] | `[]` | Prohibitions |
| `fallback` | string | `""` | Behavior on uncertainty |
| `tools` | list[Tool] | `[]` | Tools (function calling) |
| `tools_policy` | string | see code | Tool usage policy |
| `examples` | list[Example] | `[]` | Few-shot examples |
| `inline_examples` | bool | `false` | Embed examples in system prompt |
| `output.format` | string | `"markdown"` | Response format: `text`, `markdown`, `json` |
| `output.instructions` | list[string] | `[]` | Format instructions |
| `output.schema` | object | `null` | Response JSON Schema (for `format: json`) |
| `output.schema_name` | string | `"agent_response"` | Schema name |
| `variables` | object | `{}` | Variables for `{{key}}` substitution |
| `model` | string | `"gpt-4.1-mini"` | Model name |
| `temperature` | float | `0.2` | Temperature (0.0–2.0) |
| `top_p` | float | `null` | Top-p (0.0–1.0) |
| `max_tokens` | int | `2048` | Token limit |
| `token_param` | string | `"max_tokens"` | Token limit parameter name |
| `cache_system_prompt` | bool | `false` | Cache system prompt (Anthropic) |
| `metadata` | object | `{}` | Arbitrary metadata |

### Tool Structure

```json
{
  "name": "get_file",
  "description": "Read file contents.",
  "parameters": {
    "type": "object",
    "properties": {
      "path": {"type": "string", "description": "File path"}
    },
    "required": ["path"],
    "additionalProperties": false
  },
  "strict": true
}
```

### Example Structure

```json
{
  "user": "User message",
  "assistant": "Assistant response"
}
```

## Programmatic Usage

### Basic Example

```python
from promptforge import AgentConfig, PromptBuilder, export

# Load configuration
config = AgentConfig.from_file("agent.config.json")

# Build prompt with variable substitution
built = PromptBuilder(config, variables={"django_version": "5.1"}).build()

# Export to OpenAI format
payload = export(built, "openai")

# Use with OpenAI API
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(**payload)
print(response.choices[0].message.content)
```

### Prompt Metadata

```python
from promptforge import AgentConfig, PromptBuilder

config = AgentConfig.from_file("agent.config.json")
built = PromptBuilder(config).build()

print(f"Prompt version: {built.prompt_version}")
print(f"SHA256: {built.sha256}")
print(f"Token estimate: {built.tokens_estimate}")
print(f"Sections: {list(built.sections.keys())}")

# Metadata for logging
meta = built.meta()
print(meta)
# {
#   "agent": "django-code-reviewer",
#   "config_version": "1.0.0",
#   "prompt_version": "1.0.0+a1b2c3d4",
#   "sha256": "...",
#   "tokens_estimate": 1234,
#   "language": "en",
#   "tools": ["get_file", "run_tests"]
# }
```

### Create Configuration from Code

```python
from promptforge import AgentConfig, Tool, Example, OutputSpec

config = AgentConfig(
    name="my-agent",
    role="Assistant",
    goal="Answer questions",
    language="en",
    tools=[
        Tool(
            name="search",
            description="Search knowledge base",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        )
    ],
    examples=[
        Example(user="What is Django?", assistant="Django is a web framework.")
    ],
    output=OutputSpec(format="markdown"),
)

# Validation
errors = config.validate()
if errors:
    print("Errors:", errors)
else:
    config.ensure_valid()  # raises exception on errors
```

### Create Configuration from Dictionary

```python
from promptforge import AgentConfig

config_dict = {
    "name": "my-agent",
    "role": "Assistant",
    "goal": "Answer questions",
}

config = AgentConfig.from_dict(config_dict)
```

## Django Integration

### Management Command

Create file `apps/agents/management/commands/build_agent_prompt.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from promptforge import AgentConfig, ConfigError, PromptBuilder, export
from promptforge.exporters import FORMATS


class Command(BaseCommand):
    help = "Build agent system prompt into JSON payload for LLM API."

    def add_arguments(self, parser):
        parser.add_argument("-c", "--config", required=True, type=Path)
        parser.add_argument("-f", "--format", default="openai", choices=sorted(FORMATS))
        parser.add_argument("-o", "--out", type=Path, required=True)
        parser.add_argument("--var", action="append", default=[], metavar="KEY=VALUE")
        parser.add_argument("--no-examples", action="store_true")

    def handle(self, *args, **options):
        variables = dict(
            item.split("=", 1) for item in options["var"] if "=" in item
        )
        try:
            config = AgentConfig.from_file(options["config"])
            built = PromptBuilder(config, variables=variables).build()
            payload = export(
                built, options["format"], include_examples=not options["no_examples"]
            )
        except ConfigError as exc:
            raise CommandError(str(exc)) from exc

        out: Path = options["out"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"{out} [{options['format']}] prompt v{built.prompt_version}, "
                f"~{built.tokens_estimate} tokens, sha256={built.sha256[:12]}"
            )
        )
```

Usage:

```bash
python manage.py build_agent_prompt -c configs/django_reviewer.json -o build/agent.json
```

## Export Formats

### OpenAI

```bash
python -m promptforge build -c agent.config.json -f openai -o agent.json
```

Result:

```json
{
  "model": "gpt-4.1-mini",
  "messages": [
    {"role": "system", "content": "# Agent system instruction ..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "temperature": 0.2,
  "max_tokens": 2048,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_file",
        "description": "...",
        "parameters": {...},
        "strict": true
      }
    }
  ],
  "tool_choice": "auto",
  "parallel_tool_calls": true
}
```

Usage:

```python
import json
from openai import OpenAI

payload = json.load(open("agent.json", encoding="utf-8"))
payload["messages"].append({"role": "user", "content": "Check apps/orders/views.py"})

resp = OpenAI().chat.completions.create(**payload)
print(resp.choices[0].message.content)
```

### Anthropic

```bash
python -m promptforge build -c agent.config.json -f anthropic -o agent.claude.json
```

Result:

```json
{
  "model": "claude-3-5-sonnet-20241022",
  "system": "# Agent system instruction ...",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "max_tokens": 2048,
  "temperature": 0.2,
  "tools": [
    {
      "name": "get_file",
      "description": "...",
      "input_schema": {...}
    }
  ]
}
```

With system prompt caching (if `cache_system_prompt: true` in config):

```json
{
  "system": [
    {
      "type": "text",
      "text": "# Agent system instruction ...",
      "cache_control": {"type": "ephemeral"}
    }
  ]
}
```

Usage:

```python
import json
from anthropic import Anthropic

payload = json.load(open("agent.claude.json", encoding="utf-8"))
payload["messages"].append({"role": "user", "content": "Check code"})

resp = Anthropic().messages.create(**payload)
print(resp.content[0].text)
```

### Raw (Universal)

```bash
python -m promptforge build -c agent.config.json -f raw -o agent.raw.json
```

Result:

```json
{
  "name": "django-code-reviewer",
  "version": "1.0.0+a1b2c3d4",
  "system_prompt": "# Agent system instruction ...",
  "messages": [...],
  "tools": [...],
  "output": {
    "format": "markdown",
    "schema": null
  },
  "model_params": {
    "model": "gpt-4.1-mini",
    "temperature": 0.2,
    "top_p": null,
    "max_tokens": 2048
  },
  "metadata": {...}
}
```

## Variables and Templates

You can use variables `{{key}}` in configuration text, which will be substituted during prompt assembly.

### Set Variables in Config

```json
{
  "context": [
    "Project stack: Python {{python_version}}, Django {{django_version}}."
  ],
  "variables": {
    "python_version": "3.12",
    "django_version": "5.0"
  }
}
```

### Override via CLI

```bash
python -m promptforge build -c agent.config.json --var django_version=5.1 --var python_version=3.13
```

### Override in Code

```python
built = PromptBuilder(config, variables={"django_version": "5.1"}).build()
```

### Error on Missing Variables

If text contains `{{key}}` but value is not set, error occurs:

```
Error: Variable values not set: django_version. Pass them via variables or --var key=value.
```

## Few-shot Examples

Examples can be embedded in system prompt or added as separate messages.

### Inline in System Prompt

```json
{
  "examples": [
    {
      "user": "Question",
      "assistant": "Answer"
    }
  ],
  "inline_examples": true
}
```

Result: "Examples" section in system prompt.

### Separate Messages (default)

```json
{
  "examples": [
    {
      "user": "Question",
      "assistant": "Answer"
    }
  ],
  "inline_examples": false
}
```

Result: examples added to `messages` after system prompt.

### Without Examples

```bash
python -m promptforge build -c agent.config.json --no-examples
```

## Validation

The `validate` command checks configuration:

```bash
python -m promptforge validate -c agent.config.json
```

Checks:

- Required fields (`name`, `role`, `goal`)
- Agent name format (regex `^[a-zA-Z0-9_-]{1,64}$`)
- `temperature` range (0.0–2.0) and `top_p` range (0.0–1.0)
- `max_tokens` positivity
- `output.format` correctness
- `output.schema` presence for `format: json`
- Tool name uniqueness
- Tool name correctness
- Non-empty tool descriptions
- `parameters.type == "object"` for tools
- Non-empty `user` and `assistant` fields in examples

Error example:

```
Error: Invalid agent configuration:
- Field 'name' is required and cannot be empty.
- Field 'temperature' must be in range 0.0–2.0.
- Tool 'get_file': duplicate name.
```

## Prompt Metadata

The `build` command with `--meta` flag saves prompt metadata:

```bash
python -m promptforge build -c agent.config.json -f openai -o agent.json --meta agent.meta.json
```

Contents of `agent.meta.json`:

```json
{
  "agent": "django-code-reviewer",
  "config_version": "1.0.0",
  "prompt_version": "1.0.0+a1b2c3d4",
  "sha256": "a1b2c3d4e5f6...",
  "tokens_estimate": 1234,
  "language": "en",
  "tools": ["get_file", "run_tests"]
}
```

Use for:

- Logging prompt versions
- Tracking changes
- A/B testing
- Cost monitoring (via `tokens_estimate`)

## Token Estimation

By default, heuristic is used: `tokens ≈ len(text) / 3`.

For accurate estimation, install `tiktoken`:

```bash
pip install tiktoken
```

After installation, `o200k_base` encoding is used automatically.

## License

MIT
