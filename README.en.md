<p align="center">
  <h1 align="center">PromptForge</h1>
  <p align="center">
    <em>CLI System prompt generator for LLM agents with JSON export for APIs</em>
  </p>
</p>

<p align="center">
  <a href="https://pypi.org/project/promptforge-llm/">
    <img src="https://img.shields.io/pypi/v/promptforge-llm?label=PyPI&color=blue" alt="PyPI version">
  </a>
  <a href="https://pypi.org/project/promptforge-llm/">
    <img src="https://img.shields.io/pypi/pyversions/promptforge-llm?label=Python&color=3776AB" alt="Python versions">
  </a>
  <a href="https://github.com/mandalay-rp/prompt-forge/actions/workflows/test.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/mandalay-rp/prompt-forge/test.yml?label=Tests" alt="Tests">
  </a>
  <a href="https://github.com/mandalay-rp/prompt-forge/blob/main/LICENSE">
    <img src="https://img.shields.io/pypi/l/promptforge-llm?label=License&color=green" alt="License">
  </a>
  <a href="https://pypi.org/project/promptforge-llm/">
    <img src="https://img.shields.io/pypi/dm/promptforge-llm?label=Downloads" alt="Downloads">
  </a>
</p>

<p align="center">
  <strong>English</strong> | <a href="README.md">Русский</a>
</p>

---

**PromptForge** is a CLI tool for creating, validating, and exporting system prompts for LLM agents into ready-to-use JSON payloads for APIs (OpenAI, Anthropic, universal format).

### Key Features

- 🎯 **Interactive wizard** — step-by-step agent configuration creation
- 🔒 **Deterministic rendering** — same config → same `sha256` and prompt version
- ✅ **Validation** of configuration before generation
- 🔧 **Variable substitution** `{{key}}` in prompt text
- 📦 **Three export formats**: OpenAI, Anthropic, universal raw
- 💬 **Few-shot examples** — inline in system prompt or as separate messages
- 🛡️ **Atomic file writing**
- 🎓 **Django integration** via management command

## Installation

```bash
pip install promptforge-llm

# With optional dependencies
pip install promptforge-llm[yaml]       # YAML config support
pip install promptforge-llm[tokens]     # accurate token estimation via tiktoken
pip install promptforge-llm[all]        # all optional dependencies
```

## Quick Start

```bash
# Create agent configuration (interactive wizard)
promptforge init -o agent.config.json

# Validate configuration
promptforge validate -c agent.config.json

# Preview generated system prompt
promptforge preview -c agent.config.json

# Build JSON payload for OpenAI
promptforge build -c agent.config.json -f openai -o build/agent.json

# Build JSON payload for Anthropic
promptforge build -c agent.config.json -f anthropic -o build/agent.claude.json
```

## Usage in Code

```python
from promptforge import AgentConfig, PromptBuilder, export
from openai import OpenAI

# Load configuration
config = AgentConfig.from_file("agent.config.json")

# Build prompt with variable substitution
built = PromptBuilder(config, variables={"django_version": "5.1"}).build()

# Export to OpenAI format
payload = export(built, "openai")

# Use with API
response = OpenAI().chat.completions.create(**payload)
print(response.choices[0].message.content)
```

---

## Citation

If you use PromptForge in academic work or a project, we'd appreciate a citation:

```bibtex
@software{promptforge2026,
  author = {Your Name},
  title = {PromptForge: System Prompt Generator for LLM Agents},
  year = {2026},
  publisher = {PyPI},
  url = {https://pypi.org/project/promptforge-llm/},
  version = {1.0.0}
}
```

## License

This project is licensed under the [MIT License](LICENSE).

```
Copyright: Copyright (c) 2026 Alex Jurow (mandalay-rp)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```
