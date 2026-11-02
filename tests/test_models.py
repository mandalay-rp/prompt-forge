"""Tests for models module."""

from promptforge import AgentConfig, Tool


def test_valid_config():
    config = AgentConfig(
        name="test-agent",
        role="Test role",
        goal="Test goal",
    )
    errors = config.validate()
    assert errors == []


def test_invalid_name():
    config = AgentConfig(
        name="invalid name with spaces",
        role="Test",
        goal="Test",
    )
    errors = config.validate()
    assert any("name" in e.lower() for e in errors)


def test_temperature_range():
    config = AgentConfig(
        name="test-agent",
        role="Test",
        goal="Test",
        temperature=3.0,
    )
    errors = config.validate()
    assert any("temperature" in e.lower() for e in errors)


def test_tool_validation():
    config = AgentConfig(
        name="test-agent",
        role="Test",
        goal="Test",
        tools=[
            Tool(name="valid_tool", description="Valid"),
            Tool(name="valid_tool", description="Duplicate"),
        ],
    )
    errors = config.validate()
    assert any("duplicate" in e.lower() or "дубликат" in e.lower() for e in errors)


def test_from_dict():
    data = {
        "name": "test-agent",
        "role": "Test role",
        "goal": "Test goal",
    }
    config = AgentConfig.from_dict(data)
    assert config.name == "test-agent"
    assert config.temperature == 0.2  # default
