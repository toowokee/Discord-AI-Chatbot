import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _get_int(key: str, default: int) -> int:
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _get_float(key: str, default: float) -> float:
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        return default


@dataclass(frozen=True)
class Config:
    discord_token: str = field(default_factory=lambda: os.getenv("DISCORD_TOKEN", ""))
    ollama_base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "gemma4"))
    temperature: float = field(default_factory=lambda: _get_float("OLLAMA_TEMPERATURE", 0.8))
    top_p: float = field(default_factory=lambda: _get_float("OLLAMA_TOP_P", 0.9))
    top_k: int = field(default_factory=lambda: _get_int("OLLAMA_TOP_K", 40))
    num_ctx: int = field(default_factory=lambda: _get_int("OLLAMA_NUM_CTX", 2048))
    repeat_penalty: float = field(default_factory=lambda: _get_float("OLLAMA_REPEAT_PENALTY", 1.1))
    max_context_messages: int = field(default_factory=lambda: _get_int("MAX_CONTEXT_MESSAGES", 20))
    memory_expiry_minutes: int = field(default_factory=lambda: _get_int("MEMORY_EXPIRY_MINUTES", 60))
    summary_threshold: int = field(default_factory=lambda: _get_int("SUMMARY_THRESHOLD", 15))
    max_response_tokens: int = field(default_factory=lambda: _get_int("MAX_RESPONSE_TOKENS", 450))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "WARNING"))

    def validate(self) -> None:
        if not self.discord_token:
            raise ValueError("DISCORD_TOKEN environment variable is required.")
        if not self.ollama_base_url:
            raise ValueError("OLLAMA_BASE_URL must be set.")
        if not self.ollama_model:
            raise ValueError("OLLAMA_MODEL must be set.")
