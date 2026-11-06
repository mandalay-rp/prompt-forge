<p align="center">
  <h1 align="center">PromptForge</h1>
  <p align="center">
    <em>CLI-утилита для генерации system-промтов для LLM-агентов с экспортом в JSON для API</em>
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
  <a href="README.en.md">English</a> | <strong>Русский</strong>
</p>

---

**PromptForge** — CLI-инструмент для создания, валидации и экспорта system-промтов LLM-агентов в готовые JSON-payload для API (OpenAI, Anthropic, универсальный формат).

### Ключевые возможности

- 🎯 **Интерактивный мастер** — пошаговое создание конфигурации агента
- 🔒 **Детерминированный рендер** — одинаковый конфиг → одинаковый `sha256` и версия промта
- ✅ **Валидация** конфигурации до генерации
- 🔧 **Подстановка переменных** `{{key}}` в тексте промта
- 📦 **Три формата экспорта**: OpenAI, Anthropic, универсальный raw
- 💬 **Few-shot примеры** — inline в system-промт или отдельными сообщениями
- 🛡️ **Атомарная запись** файлов
- 🎓 **Интеграция с Django** через management command

## Установка

```bash
pip install promptforge-llm

# С дополнительными зависимостями
pip install promptforge-llm[yaml]       # поддержка YAML-конфигов
pip install promptforge-llm[tokens]     # точная оценка токенов через tiktoken
pip install promptforge-llm[all]        # все опциональные зависимости
```

## Быстрый старт

```bash
# Создать конфигурацию агента (интерактивный мастер)
promptforge init -o agent.config.json

# Проверить конфигурацию
promptforge validate -c agent.config.json

# Посмотреть сгенерированный system-промт
promptforge preview -c agent.config.json

# Собрать JSON-payload для OpenAI
promptforge build -c agent.config.json -f openai -o build/agent.json

# Собрать JSON-payload для Anthropic
promptforge build -c agent.config.json -f anthropic -o build/agent.claude.json
```

## Использование в коде

```python
from promptforge import AgentConfig, PromptBuilder, export
from openai import OpenAI

# Загрузить конфигурацию
config = AgentConfig.from_file("agent.config.json")

# Собрать промт с подстановкой переменных
built = PromptBuilder(config, variables={"django_version": "5.1"}).build()

# Экспортировать в формат OpenAI
payload = export(built, "openai")

# Использовать с API
response = OpenAI().chat.completions.create(**payload)
print(response.choices[0].message.content)
```

---

## Цитирование

Если вы используете PromptForge в научной работе или проекте, будем признательны за ссылку:

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

## Лицензия

Проект распространяется под лицензией [MIT](LICENSE).

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
