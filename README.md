# PromptForge

Генератор system-промтов для LLM-агентов с экспортом в JSON для API (OpenAI, Anthropic, универсальный формат).

Читать на [English](README.en.md)

## Возможности

- **Интерактивный мастер** создания конфигурации агента с пошаговым опросом
- **Детерминированный рендер** — одинаковый конфиг → одинаковый `sha256` и версия промта
- **Валидация** конфигурации до генерации (имена инструментов, диапазоны параметров, обязательные поля)
- **Подстановка переменных** `{{key}}` в тексте промта
- **Три формата экспорта**: OpenAI, Anthropic, универсальный raw
- **Few-shot примеры** — inline в system-промт или отдельными сообщениями
- **Атомарная запись** файлов через `tempfile` + `os.replace`
- **Интеграция с Django** через management command

## Требования

- Python ≥ 3.10
- Опционально:
  - `PyYAML` — для загрузки YAML-конфигов
  - `tiktoken` — для точной оценки токенов (иначе эвристика)

```bash
pip install pyyaml tiktoken
```

## Структура проекта

```
promptforge/
├── __init__.py          # публичный API
├── __main__.py          # точка входа CLI
├── models.py            # модели конфигурации (dataclasses)
├── builder.py           # сборка system-промта
├── exporters.py         # экспорт в JSON для API
├── interactive.py       # интерактивный мастер
├── sample.py            # эталонная конфигурация
└── cli.py               # CLI-команды
```

## Быстрый старт

### 1. Создать конфигурацию агента

```bash
# Интерактивный мастер (по умолчанию)
python -m promptforge init -o agent.config.json

# Из готового шаблона (без опроса)
python -m promptforge init -o agent.config.json --template

# Принудительно неинтерактивно (для CI/CD)
python -m promptforge init -o agent.config.json --non-interactive

# Перезаписать существующий файл
python -m promptforge init -o agent.config.json --force

# Без предпросмотра перед сохранением
python -m promptforge init -o agent.config.json --no-preview
```

### 2. Проверить конфигурацию

```bash
python -m promptforge validate -c agent.config.json
# OK: django-code-reviewer v1.0.0+a1b2c3d4, ~1234 токенов, 9 секций.
```

### 3. Посмотреть текст промта

```bash
python -m promptforge preview -c agent.config.json --var django_version=5.1
```

### 4. Собрать JSON-payload для API

```bash
# Для OpenAI
python -m promptforge build -c agent.config.json -f openai -o build/agent.json

# Для Anthropic
python -m promptforge build -c agent.config.json -f anthropic -o build/agent.claude.json

# Универсальный формат
python -m promptforge build -c agent.config.json -f raw -o build/agent.raw.json

# С метаданными промта
python -m promptforge build -c agent.config.json -f openai -o build/agent.json --meta build/agent.meta.json

# Без few-shot примеров
python -m promptforge build -c agent.config.json -f openai -o build/agent.json --no-examples
```

## Интерактивный мастер

Команда `init` по умолчанию запускает пошаговый мастер. На любом шаге `Ctrl+C` прерывает процесс без сохранения файла.

### Пример диалога

```
$ python -m promptforge init -o my_agent.json

=== PromptForge: мастер создания агента ===
На любом шаге Ctrl+C — прервать без сохранения.

=== Базовая информация ===
? Имя агента (латиница/цифры/_/-) [a-zA-Z0-9_-]: django-reviewer
? Версия  (по умолчанию: '1.0.0'): 
? Роль агента напр. 'Senior Django-разработчик': Senior Python/Django инженер
? Цель агента 1–3 предложения
  Многострочный ввод. Пустая строка — завершить.
  │ Находить дефекты и уязвимости в коде
  │ и предлагать исправления.
  │ 
? Целевая аудитория (необязательно): backend middle+
? Тон общения (необязательно)
  Вводите по одному пункту на строку. Пустая строка — завершить.
  #1 профессиональный
  #2 без воды
  #3 

=== Контекст и задачи ===
? Контекст проекта (необязательно)
  #1 Стек: Python {{python_version}}, Django {{django_version}}
  #2 
? Задачи агента
  #1 Проверять ORM-запросы на N+1
  #2 Искать проблемы безопасности
  #3 
? Порядок работы (необязательно)
  #1 Определи назначение кода
  #2 Составь список находок
  #3 
? Правила (необязательно)
  #1 Каждая находка содержит путь к файлу
  #2 
? Запреты (необязательно)
  #1 выдумывать содержимое файлов
  #2 
? Поведение при неопределённости (необязательно)
  │ Если данных недостаточно — задай уточняющий вопрос.
  │ 

=== Язык и стиль ===
? Язык ответа [ru, en, de, fr, es, kk] (по умолчанию: 'ru'): 

=== Инструменты (function calling) ===
? Добавить инструменты? [Y/n]: y
? Имя инструмента [a-zA-Z0-9_-]: get_file
? Описание инструмента: Прочитать файл из репозитория
? JSON Schema параметров {"type":"object","properties":{...},"required":[...]}
  │ {"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}
  │ 
? Включить strict mode? [y/N]: y
? Добавить ещё один инструмент? [y/N]: n

=== Few-shot примеры ===
? Добавить примеры диалогов? [Y/n]: y
--- Пример №1 ---
? Сообщение пользователя
  │ Проверь этот код: for order in Order.objects.all(): print(order.user.email)
  │ 
? Ответ ассистента
  │ **major — N+1 запрос.** Используй select_related('user').
  │ 
? Добавить ещё пример? [y/N]: n
? Встроить примеры в system-промт (inline)? [y/N]: n

=== Формат ответа ===
? Формат ответа [markdown, json, text] (по умолчанию: 'markdown'): markdown
? Дополнительные инструкции по формату (необязательно)
  #1 Структура: Находки → Исправления → Резюме
  #2 

=== Переменные шаблона ===
? Задать переменные? [y/N]: y
? Имя переменной (пусто — завершить): django_version
? Значение переменной {{django_version}}: 5.1
? Ещё переменная? [y/N]: y
? Имя переменной (пусто — завершить): python_version
? Значение переменной {{python_version}}: 3.12
? Ещё переменная? [y/N]: n

=== Параметры модели ===
? Имя модели  (по умолчанию: 'gpt-4.1-mini'): 
? Temperature [0.0..2.0] (по умолчанию: '0.2'): 
? Top-p (пусто — не задавать): 
? Max tokens  (по умолчанию: '2048'): 
? Параметр лимита токенов [max_tokens, max_completion_tokens] (по умолчанию: 'max_tokens'): 
? Кэшировать system-промт (Anthropic cache_control)? [y/N]: n

=== Предпросмотр конфигурации ===
{
  "name": "django-reviewer",
  "version": "1.0.0",
  "role": "Senior Python/Django инженер",
  "goal": "Находить дефекты и уязвимости в коде\nи предлагать исправления.",
  ...
}
? Сохранить этот конфиг? [Y/n/edit]: y
Конфигурация создана: my_agent.json
```

### Особенности мастера

- **Автоопределение режима**: если `stdin` не TTY (пайп, CI), автоматически используется шаблон
- **Валидация на лету**: каждое поле проверяется сразу — при ошибке переспрос, а не падение
- **Многострочный ввод**: для `goal`, `fallback`, примеров — пустая строка завершает блок
- **Редактирование перед сохранением**: ответ `edit` открает JSON в `$EDITOR`
- **Локализованные ответы**: принимаются `y/n/да/нет`

## Формат конфигурации

Конфигурация — JSON (или YAML при наличии PyYAML) со следующей структурой:

```json
{
  "name": "django-code-reviewer",
  "version": "1.0.0",
  "role": "Senior Python/Django инженер, проводящий код-ревью",
  "goal": "Находить дефекты и предлагать исправления.",
  
  "language": "ru",
  "audience": "backend-разработчики уровня middle+",
  "tone": ["профессиональный", "без воды"],
  
  "context": [
    "Стек проекта: Python {{python_version}}, Django {{django_version}}."
  ],
  "tasks": [
    "Проверять корректность ORM-запросов.",
    "Искать проблемы безопасности."
  ],
  "workflow": [
    "Определи назначение кода.",
    "Составь список находок.",
    "Предложи исправления."
  ],
  "rules": [
    "Каждая находка содержит путь к файлу."
  ],
  "prohibitions": [
    "выдумывать содержимое файлов, которых не видел"
  ],
  "fallback": "Если данных недостаточно — задай уточняющий вопрос.",
  
  "tools": [
    {
      "name": "get_file",
      "description": "Прочитать содержимое файла из репозитория.",
      "parameters": {
        "type": "object",
        "properties": {
          "path": {"type": "string", "description": "Путь к файлу"}
        },
        "required": ["path"],
        "additionalProperties": false
      },
      "strict": true
    }
  ],
  "tools_policy": "Читай файл инструментом get_file прежде чем делать выводы.",
  
  "examples": [
    {
      "user": "Проверь: for order in Order.objects.all(): print(order.user.email)",
      "assistant": "**major — N+1 запрос.** Используй select_related('user')."
    }
  ],
  "inline_examples": false,
  
  "output": {
    "format": "markdown",
    "instructions": [
      "Структура: Находки → Исправления → Резюме."
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

### Обязательные поля

| Поле | Тип | Описание |
|------|-----|----------|
| `name` | string | Имя агента: латиница, цифры, `_`, `-` (1–64 символа) |
| `role` | string | Роль агента |
| `goal` | string | Цель агента |

### Опциональные поля

| Поле | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| `version` | string | `"1.0.0"` | Версия конфигурации |
| `language` | string | `"ru"` | Язык ответа (`ru`, `en`, `de`, `fr`, `es`, `kk`) |
| `audience` | string | `""` | Целевая аудитория |
| `tone` | list[string] | `[]` | Тон общения |
| `context` | list[string] | `[]` | Контекст проекта |
| `tasks` | list[string] | `[]` | Задачи агента |
| `workflow` | list[string] | `[]` | Порядок работы |
| `rules` | list[string] | `[]` | Правила |
| `prohibitions` | list[string] | `[]` | Запреты |
| `fallback` | string | `""` | Поведение при неопределённости |
| `tools` | list[Tool] | `[]` | Инструменты (function calling) |
| `tools_policy` | string | см. код | Политика использования инструментов |
| `examples` | list[Example] | `[]` | Few-shot примеры |
| `inline_examples` | bool | `false` | Встроить примеры в system-промт |
| `output.format` | string | `"markdown"` | Формат ответа: `text`, `markdown`, `json` |
| `output.instructions` | list[string] | `[]` | Инструкции по формату |
| `output.schema` | object | `null` | JSON Schema ответа (для `format: json`) |
| `output.schema_name` | string | `"agent_response"` | Имя схемы |
| `variables` | object | `{}` | Переменные для подстановки `{{key}}` |
| `model` | string | `"gpt-4.1-mini"` | Имя модели |
| `temperature` | float | `0.2` | Температура (0.0–2.0) |
| `top_p` | float | `null` | Top-p (0.0–1.0) |
| `max_tokens` | int | `2048` | Лимит токенов |
| `token_param` | string | `"max_tokens"` | Имя параметра лимита |
| `cache_system_prompt` | bool | `false` | Кэшировать system-промт (Anthropic) |
| `metadata` | object | `{}` | Произвольные метаданные |

### Структура Tool

```json
{
  "name": "get_file",
  "description": "Прочитать содержимое файла.",
  "parameters": {
    "type": "object",
    "properties": {
      "path": {"type": "string", "description": "Путь к файлу"}
    },
    "required": ["path"],
    "additionalProperties": false
  },
  "strict": true
}
```

### Структура Example

```json
{
  "user": "Сообщение пользователя",
  "assistant": "Ответ ассистента"
}
```

## Программное использование

### Базовый пример

```python
from promptforge import AgentConfig, PromptBuilder, export

# Загрузить конфигурацию
config = AgentConfig.from_file("agent.config.json")

# Собрать промт с подстановкой переменных
built = PromptBuilder(config, variables={"django_version": "5.1"}).build()

# Экспортировать в формат OpenAI
payload = export(built, "openai")

# Использовать с OpenAI API
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(**payload)
print(response.choices[0].message.content)
```

### Метаданные промта

```python
from promptforge import AgentConfig, PromptBuilder

config = AgentConfig.from_file("agent.config.json")
built = PromptBuilder(config).build()

print(f"Версия промта: {built.prompt_version}")
print(f"SHA256: {built.sha256}")
print(f"Оценка токенов: {built.tokens_estimate}")
print(f"Секции: {list(built.sections.keys())}")

# Метаданные для логирования
meta = built.meta()
print(meta)
# {
#   "agent": "django-code-reviewer",
#   "config_version": "1.0.0",
#   "prompt_version": "1.0.0+a1b2c3d4",
#   "sha256": "...",
#   "tokens_estimate": 1234,
#   "language": "ru",
#   "tools": ["get_file", "run_tests"]
# }
```

### Создание конфигурации из кода

```python
from promptforge import AgentConfig, Tool, Example, OutputSpec

config = AgentConfig(
    name="my-agent",
    role="Помощник",
    goal="Отвечать на вопросы",
    language="ru",
    tools=[
        Tool(
            name="search",
            description="Поиск в базе знаний",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        )
    ],
    examples=[
        Example(user="Что такое Django?", assistant="Django — это веб-фреймворк.")
    ],
    output=OutputSpec(format="markdown"),
)

# Валидация
errors = config.validate()
if errors:
    print("Ошибки:", errors)
else:
    config.ensure_valid()  # выбросит исключение при ошибках
```

### Создание конфигурации из словаря

```python
from promptforge import AgentConfig

config_dict = {
    "name": "my-agent",
    "role": "Помощник",
    "goal": "Отвечать на вопросы",
}

config = AgentConfig.from_dict(config_dict)
```

## Django-интеграция

### Management command

Создайте файл `apps/agents/management/commands/build_agent_prompt.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from promptforge import AgentConfig, ConfigError, PromptBuilder, export
from promptforge.exporters import FORMATS


class Command(BaseCommand):
    help = "Собрать system-промт агента в JSON-payload для LLM API."

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
                f"~{built.tokens_estimate} токенов, sha256={built.sha256[:12]}"
            )
        )
```

Использование:

```bash
python manage.py build_agent_prompt -c configs/django_reviewer.json -o build/agent.json
```

## Форматы экспорта

### OpenAI

```bash
python -m promptforge build -c agent.config.json -f openai -o agent.json
```

Результат:

```json
{
  "model": "gpt-4.1-mini",
  "messages": [
    {"role": "system", "content": "# Системная инструкция агента ..."},
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

Использование:

```python
import json
from openai import OpenAI

payload = json.load(open("agent.json", encoding="utf-8"))
payload["messages"].append({"role": "user", "content": "Проверь apps/orders/views.py"})

resp = OpenAI().chat.completions.create(**payload)
print(resp.choices[0].message.content)
```

### Anthropic

```bash
python -m promptforge build -c agent.config.json -f anthropic -o agent.claude.json
```

Результат:

```json
{
  "model": "claude-3-5-sonnet-20241022",
  "system": "# Системная инструкция агента ...",
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

С кэшированием system-промта (если `cache_system_prompt: true` в конфиге):

```json
{
  "system": [
    {
      "type": "text",
      "text": "# Системная инструкция агента ...",
      "cache_control": {"type": "ephemeral"}
    }
  ]
}
```

Использование:

```python
import json
from anthropic import Anthropic

payload = json.load(open("agent.claude.json", encoding="utf-8"))
payload["messages"].append({"role": "user", "content": "Проверь код"})

resp = Anthropic().messages.create(**payload)
print(resp.content[0].text)
```

### Raw (универсальный)

```bash
python -m promptforge build -c agent.config.json -f raw -o agent.raw.json
```

Результат:

```json
{
  "name": "django-code-reviewer",
  "version": "1.0.0+a1b2c3d4",
  "system_prompt": "# Системная инструкция агента ...",
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

## Переменные и шаблоны

В тексте конфигурации можно использовать переменные `{{key}}`, которые будут подставлены при сборке промта.

### Задание переменных в конфиге

```json
{
  "context": [
    "Стек проекта: Python {{python_version}}, Django {{django_version}}."
  ],
  "variables": {
    "python_version": "3.12",
    "django_version": "5.0"
  }
}
```

### Переопределение через CLI

```bash
python -m promptforge build -c agent.config.json --var django_version=5.1 --var python_version=3.13
```

### Переопределение в коде

```python
built = PromptBuilder(config, variables={"django_version": "5.1"}).build()
```

### Ошибка при отсутствии переменных

Если в тексте есть `{{key}}`, но значение не задано, будет ошибка:

```
Ошибка: Не заданы значения переменных: django_version. Передайте их через variables или --var key=value.
```

## Few-shot примеры

Примеры можно встраивать в system-промт или добавлять как отдельные сообщения.

### Inline в system-промт

```json
{
  "examples": [
    {
      "user": "Вопрос",
      "assistant": "Ответ"
    }
  ],
  "inline_examples": true
}
```

Результат: секция "Примеры" в system-промте.

### Отдельные сообщения (по умолчанию)

```json
{
  "examples": [
    {
      "user": "Вопрос",
      "assistant": "Ответ"
    }
  ],
  "inline_examples": false
}
```

Результат: примеры добавляются в `messages` после system-промта.

### Без примеров

```bash
python -m promptforge build -c agent.config.json --no-examples
```

## Валидация

Команда `validate` проверяет конфигурацию:

```bash
python -m promptforge validate -c agent.config.json
```

Проверяются:

- Обязательные поля (`name`, `role`, `goal`)
- Формат имени агента (regex `^[a-zA-Z0-9_-]{1,64}$`)
- Диапазоны `temperature` (0.0–2.0) и `top_p` (0.0–1.0)
- Положительность `max_tokens`
- Корректность `output.format`
- Наличие `output.schema` для `format: json`
- Уникальность имён инструментов
- Корректность имён инструментов
- Непустые описания инструментов
- `parameters.type == "object"` для инструментов
- Непустые поля `user` и `assistant` в примерах

Пример ошибки:

```
Ошибка: Некорректная конфигурация агента:
- Поле 'name' обязательно и не может быть пустым.
- Поле 'temperature' должно быть в диапазоне 0.0–2.0.
- Инструмент 'get_file': дубликат имени.
```

## Метаданные промта

Команда `build` с флагом `--meta` сохраняет метаданные промта:

```bash
python -m promptforge build -c agent.config.json -f openai -o agent.json --meta agent.meta.json
```

Содержимое `agent.meta.json`:

```json
{
  "agent": "django-code-reviewer",
  "config_version": "1.0.0",
  "prompt_version": "1.0.0+a1b2c3d4",
  "sha256": "a1b2c3d4e5f6...",
  "tokens_estimate": 1234,
  "language": "ru",
  "tools": ["get_file", "run_tests"]
}
```

Используйте для:

- Логирования версий промтов
- Отслеживания изменений
- A/B тестирования
- Мониторинга стоимости (через `tokens_estimate`)

## Оценка токенов

По умолчанию используется эвристика: `tokens ≈ len(text) / 3`.

Для точной оценки установите `tiktoken`:

```bash
pip install tiktoken
```

После установки автоматически используется кодировка `o200k_base`.

## Лицензия

MIT
