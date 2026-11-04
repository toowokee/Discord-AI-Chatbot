from bot.ollama_client import OllamaClient, OllamaError


class TestOllamaClient:
    def test_init(self) -> None:
        client = OllamaClient("http://localhost:11434", "gemma4")
        assert client._base_url == "http://localhost:11434"
        assert client._model == "gemma4"
        assert client._session is None

    def test_trailing_slash_stripped(self) -> None:
        client = OllamaClient("http://localhost:11434/", "gemma4")
        assert client._base_url == "http://localhost:11434"


class TestOllamaError:
    def test_is_exception(self) -> None:
        err = OllamaError("test error")
        assert isinstance(err, Exception)
        assert str(err) == "test error"
