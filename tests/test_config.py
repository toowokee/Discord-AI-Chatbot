import pytest

from bot.config import Config


class TestConfig:
    def test_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        monkeypatch.delenv("OLLAMA_TEMPERATURE", raising=False)
        monkeypatch.delenv("MAX_CONTEXT_MESSAGES", raising=False)
        monkeypatch.delenv("MEMORY_EXPIRY_MINUTES", raising=False)
        monkeypatch.setenv("DISCORD_TOKEN", "test-token")
        cfg = Config()
        assert cfg.discord_token == "test-token"
        assert cfg.ollama_model == "gemma4"
        assert cfg.ollama_base_url == "http://localhost:11434"
        assert cfg.temperature == 0.8
        assert cfg.max_context_messages == 20
        assert cfg.memory_expiry_minutes == 60

    def test_custom_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DISCORD_TOKEN", "tok")
        monkeypatch.setenv("OLLAMA_MODEL", "gemma4:27b")
        monkeypatch.setenv("OLLAMA_TEMPERATURE", "0.5")
        monkeypatch.setenv("MAX_CONTEXT_MESSAGES", "10")
        cfg = Config()
        assert cfg.ollama_model == "gemma4:27b"
        assert cfg.temperature == 0.5
        assert cfg.max_context_messages == 10

    def test_validate_missing_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("DISCORD_TOKEN", raising=False)
        cfg = Config(discord_token="")
        with pytest.raises(ValueError, match="DISCORD_TOKEN"):
            cfg.validate()

    def test_validate_passes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cfg = Config(discord_token="tok", ollama_base_url="http://localhost:11434", ollama_model="gemma4")
        cfg.validate()

    def test_invalid_int_falls_back(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DISCORD_TOKEN", "tok")
        monkeypatch.setenv("MAX_CONTEXT_MESSAGES", "not_a_number")
        cfg = Config()
        assert cfg.max_context_messages == 20

    def test_invalid_float_falls_back(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DISCORD_TOKEN", "tok")
        monkeypatch.setenv("OLLAMA_TEMPERATURE", "abc")
        cfg = Config()
        assert cfg.temperature == 0.8

    def test_frozen(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cfg = Config(discord_token="tok")
        with pytest.raises(AttributeError):
            cfg.discord_token = "new"  # type: ignore[misc]
