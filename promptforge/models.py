# PromptForge — system prompt generator for LLM agents
# Home: https://github.com/mandalay-rp/prompt-forge
#
# Author: Alex Jurow (mandalay-rp) <teletoo51@yahoo.com>
# Copyright: Copyright (c) 2026 Alex Jurow (mandalay-rp)
# License: MIT
"""Модели конфигурации LLM-агента. Только стандартная библиотека."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Literal

TOOL_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
OutputFormat = Literal["text", "markdown", "json"]


class ConfigError(ValueError):
    """Ошибка конфигурации агента."""


def _filter_kwargs(cls: type, data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ConfigError(
            f"{cls.__name__}: ожидался объект, получен {type(data).__name__}"
        )
    allowed = {f.name for f in fields(cls)}
    unknown = set(data) - allowed
    if unknown:
        raise ConfigError(
            f"{cls.__name__}: неизвестные поля: {', '.join(sorted(unknown))}"
        )
    return dict(data)


def _default_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }


@dataclass(slots=True)
class Tool:
    """Описание инструмента (function calling)."""

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=_default_schema)
    strict: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Tool":
        return cls(**_filter_kwargs(cls, data))

    def to_openai(self) -> dict[str, Any]:
        fn: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
        if self.strict:
            fn["strict"] = True
        return {"type": "function", "function": fn}

    def to_anthropic(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }


@dataclass(slots=True)
class Example:
    """Few-shot пример диалога."""

    user: str
    assistant: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Example":
        return cls(**_filter_kwargs(cls, data))


@dataclass(slots=True)
class OutputSpec:
    """Требования к формату ответа агента."""

    format: OutputFormat = "markdown"
    instructions: list[str] = field(default_factory=list)
    schema: dict[str, Any] | None = None
    schema_name: str = "agent_response"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OutputSpec":
        return cls(**_filter_kwargs(cls, data))


@dataclass(slots=True)
class AgentConfig:
    """Полное описание агента: роль, правила, инструменты, параметры модели."""

    name: str
    role: str
    goal: str
    version: str = "1.0.0"

    language: str = "ru"
    audience: str = ""
    tone: list[str] = field(default_factory=list)

    context: list[str] = field(default_factory=list)
    tasks: list[str] = field(default_factory=list)
    workflow: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    prohibitions: list[str] = field(default_factory=list)
    fallback: str = ""

    tools: list[Tool] = field(default_factory=list)
    tools_policy: str = (
        "Вызывай инструмент только если без него нельзя дать точный ответ. "
        "Не выдумывай результаты вызовов и аргументы."
    )
    examples: list[Example] = field(default_factory=list)
    inline_examples: bool = False
    output: OutputSpec = field(default_factory=OutputSpec)

    variables: dict[str, str] = field(default_factory=dict)

    model: str = "gpt-4.1-mini"
    temperature: float = 0.2
    top_p: float | None = None
    max_tokens: int = 2048
    token_param: Literal["max_tokens", "max_completion_tokens"] = "max_tokens"
    cache_system_prompt: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentConfig":
        kwargs = _filter_kwargs(cls, data)
        kwargs["tools"] = [
            t if isinstance(t, Tool) else Tool.from_dict(t)
            for t in kwargs.get("tools", [])
        ]
        kwargs["examples"] = [
            e if isinstance(e, Example) else Example.from_dict(e)
            for e in kwargs.get("examples", [])
        ]
        out = kwargs.get("output")
        if out is not None and not isinstance(out, OutputSpec):
            kwargs["output"] = OutputSpec.from_dict(out)
        return cls(**kwargs)

    @classmethod
    def from_file(cls, path: str | Path) -> "AgentConfig":
        path = Path(path)
        raw = path.read_text(encoding="utf-8")
        if path.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml  # type: ignore
            except ImportError as exc:  # pragma: no cover
                raise ConfigError(
                    "Для YAML установите PyYAML: pip install pyyaml"
                ) from exc
            data = yaml.safe_load(raw)
        else:
            data = json.loads(raw)
        return cls.from_dict(data)

    def validate(self) -> list[str]:
        errors: list[str] = []
        for key in ("name", "role", "goal"):
            if not str(getattr(self, key)).strip():
                errors.append(f"Поле '{key}' обязательно и не может быть пустым.")
        if not TOOL_NAME_RE.match(self.name):
            errors.append(
                "Поле 'name': допустимы только латиница, цифры, '_' и '-' (1–64 символа)."
            )
        if not 0.0 <= self.temperature <= 2.0:
            errors.append("Поле 'temperature' должно быть в диапазоне 0.0–2.0.")
        if self.top_p is not None and not 0.0 < self.top_p <= 1.0:
            errors.append("Поле 'top_p' должно быть в диапазоне (0.0, 1.0].")
        if self.max_tokens <= 0:
            errors.append("Поле 'max_tokens' должно быть положительным.")
        if self.output.format not in ("text", "markdown", "json"):
            errors.append("Поле 'output.format' должно быть text | markdown | json.")
        if self.output.format == "json" and self.output.schema is None:
            errors.append(
                "Для output.format='json' рекомендуется задать output.schema."
            )

        seen: set[str] = set()
        for tool in self.tools:
            if not TOOL_NAME_RE.match(tool.name):
                errors.append(f"Инструмент '{tool.name}': некорректное имя.")
            if tool.name in seen:
                errors.append(f"Инструмент '{tool.name}': дубликат имени.")
            seen.add(tool.name)
            if not tool.description.strip():
                errors.append(f"Инструмент '{tool.name}': пустое описание.")
            if tool.parameters.get("type") != "object":
                errors.append(
                    f"Инструмент '{tool.name}': parameters.type должен быть 'object'."
                )

        for i, ex in enumerate(self.examples, 1):
            if not ex.user.strip() or not ex.assistant.strip():
                errors.append(f"Пример №{i}: поля 'user' и 'assistant' обязательны.")
        return errors

    def ensure_valid(self) -> None:
        errors = self.validate()
        if errors:
            raise ConfigError(
                "Некорректная конфигурация агента:\n- " + "\n- ".join(errors)
            )
