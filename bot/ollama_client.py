import json
import logging
from typing import Any, AsyncGenerator

import aiohttp

logger = logging.getLogger(__name__)


class OllamaError(Exception):
    pass


class OllamaClient:
    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._session: aiohttp.ClientSession | None = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=10, keepalive_timeout=60)
            self._session = aiohttp.ClientSession(
                base_url=self._base_url,
                connector=connector,
                connector_owner=True,
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None

    async def preload_model(self) -> bool:
        session = await self._ensure_session()
        try:
            payload = {
                "model": self._model,
                "messages": [],
                "keep_alive": "60m",
            }
            async with session.post("/api/chat", json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                async for _ in resp.content:
                    pass
                return resp.status == 200
        except Exception as err:
            logger.warning("Failed to preload model: %s", err)
            return False

    async def chat(self, messages: list[dict[str, str]], **options: Any) -> str:
        session = await self._ensure_session()

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "keep_alive": "60m",
        }

        allowed = {"temperature", "top_p", "top_k", "num_ctx", "repeat_penalty", "num_predict"}
        opts = {k: v for k, v in options.items() if k in allowed}
        if opts:
            payload["options"] = opts

        try:
            async with session.post(
                "/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=180, connect=15),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise OllamaError(f"Ollama returned HTTP {resp.status}: {text[:200]}")

                data = await resp.json()
                return data.get("message", {}).get("content", "")

        except OllamaError:
            raise
        except aiohttp.ClientError as err:
            raise OllamaError(f"Connection error: {err}") from err
        except TimeoutError as err:
            raise OllamaError("Request timed out") from err
        except Exception as err:
            raise OllamaError(f"Unexpected error: {err}") from err

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        **options: Any,
    ) -> AsyncGenerator[str, None]:
        session = await self._ensure_session()

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": True,
            "keep_alive": "60m",
        }

        allowed = {"temperature", "top_p", "top_k", "num_ctx", "repeat_penalty", "num_predict"}
        opts = {k: v for k, v in options.items() if k in allowed}
        if opts:
            payload["options"] = opts

        try:
            async with session.post(
                "/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=90, connect=15),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise OllamaError(f"Ollama returned HTTP {resp.status}: {text[:200]}")

                async for raw_line in resp.content:
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    msg = chunk.get("message")
                    if msg:
                        token = msg.get("content", "")
                        if token:
                            yield token

                    if chunk.get("done", False):
                        break

        except OllamaError:
            raise
        except aiohttp.ClientError as err:
            raise OllamaError(f"Connection error: {err}") from err
        except TimeoutError as err:
            raise OllamaError("Request timed out") from err
        except Exception as err:
            raise OllamaError(f"Unexpected error: {err}") from err

    async def check_health(self) -> bool:
        session = await self._ensure_session()
        try:
            async with session.get("/api/tags", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                return resp.status == 200
        except Exception:
            return False

    async def get_model_info(self) -> dict[str, Any] | None:
        session = await self._ensure_session()
        try:
            async with session.post(
                "/api/show",
                json={"name": self._model},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception:
            return None
