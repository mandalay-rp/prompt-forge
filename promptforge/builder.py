# PromptForge — system prompt generator for LLM agents
# Home: https://github.com/mandalay-rp/prompt-forge
#
# Author: Alex Jurow (mandalay-rp) <teletoo51@yahoo.com>
# Copyright: Copyright (c) 2026 Alex Jurow (mandalay-rp)
# License: MIT
"""Сборка детерминированного system-промта из конфигурации."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any

from .models import AgentConfig, ConfigError

PLACEHOLDER_RE = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*}}")

LANGUAGE_NAMES = {
    "ru": "русский",
    "en": "английский",
    "de": "немецкий",
    "fr": "французский",
    "es": "испанский",
    "kk": "казахский",
}


def estimate_tokens(text: str) -> int:
    """Точная оценка при установленном tiktoken, иначе эвристика."""
    try:  # pragma: no cover
        import tiktoken  # type: ignore

        return len(tiktoken.get_encoding("o200k_base").encode(text))
    except Exception:
        return math.ceil(len(text) / 3)


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _numbers(items: list[str]) -> str:
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))


@dataclass(slots=True)
class BuiltPrompt:
    text: str
    sections: dict[str, str]
    sha256: str
    tokens_estimate: int
    prompt_version: str
    config: AgentConfig

    def meta(self) -> dict[str, Any]:
        return {
            "agent": self.config.name,
            "config_version": self.config.version,
            "prompt_version": self.prompt_version,
            "sha256": self.sha256,
            "tokens_estimate": self.tokens_estimate,
            "language": self.config.language,
            "tools": [t.name for t in self.config.tools],
        }


class PromptBuilder:
    """PromptBuilder(config, variables={...}).build() -> BuiltPrompt."""

    def __init__(
        self, config: AgentConfig, *, variables: dict[str, str] | None = None
    ) -> None:
        self.config = config
        self.variables: dict[str, str] = {**config.variables, **(variables or {})}

    def build(self) -> BuiltPrompt:
        self.config.ensure_valid()
        sections = self._sections()
        body = "\n\n".join(
            f"## {i}. {title}\n{content}"
            for i, (title, content) in enumerate(sections.items(), 1)
        )
        header = f"# Системная инструкция агента «{self.config.name}» (v{self.config.version})"
        text = self._substitute(f"{header}\n\n{body}").strip() + "\n"
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return BuiltPrompt(
            text=text,
            sections=sections,
            sha256=digest,
            tokens_estimate=estimate_tokens(text),
            prompt_version=f"{self.config.version}+{digest[:8]}",
            config=self.config,
        )

    def _substitute(self, text: str) -> str:
        missing = sorted(
            {m.group(1) for m in PLACEHOLDER_RE.finditer(text)} - set(self.variables)
        )
        if missing:
            raise ConfigError(
                "Не заданы значения переменных: "
                + ", ".join(missing)
                + ". Передайте их через variables или --var key=value."
            )
        return PLACEHOLDER_RE.sub(lambda m: str(self.variables[m.group(1)]), text)

    def _sections(self) -> dict[str, str]:
        cfg = self.config
        s: dict[str, str] = {}

        role = f"Ты — {cfg.role}."
        if cfg.audience:
            role += f"\nТвоя аудитория: {cfg.audience}."
        s["Роль"] = role

        s["Цель"] = cfg.goal

        if cfg.context:
            s["Контекст"] = _bullets(cfg.context)
        if cfg.tasks:
            s["Задачи"] = _bullets(cfg.tasks)
        if cfg.tools:
            tools_lines = [f"`{t.name}` — {t.description}" for t in cfg.tools]
            policy = f"\n\n{cfg.tools_policy}" if cfg.tools_policy else ""
            s["Инструменты"] = _bullets(tools_lines) + policy
        if cfg.workflow:
            s["Порядок работы"] = _numbers(cfg.workflow)
        if cfg.rules:
            s["Правила"] = _bullets(cfg.rules)
        if cfg.prohibitions:
            s["Запреты"] = _bullets(f"НЕ {item}" for item in cfg.prohibitions)  # type: ignore

        s["Формат ответа"] = self._output_section()

        if cfg.fallback:
            s["Неопределённость и отказ"] = cfg.fallback

        style: list[str] = [
            f"Язык ответа: {LANGUAGE_NAMES.get(cfg.language, cfg.language)}.",
            "Отвечай по существу, без вступлений и извинений.",
        ]
        if cfg.tone:
            style.append("Тон: " + ", ".join(cfg.tone) + ".")
        s["Стиль"] = _bullets(style)

        if cfg.inline_examples and cfg.examples:
            blocks = [
                f"Пользователь:\n{ex.user}\n\nАссистент:\n{ex.assistant}"
                for ex in cfg.examples
            ]
            s["Примеры"] = "\n\n---\n\n".join(blocks)

        return s

    def _output_section(self) -> str:
        out = self.config.output
        lines: list[str] = []
        if out.format == "json":
            lines.append(
                "Верни ТОЛЬКО валидный JSON: без markdown-обёртки, комментариев и текста вне JSON."
            )
            if out.schema:
                lines.append(
                    "Схема ответа (JSON Schema):\n```json\n"
                    + json.dumps(out.schema, ensure_ascii=False, indent=2)
                    + "\n```"
                )
        elif out.format == "markdown":
            lines.append(
                "Формат ответа — Markdown: заголовки, списки, блоки кода с указанием языка."
            )
        else:
            lines.append("Формат ответа — простой текст без разметки.")
        lines.extend(out.instructions)
        return _bullets(lines)
