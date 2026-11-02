# PromptForge — system prompt generator for LLM agents
# Home: https://github.com/mandalay-rp/prompt-forge
#
# Author: Alex Jurow (mandalay-rp) <teletoo51@yahoo.com>
# Copyright: Copyright (c) 2026 Alex Jurow (mandalay-rp)
# License: MIT
"""Интерактивный мастер создания конфигурации агента."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from typing import Any

from .models import AgentConfig

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"


class AbortError(Exception):
    """Пользователь прервал ввод (Ctrl+C)."""


# ---------- примитивы ввода ----------


def _prompt(label: str, hint: str = "", default: str = "") -> str:
    suffix = f" {DIM}(по умолчанию: {default!r}){RESET}" if default else ""
    hint_str = f" {DIM}{hint}{RESET}" if hint else ""
    return input(
        f"{BOLD}{CYAN}?{RESET} {BOLD}{label}{RESET}{hint_str}{suffix}: "
    ).strip()


def ask_str(
    label: str,
    *,
    hint: str = "",
    default: str = "",
    min_length: int = 0,
    validator: Callable[[str], str | None] | None = None,
) -> str:
    while True:
        value = _prompt(label, hint, default) or default
        if len(value) < min_length:
            print(
                f"{YELLOW}  ⚠ значение не может быть короче {min_length} символов{RESET}"
            )
            continue
        if validator is not None:
            err = validator(value)
            if err:
                print(f"{YELLOW}  ⚠ {err}{RESET}")
                continue
        return value


def ask_bool(label: str, *, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        raw = _prompt(label, hint).lower()
        if not raw:
            return default
        if raw in {"y", "yes", "да", "д"}:
            return True
        if raw in {"n", "no", "нет", "н"}:
            return False
        print(f"{YELLOW}  ⚠ введите y или n{RESET}")


def ask_choice(
    label: str, choices: Sequence[str], *, default: str | None = None
) -> str:
    choices_list = list(choices)
    if default and default not in choices_list:
        default = None
    hint = ", ".join(choices_list)
    while True:
        value = _prompt(label, f"[{hint}]", default or "")
        if not value and default:
            return default
        if value in choices_list:
            return value
        print(f"{YELLOW}  ⚠ допустимые значения: {', '.join(choices_list)}{RESET}")


def ask_list(label: str, *, hint: str = "", min_items: int = 0) -> list[str]:
    print(f"{BOLD}{CYAN}?{RESET} {BOLD}{label}{RESET} {DIM}{hint}{RESET}")
    print(
        f"  {DIM}Вводите по одному пункту на строку. Пустая строка — завершить.{RESET}"
    )
    items: list[str] = []
    while True:
        try:
            line = input(f"  {GREEN}#{len(items) + 1}{RESET} ")
        except EOFError:
            print()
            break
        line = line.strip()
        if not line:
            break
        items.append(line)
    if len(items) < min_items:
        print(f"{YELLOW}  ⚠ нужно минимум {min_items} пунктов, продолжайте ввод{RESET}")
        return items + ask_list(label, hint=hint, min_items=min_items - len(items))
    return items


def ask_multiline(label: str, *, hint: str = "", allow_empty: bool = True) -> str:
    print(f"{BOLD}{CYAN}?{RESET} {BOLD}{label}{RESET} {DIM}{hint}{RESET}")
    print(f"  {DIM}Многострочный ввод. Пустая строка — завершить.{RESET}")
    lines: list[str] = []
    while True:
        try:
            line = input("  │ ")
        except EOFError:
            print()
            break
        if line == "":
            break
        lines.append(line)
    text = "\n".join(lines).strip()
    if not text and not allow_empty:
        print(f"{YELLOW}  ⚠ поле не может быть пустым{RESET}")
        return ask_multiline(label, hint=hint, allow_empty=False)
    return text


def ask_json(label: str, *, hint: str = "", required: bool = False) -> Any | None:
    print(f"{BOLD}{CYAN}?{RESET} {BOLD}{label}{RESET} {DIM}{hint}{RESET}")
    print(f"  {DIM}Вставьте валидный JSON. Пустая строка — пропустить.{RESET}")
    buf: list[str] = []
    while True:
        try:
            line = input("  │ ")
        except EOFError:
            print()
            break
        if line == "":
            break
        buf.append(line)
    if not buf:
        if required:
            print(f"{YELLOW}  ⚠ поле обязательно{RESET}")
            return ask_json(label, hint=hint, required=True)
        return None
    raw = "\n".join(buf)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"{YELLOW}  ⚠ невалидный JSON: {exc}. Попробуйте ещё раз.{RESET}")
        return ask_json(label, hint=hint, required=required)


def ask_var(key: str) -> str:
    return ask_str(f"Значение переменной {{{{{key}}}}}")


# ---------- мастер ----------


def _ask_tools() -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    print()
    print(f"{BOLD}=== Инструменты (function calling) ==={RESET}")
    while True:
        if tools and not ask_bool("Добавить ещё один инструмент?", default=False):
            break
        if not tools and not ask_bool("Добавить инструменты?", default=True):
            break
        name = ask_str(
            "Имя инструмента",
            hint="[a-zA-Z0-9_-]",
            min_length=1,
            validator=lambda v: (
                None
                if __import__("re").match(r"^[a-zA-Z0-9_-]{1,64}$", v)
                else "только латиница/цифры/_/-, 1–64 символа"
            ),
        )
        description = ask_str("Описание инструмента", min_length=1)
        schema = ask_json(
            "JSON Schema параметров",
            hint='{"type":"object","properties":{...},"required":[...]}',
        )
        if schema is None:
            schema = {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            }
        strict = ask_bool("Включить strict mode?", default=False) if schema else False
        tools.append(
            {
                "name": name,
                "description": description,
                "parameters": schema,
                "strict": strict,
            }
        )
    return tools


def _ask_examples() -> list[dict[str, str]]:
    examples: list[dict[str, str]] = []
    print()
    print(f"{BOLD}=== Few-shot примеры ==={RESET}")
    if not ask_bool("Добавить примеры диалогов?", default=True):
        return examples
    while True:
        if examples and not ask_bool("Добавить ещё пример?", default=False):
            break
        print(f"\n{DIM}--- Пример №{len(examples) + 1} ---{RESET}")
        user = ask_multiline("Сообщение пользователя")
        assistant = ask_multiline("Ответ ассистента")
        examples.append({"user": user, "assistant": assistant})
    return examples


def _ask_output() -> dict[str, Any]:
    print()
    print(f"{BOLD}=== Формат ответа ==={RESET}")
    fmt = ask_choice(
        "Формат ответа",
        choices=["markdown", "json", "text"],
        default="markdown",
    )
    instructions = ask_list(
        "Дополнительные инструкции по формату",
        hint="(необязательно)",
    )
    schema = None
    schema_name = "agent_response"
    if fmt == "json":
        schema = ask_json(
            "JSON Schema ответа",
            hint='{"type":"object","properties":{...}}',
            required=True,
        )
        schema_name = ask_str("Имя схемы", default="agent_response")
    return {
        "format": fmt,
        "instructions": instructions,
        "schema": schema,
        "schema_name": schema_name,
    }


def _ask_variables() -> dict[str, str]:
    variables: dict[str, str] = {}
    print()
    print(f"{BOLD}=== Переменные шаблона ==={RESET}")
    print(f"  {DIM}Используются как {{{{key}}}} в тексте промта.{RESET}")
    if not ask_bool("Задать переменные?", default=False):
        return variables
    while True:
        key = ask_str("Имя переменной", hint="(пусто — завершить)")
        if not key:
            break
        value = ask_var(key)
        variables[key] = value
        if not ask_bool("Ещё переменная?", default=False):
            break
    return variables


def run_wizard() -> dict[str, Any]:
    """Пошаговый опрос пользователя, возврат готового конфига как dict."""
    print()
    print(f"{BOLD}{GREEN}=== PromptForge: мастер создания агента ==={RESET}")
    print(f"{DIM}На любом шаге Ctrl+C — прервать без сохранения.{RESET}\n")

    try:
        # --- Базовые поля ---
        print(f"{BOLD}=== Базовая информация ==={RESET}")
        name = ask_str(
            "Имя агента (латиница/цифры/_/-)",
            min_length=1,
            validator=lambda v: (
                None
                if __import__("re").match(r"^[a-zA-Z0-9_-]{1,64}$", v)
                else "некорректное имя"
            ),
        )
        version = ask_str("Версия", default="1.0.0")
        role = ask_str(
            "Роль агента", hint="напр. 'Senior Django-разработчик'", min_length=1
        )
        goal = ask_multiline("Цель агента", hint="1–3 предложения")
        audience = ask_str("Целевая аудитория", hint="(необязательно)")
        tone = ask_list("Тон общения", hint="(необязательно)")

        # --- Контекст и задачи ---
        print(f"\n{BOLD}=== Контекст и задачи ==={RESET}")
        context = ask_list("Контекст проекта", hint="(необязательно)")
        tasks = ask_list("Задачи агента", min_items=1)
        workflow = ask_list("Порядок работы", hint="(необязательно)")
        rules = ask_list("Правила", hint="(необязательно)")
        prohibitions = ask_list("Запреты", hint="(необязательно)")
        fallback = ask_multiline(
            "Поведение при неопределённости",
            hint="(необязательно)",
            allow_empty=True,
        )

        # --- Язык и стиль ---
        print(f"\n{BOLD}=== Язык и стиль ==={RESET}")
        language = ask_choice(
            "Язык ответа",
            choices=["ru", "en", "de", "fr", "es", "kk"],
            default="ru",
        )

        # --- Инструменты ---
        tools = _ask_tools()
        tools_policy = ""
        if tools:
            tools_policy = ask_multiline(
                "Политика использования инструментов",
                hint="(необязательно)",
                allow_empty=True,
            )

        # --- Примеры ---
        examples = _ask_examples()
        inline_examples = (
            ask_bool(
                "Встроить примеры в system-промт (inline)?",
                default=False,
            )
            if examples
            else False
        )

        # --- Вывод ---
        output = _ask_output()

        # --- Переменные ---
        variables = _ask_variables()

        # --- Модель ---
        print(f"\n{BOLD}=== Параметры модели ==={RESET}")
        model = ask_str("Имя модели", default="gpt-4.1-mini")
        temperature = float(
            ask_str(
                "Temperature",
                hint="[0.0..2.0]",
                default="0.2",
                validator=lambda v: (
                    None
                    if v.replace(".", "", 1).isdigit() and 0.0 <= float(v) <= 2.0
                    else "должно быть в диапазоне 0.0–2.0"
                ),
            )
        )
        top_p_raw = ask_str("Top-p", hint="(пусто — не задавать)")
        top_p: float | None = float(top_p_raw) if top_p_raw else None
        max_tokens = int(
            ask_str(
                "Max tokens",
                default="2048",
                validator=lambda v: (
                    None if v.isdigit() and int(v) > 0 else "положительное целое"
                ),
            )
        )
        token_param = ask_choice(
            "Параметр лимита токенов",
            choices=["max_tokens", "max_completion_tokens"],
            default="max_tokens",
        )
        cache_system_prompt = ask_bool(
            "Кэшировать system-промт (Anthropic cache_control)?",
            default=False,
        )

    except (KeyboardInterrupt, EOFError):
        print(f"\n{YELLOW}Прервано пользователем.{RESET}")
        raise AbortError() from None

    config: dict[str, Any] = {
        "name": name,
        "version": version,
        "role": role,
        "goal": goal,
        "language": language,
        "audience": audience,
        "tone": tone,
        "context": context,
        "tasks": tasks,
        "workflow": workflow,
        "rules": rules,
        "prohibitions": prohibitions,
        "fallback": fallback,
        "tools": tools,
        "tools_policy": tools_policy,
        "examples": examples,
        "inline_examples": inline_examples,
        "output": output,
        "variables": variables,
        "model": model,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "token_param": token_param,
        "cache_system_prompt": cache_system_prompt,
        "metadata": {},
    }

    # Валидация через модель
    AgentConfig.from_dict(config).ensure_valid()
    return config
