import time
import pytest

from bot.memory import ConversationMemory


@pytest.fixture
def memory() -> ConversationMemory:
    return ConversationMemory(max_messages=10, summary_threshold=8, max_facts=5)


class TestConversationMemory:
    @pytest.mark.asyncio
    async def test_add_and_get(self, memory: ConversationMemory) -> None:
        await memory.add_message(1, 100, "user", "hello")
        await memory.add_message(1, 100, "assistant", "hi there")

        context, summary = await memory.get_context(1, 100)
        assert len(context) == 2
        assert context[0]["role"] == "user"
        assert context[0]["content"] == "hello"
        assert context[1]["role"] == "assistant"
        assert summary is None

    @pytest.mark.asyncio
    async def test_isolation_between_users(self, memory: ConversationMemory) -> None:
        await memory.add_message(1, 100, "user", "user1 msg")
        await memory.add_message(2, 100, "user", "user2 msg")

        ctx1, _ = await memory.get_context(1, 100)
        ctx2, _ = await memory.get_context(2, 100)

        assert len(ctx1) == 1
        assert ctx1[0]["content"] == "user1 msg"
        assert len(ctx2) == 1
        assert ctx2[0]["content"] == "user2 msg"

    @pytest.mark.asyncio
    async def test_isolation_between_channels(self, memory: ConversationMemory) -> None:
        await memory.add_message(1, 100, "user", "channel A")
        await memory.add_message(1, 200, "user", "channel B")

        ctxA, _ = await memory.get_context(1, 100)
        ctxB, _ = await memory.get_context(1, 200)

        assert ctxA[0]["content"] == "channel A"
        assert ctxB[0]["content"] == "channel B"

    @pytest.mark.asyncio
    async def test_max_messages_limit(self, memory: ConversationMemory) -> None:
        for i in range(15):
            await memory.add_message(1, 100, "user", f"msg {i}")

        context, _ = await memory.get_context(1, 100)
        assert len(context) <= memory.max_messages

    @pytest.mark.asyncio
    async def test_summarization_triggers(self, memory: ConversationMemory) -> None:
        for i in range(10):
            await memory.add_message(1, 100, "user", f"talking about python programming topic {i}")

        context, summary = await memory.get_context(1, 100)
        assert summary is not None
        assert len(summary) > 0

    @pytest.mark.asyncio
    async def test_clear(self, memory: ConversationMemory) -> None:
        await memory.add_message(1, 100, "user", "hello")
        await memory.clear(1, 100)

        context, summary = await memory.get_context(1, 100)
        assert context == []
        assert summary is None

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, memory: ConversationMemory) -> None:
        await memory.add_message(1, 100, "user", "old message")

        key = (1, 100)
        async with memory._lock:
            memory._conversations[key].last_active = time.time() - 7200

        removed = await memory.cleanup_expired(expiry_minutes=60)
        assert removed == 1

        context, _ = await memory.get_context(1, 100)
        assert context == []

    @pytest.mark.asyncio
    async def test_cleanup_keeps_active(self, memory: ConversationMemory) -> None:
        await memory.add_message(1, 100, "user", "fresh message")
        removed = await memory.cleanup_expired(expiry_minutes=60)
        assert removed == 0

        context, _ = await memory.get_context(1, 100)
        assert len(context) == 1

    @pytest.mark.asyncio
    async def test_get_stats(self, memory: ConversationMemory) -> None:
        await memory.add_message(1, 100, "user", "a")
        await memory.add_message(1, 100, "assistant", "b")
        await memory.add_message(2, 200, "user", "c")
        await memory.add_fact(500, "toowoke owns the bot")

        stats = await memory.get_stats()
        assert stats["active_conversations"] == 2
        assert stats["total_messages"] == 3
        assert stats["total_facts"] == 1

    @pytest.mark.asyncio
    async def test_empty_context(self, memory: ConversationMemory) -> None:
        context, summary = await memory.get_context(999, 999)
        assert context == []
        assert summary is None


class TestFactsMemory:
    @pytest.mark.asyncio
    async def test_add_and_get_fact(self, memory: ConversationMemory) -> None:
        res = await memory.add_fact(100, "toowoke owns the bot")
        assert res is True
        facts = await memory.get_facts(100)
        assert facts == ["toowoke owns the bot"]

    @pytest.mark.asyncio
    async def test_fact_deduplication(self, memory: ConversationMemory) -> None:
        await memory.add_fact(100, "toowoke owns the bot")
        res = await memory.add_fact(100, "toowoke owns the bot")
        assert res is False
        facts = await memory.get_facts(100)
        assert len(facts) == 1

    @pytest.mark.asyncio
    async def test_facts_isolated_by_scope(self, memory: ConversationMemory) -> None:
        await memory.add_fact(100, "fact for server A")
        await memory.add_fact(200, "fact for server B")

        factsA = await memory.get_facts(100)
        factsB = await memory.get_facts(200)

        assert factsA == ["fact for server A"]
        assert factsB == ["fact for server B"]

    @pytest.mark.asyncio
    async def test_clear_facts(self, memory: ConversationMemory) -> None:
        await memory.add_fact(100, "fact 1")
        await memory.add_fact(100, "fact 2")

        cleared = await memory.clear_facts(100)
        assert cleared == 2
        assert await memory.get_facts(100) == []

    @pytest.mark.asyncio
    async def test_max_facts_eviction(self, memory: ConversationMemory) -> None:
        for i in range(6):
            await memory.add_fact(100, f"fact {i}")

        facts = await memory.get_facts(100)
        assert len(facts) == 5
        assert "fact 0" not in facts
        assert "fact 5" in facts

    @pytest.mark.asyncio
    async def test_empty_fact_rejected(self, memory: ConversationMemory) -> None:
        assert await memory.add_fact(100, "   ") is False
        assert await memory.get_facts(100) == []


class TestBuildSummary:
    def test_basic_summary(self) -> None:
        messages = [
            {"role": "user", "content": "Can you explain Python decorators?"},
            {"role": "assistant", "content": "Decorators are a way to modify functions in Python."},
            {"role": "user", "content": "What about Python generators?"},
        ]
        summary = ConversationMemory.build_summary(messages)
        assert "python" in summary.lower()

    def test_empty_messages(self) -> None:
        assert ConversationMemory.build_summary([]) == ""

    def test_no_meaningful_words(self) -> None:
        messages = [{"role": "user", "content": "hi ok yes"}]
        assert ConversationMemory.build_summary(messages) == "General conversation."
