# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-02

### Added
- Initial release
- Interactive wizard for agent configuration creation
- Deterministic prompt rendering with SHA256 versioning
- Configuration validation (tool names, parameter ranges, required fields)
- Variable substitution (`{{key}}`) in prompt text
- Three export formats: OpenAI, Anthropic, universal raw
- Few-shot examples support (inline or as separate messages)
- Atomic file writing via `tempfile` + `os.replace`
- Django management command integration
- YAML configuration support (with PyYAML)
- Token estimation (heuristic or tiktoken)
- CLI commands: `init`, `validate`, `preview`, `build`
