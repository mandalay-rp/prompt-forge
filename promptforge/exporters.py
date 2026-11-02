# PromptForge — system prompt generator for LLM agents
# Home: https://github.com/mandalay-rp/prompt-forge
#
# Author: Alex Jurow (mandalay-rp) <teletoo51@yahoo.com>
# Copyright: Copyright (c) 2026 Alex Jurow (mandalay-rp)
# License: MIT
"""Экспорт собранного промта в JSON-payload конкретных API."""

from __future__ import annotations

import re
from typing import Any, Callable

from .builder import BuiltPrompt
from .models import ConfigError

_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9_-]")


def _few_shot(built: BuiltPrompt) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for ex in built.config.examples:
        messages.append({"role": "user", "content": ex.user})
        messages.append({"role": "assistant", "content": ex.assistant})
    return messages


def export_openai(
    built: BuiltPrompt, *, include_examples: bool = True
) -> dict[str, Any]:
    """Payload для client.chat.completions.create(**payload)."""
    cfg = built.config
    messages = [{"role": "system", "content": built.text}]
    if include_examples and not cfg.inline_examples:
        messages += _few_shot(built)

    payload: dict[str, Any] = {
        "model": cfg.model,
        "messages": messages,
        "temperature": cfg.temperature,
        cfg.token_param: cfg.max_tokens,
    }
    if cfg.top_p is not None:
        payload["top_p"] = cfg.top_p
    if cfg.tools:
        payload["tools"] = [t.to_openai() for t in cfg.tools]
        payload["tool_choice"] = "auto"
        payload["parallel_tool_calls"] = True
    if cfg.output.format == "json":
        if cfg.output.schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": _SAFE_NAME_RE.sub("_", cfg.output.schema_name or cfg.name),
                    "strict": True,
                    "schema": cfg.output.schema,
                },
            }
        else:
            payload["response_format"] = {"type": "json_object"}
    return payload


def export_anthropic(
    built: BuiltPrompt, *, include_examples: bool = True
) -> dict[str, Any]:
    """Payload для client.messages.create(**payload)."""
    cfg = built.config
    system: Any
    if cfg.cache_system_prompt:
        system = [
            {"type": "text", "text": built.text, "cache_control": {"type": "ephemeral"}}
        ]
    else:
        system = built.text

    payload: dict[str, Any] = {
        "model": cfg.model,
        "system": system,
        "messages": (
            _few_shot(built) if (include_examples and not cfg.inline_examples) else []
        ),
        "max_tokens": cfg.max_tokens,
        "temperature": min(cfg.temperature, 1.0),
    }
    if cfg.top_p is not None:
        payload["top_p"] = cfg.top_p
    if cfg.tools:
        payload["tools"] = [t.to_anthropic() for t in cfg.tools]
    return payload


def export_raw(built: BuiltPrompt, *, include_examples: bool = True) -> dict[str, Any]:
    """Универсальный формат: промт + метаданные + параметры модели."""
    cfg = built.config
    return {
        "name": cfg.name,
        "version": built.prompt_version,
        "system_prompt": built.text,
        "messages": [{"role": "system", "content": built.text}]
        + (_few_shot(built) if include_examples and not cfg.inline_examples else []),
        "tools": [t.to_openai() for t in cfg.tools],
        "output": {
            "format": cfg.output.format,
            "schema": cfg.output.schema,
        },
        "model_params": {
            "model": cfg.model,
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
            "max_tokens": cfg.max_tokens,
        },
        "metadata": {**cfg.metadata, **built.meta()},
    }


FORMATS: dict[str, Callable[..., dict[str, Any]]] = {
    "openai": export_openai,
    "anthropic": export_anthropic,
    "raw": export_raw,
}


def export(
    built: BuiltPrompt, fmt: str = "openai", *, include_examples: bool = True
) -> dict[str, Any]:
    try:
        exporter = FORMATS[fmt]
    except KeyError:
        raise ConfigError(
            f"Неизвестный формат '{fmt}'. Доступно: {', '.join(sorted(FORMATS))}"
        ) from None
    return exporter(built, include_examples=include_examples)
