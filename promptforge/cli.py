# PromptForge — system prompt generator for LLM agents
# Home: https://github.com/mandalay-rp/prompt-forge
#
# Author: Alex Jurow (mandalay-rp) <teletoo51@yahoo.com>
# Copyright: Copyright (c) 2026 Alex Jurow (mandalay-rp)
# License: MIT
"""CLI: python -m promptforge <command> [options]."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .builder import PromptBuilder
from .exporters import FORMATS, export
from .models import AgentConfig, ConfigError
from .sample import SAMPLE_CONFIG

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"


def _parse_vars(items: Sequence[str]) -> dict[str, str]:
    variables: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ConfigError(f"--var ожидает формат key=value, получено: {item!r}")
        key, value = item.split("=", 1)
        variables[key.strip()] = value
    return variables


def _write_json(path: Path, data: dict[str, Any], indent: int) -> None:
    """Атомарная запись JSON (UTF-8, без ASCII-эскейпов)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=indent) + "\n"
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="promptforge",
        description="Генератор system-промта LLM-агента в JSON для API-запросов.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser(
        "init",
        help="создать конфигурацию агента (интерактивно или из шаблона)",
    )
    p_init.add_argument("-o", "--out", default="agent.config.json", type=Path)
    p_init.add_argument(
        "--template",
        action="store_true",
        help="использовать готовый шаблон без интерактивного опроса",
    )
    p_init.add_argument(
        "--non-interactive",
        action="store_true",
        help="принудительно отключить интерактивный режим (аналог --template)",
    )
    p_init.add_argument(
        "--force", action="store_true", help="перезаписать существующий файл"
    )
    p_init.add_argument("--indent", type=int, default=2, help="отступ в итоговом JSON")
    p_init.add_argument(
        "--no-preview",
        action="store_true",
        help="не показывать итоговый конфиг перед сохранением",
    )

    for name, help_text in (
        ("validate", "проверить конфигурацию"),
        ("preview", "показать текст system-промта"),
        ("build", "собрать JSON-payload"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument(
            "-c", "--config", required=True, type=Path, help="JSON/YAML конфигурация"
        )
        p.add_argument("--var", action="append", default=[], metavar="KEY=VALUE")
        if name == "build":
            p.add_argument("-f", "--format", default="openai", choices=sorted(FORMATS))
            p.add_argument(
                "-o", "--out", type=Path, help="файл результата (по умолчанию stdout)"
            )
            p.add_argument("--indent", type=int, default=2)
            p.add_argument(
                "--no-examples", action="store_true", help="не добавлять few-shot"
            )
            p.add_argument("--meta", type=Path, help="доп. файл с метаданными промта")
    return parser


def _edit_in_editor(data: dict[str, Any]) -> dict[str, Any] | None:
    """Открыть JSON в $EDITOR и вернуть отредактированный конфиг (или None при ошибке)."""
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "nano"
    fd, tmp = tempfile.mkstemp(suffix=".json")
    tmp_path = Path(tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

        cmd = [*shlex.split(editor), str(tmp_path)]
        try:
            completed = subprocess.run(cmd, check=False)
        except (OSError, ValueError) as exc:
            print(f"{YELLOW}  ⚠ не удалось запустить редактор '{editor}': {exc}{RESET}")
            return None
        if completed.returncode != 0:
            print(
                f"{YELLOW}  ⚠ редактор завершился с кодом {completed.returncode}{RESET}"
            )
            return None

        loaded: Any = json.loads(tmp_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            print(f"{YELLOW}  ⚠ ожидался JSON-объект верхнего уровня{RESET}")
            return None

        edited: dict[str, Any] = loaded
        try:
            AgentConfig.from_dict(edited).ensure_valid()
        except ConfigError as exc:
            print(f"{YELLOW}  ⚠ {exc}{RESET}")
            return None
        return edited

    except (json.JSONDecodeError, OSError) as exc:
        print(f"{YELLOW}  ⚠ ошибка редактирования: {exc}{RESET}")
        return None
    finally:
        tmp_path.unlink(missing_ok=True)


def _confirm_preview(data: dict[str, Any], indent: int) -> dict[str, Any] | None:
    """Показать конфиг и спросить подтверждение. None — отказ от сохранения."""
    current = data
    while True:
        print(f"\n{BOLD}=== Предпросмотр конфигурации ==={RESET}")
        print(json.dumps(current, ensure_ascii=False, indent=indent))
        print(
            f"{BOLD}{CYAN}?{RESET} {BOLD}Сохранить этот конфиг?{RESET} "
            f"{DIM}[Y/n/edit]{RESET}"
        )
        try:
            choice = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if choice in {"", "y", "yes", "да", "д"}:
            return current
        if choice in {"n", "no", "нет", "н"}:
            return None
        if choice in {"edit", "e", "редактировать"}:
            edited = _edit_in_editor(current)
            if edited is not None:
                current = edited
                print(f"{GREEN}  ✓ изменения применены{RESET}")
            continue
        print(f"{YELLOW}  ⚠ введите y, n или edit{RESET}")


def _run_init(args: argparse.Namespace) -> int:
    out: Path = args.out
    if out.exists() and not args.force:
        raise ConfigError(f"Файл {out} уже существует. Используйте --force.")

    use_template = args.template or args.non_interactive or not sys.stdin.isatty()

    if use_template:
        config_data: dict[str, Any] = dict(SAMPLE_CONFIG)
    else:
        from .interactive import AbortError, run_wizard

        try:
            config_data = run_wizard()
        except AbortError:
            return 130

        if not args.no_preview:
            confirmed = _confirm_preview(config_data, args.indent)
            if confirmed is None:
                print(f"{YELLOW}Отменено пользователем.{RESET}")
                return 1
            config_data = confirmed

    _write_json(out, config_data, args.indent)
    print(f"{GREEN}Конфигурация создана: {out}{RESET}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "init":
            return _run_init(args)

        config = AgentConfig.from_file(args.config)
        builder = PromptBuilder(config, variables=_parse_vars(args.var))

        if args.command == "validate":
            errors = config.validate()
            if errors:
                raise ConfigError("Ошибки конфигурации:\n- " + "\n- ".join(errors))
            built = builder.build()
            print(
                f"OK: {config.name} v{built.prompt_version}, "
                f"~{built.tokens_estimate} токенов, {len(built.sections)} секций."
            )
            return 0

        built = builder.build()

        if args.command == "preview":
            sys.stdout.write(built.text)
            return 0

        payload = export(built, args.format, include_examples=not args.no_examples)
        if args.out:
            _write_json(args.out, payload, args.indent)
            print(
                f"Готово: {args.out} [{args.format}], "
                f"prompt v{built.prompt_version}, ~{built.tokens_estimate} токенов."
            )
        else:
            sys.stdout.write(
                json.dumps(payload, ensure_ascii=False, indent=args.indent) + "\n"
            )
        if args.meta:
            _write_json(args.meta, built.meta(), args.indent)
        return 0

    except ConfigError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Ошибка ввода-вывода: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
