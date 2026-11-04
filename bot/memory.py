import asyncio
import time
from dataclasses import dataclass, field

from bot.safety import check_safety


@dataclass
class _Conversation:
    messages: list[dict[str, str]] = field(default_factory=list)
    last_active: float = field(default_factory=time.time)
    summary: str | None = None


class ConversationMemory:
    def __init__(
        self,
        max_messages: int = 60,
        summary_threshold: int = 50,
        max_facts: int = 100,
    ) -> None:
        self._conversations: dict[tuple[int, int], _Conversation] = {}
        self._facts: dict[int, list[str]] = {}
        self._lock = asyncio.Lock()
        self.max_messages = max_messages
        self.summary_threshold = summary_threshold
        self.max_facts = max_facts

    async def add_message(self, user_id: int, channel_id: int, role: str, content: str) -> None:
        key = (user_id, channel_id)
        async with self._lock:
            conv = self._conversations.get(key)
            if conv is None:
                conv = _Conversation()
                self._conversations[key] = conv

            conv.messages.append({"role": role, "content": content})
            conv.last_active = time.time()

            if len(conv.messages) > self.summary_threshold:
                self._summarize(conv)

    async def get_context(self, user_id: int, channel_id: int) -> tuple[list[dict[str, str]], str | None]:
        key = (user_id, channel_id)
        async with self._lock:
            conv = self._conversations.get(key)
            if conv is None:
                return [], None
            recent = conv.messages[-self.max_messages :]
            return list(recent), conv.summary

    async def clear(self, user_id: int, channel_id: int) -> None:
        key = (user_id, channel_id)
        async with self._lock:
            self._conversations.pop(key, None)

    async def cleanup_expired(self, expiry_minutes: int = 60) -> int:
        cutoff = time.time() - (expiry_minutes * 60)
        removed = 0
        async with self._lock:
            expired = [k for k, c in self._conversations.items() if c.last_active < cutoff]
            for k in expired:
                del self._conversations[k]
                removed += 1
        return removed

    async def add_fact(self, scope_id: int, fact: str) -> bool:
        clean = fact.strip()
        if not clean:
            return False

        safe, _ = check_safety(clean)
        if not safe:
            return False

        async with self._lock:
            facts = self._facts.setdefault(scope_id, [])
            if clean in facts:
                return False
            if len(facts) >= self.max_facts:
                facts.pop(0)
            facts.append(clean)
            return True

    async def get_facts(self, scope_id: int) -> list[str]:
        async with self._lock:
            return list(self._facts.get(scope_id, []))

    async def clear_facts(self, scope_id: int) -> int:
        async with self._lock:
            facts = self._facts.pop(scope_id, [])
            return len(facts)

    async def get_stats(self) -> dict[str, int]:
        async with self._lock:
            total_msgs = sum(len(c.messages) for c in self._conversations.values())
            total_facts = sum(len(f) for f in self._facts.values())
            return {
                "active_conversations": len(self._conversations),
                "total_messages": total_msgs,
                "total_facts": total_facts,
            }

    def _summarize(self, conv: _Conversation) -> None:
        keep = self.max_messages // 2
        old = conv.messages[:-keep]
        conv.messages = conv.messages[-keep:]

        new_summary = self.build_summary(old)
        if conv.summary:
            # Keep accumulated summary but cap its length to avoid runaway growth
            combined = f"{conv.summary} | {new_summary}"
            if len(combined) > 2000:
                combined = combined[-2000:]
            conv.summary = combined
        else:
            conv.summary = new_summary

    @staticmethod
    def build_summary(messages: list[dict[str, str]]) -> str:
        """Build a human-readable summary of old messages preserving key exchanges."""
        if not messages:
            return ""

        lines: list[str] = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "").strip()
            if not content:
                continue
            # Truncate very long individual messages but keep enough to be meaningful
            if len(content) > 300:
                content = content[:297] + "..."
            if role == "user":
                lines.append(f"User said: {content}")
            elif role == "assistant":
                lines.append(f"You replied: {content}")

        if not lines:
            return "General conversation."

        # Cap total summary chunk size
        summary = " | ".join(lines)
        if len(summary) > 1200:
            summary = summary[-1200:]
        return summary
