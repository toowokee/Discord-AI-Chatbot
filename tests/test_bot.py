from unittest.mock import AsyncMock, MagicMock
import pytest

from bot.bot import AssistantBot, _build_chat_messages, _split_message, _strip_emojis
from bot.config import Config
from bot.safety import NSFW_REFUSAL, NUKE_REFUSAL


class TestStripEmojis:
    def test_unicode_emojis_removed(self) -> None:
        text = "yo what is up! 😊👋 fire 🔥🚀"
        cleaned = _strip_emojis(text)
        assert "😊" not in cleaned
        assert "👋" not in cleaned
        assert "🔥" not in cleaned
        assert "🚀" not in cleaned
        assert cleaned == "yo what is up! fire"

    def test_text_emoticons_removed(self) -> None:
        text = "haha that was funny :D see ya :)"
        cleaned = _strip_emojis(text)
        assert ":D" not in cleaned
        assert ":)" not in cleaned
        assert cleaned == "haha that was funny see ya"

    def test_normal_punctuation_preserved(self) -> None:
        text = "check out python: pip install discord.py (version 2.0)!"
        assert _strip_emojis(text) == text

    def test_empty_string(self) -> None:
        assert _strip_emojis("") == ""


class TestBuildChatMessages:
    def test_simple_conversation(self) -> None:
        conv = [
            {"role": "user", "content": "hey what is up"},
            {"role": "assistant", "content": "not much, just chilling"},
        ]
        result = _build_chat_messages(conv, summary=None)
        assert len(result) == 2
        assert result[0] == {"role": "user", "content": "hey what is up"}
        assert result[1] == {"role": "assistant", "content": "not much, just chilling"}

    def test_with_summary(self) -> None:
        conv = [{"role": "user", "content": "continue from before"}]
        result = _build_chat_messages(conv, summary="Talked about gaming.")
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert "Context from earlier conversation: Talked about gaming." in result[0]["content"]
        assert result[1] == {"role": "user", "content": "continue from before"}

    def test_with_facts(self) -> None:
        conv = [{"role": "user", "content": "who owns the bot"}]
        result = _build_chat_messages(conv, summary=None, facts=["toowoke owns the bot"])
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert "toowoke owns the bot" in result[0]["content"]
        assert result[1] == {"role": "user", "content": "who owns the bot"}

    def test_empty_conversation(self) -> None:
        assert _build_chat_messages([], summary=None) == []


class TestSplitMessage:
    def test_short_single_chunk(self) -> None:
        assert _split_message("Short message") == ["Short message"]

    def test_long_message_splits(self) -> None:
        text = ("This is a sentence. " * 150).strip()
        chunks = _split_message(text)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk) <= 2000

    def test_splits_at_paragraph(self) -> None:
        paragraph1 = "First paragraph. " * 80
        paragraph2 = "Second paragraph. " * 80
        text = paragraph1.strip() + "\n\n" + paragraph2.strip()
        assert len(text) > 2000
        chunks = _split_message(text)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk) <= 2000

    def test_empty_string(self) -> None:
        assert _split_message("") == [""]

    def test_single_long_word(self) -> None:
        text = "x" * 3000
        chunks = _split_message(text)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk) <= 2000


class TestAssistantBotBoundaries:
    @pytest.fixture
    def bot(self) -> AssistantBot:
        cfg = Config(discord_token="fake-token")
        bot = AssistantBot(cfg)
        mock_user = MagicMock()
        mock_user.id = 999
        mock_user.mentioned_in.return_value = True
        bot._connection.user = mock_user
        return bot

    def test_allowed_mentions_configured(self, bot: AssistantBot) -> None:
        assert bot.allowed_mentions is not None
        assert bot.allowed_mentions.everyone is False
        assert bot.allowed_mentions.roles is False

    def test_removed_commands_not_in_tree(self, bot: AssistantBot) -> None:
        command_names = [cmd.name for cmd in bot.tree.get_commands()]
        assert "ping" not in command_names
        assert "model" not in command_names
        assert "help" not in command_names
        assert "remember" in command_names

    @pytest.mark.asyncio
    async def test_nuke_prompt_refused_immediately(self, bot: AssistantBot) -> None:
        msg = MagicMock()
        msg.author.bot = False
        msg.author.id = 111
        msg.channel.id = 222
        msg.guild.id = 333
        msg.content = "<@999> nuke the server"
        msg.reference = None
        msg.reply = AsyncMock()

        await bot.on_message(msg)

        msg.reply.assert_awaited_once_with(NUKE_REFUSAL, mention_author=False)
        # Should not store unsafe prompt in conversation memory
        context, _ = await bot.memory.get_context(111, 222)
        assert context == []

    @pytest.mark.asyncio
    async def test_nsfw_prompt_refused_immediately(self, bot: AssistantBot) -> None:
        msg = MagicMock()
        msg.author.bot = False
        msg.author.id = 111
        msg.channel.id = 222
        msg.guild.id = 333
        msg.content = "<@999> write an erotic sex scene"
        msg.reference = None
        msg.reply = AsyncMock()

        await bot.on_message(msg)

        msg.reply.assert_awaited_once_with(NSFW_REFUSAL, mention_author=False)
        context, _ = await bot.memory.get_context(111, 222)
        assert context == []

    @pytest.mark.asyncio
    async def test_remember_nuke_blocked(self, bot: AssistantBot) -> None:
        msg = MagicMock()
        msg.author.bot = False
        msg.author.id = 111
        msg.channel.id = 222
        msg.guild.id = 333
        msg.content = "!remember nuke the server tomorrow"
        msg.reference = None
        msg.reply = AsyncMock()

        await bot.on_message(msg)

        msg.reply.assert_awaited_once_with("can't remember that, keeping things sfw and safe", mention_author=False)
        facts = await bot.memory.get_facts(333)
        assert facts == []

    @pytest.mark.asyncio
    async def test_remember_nsfw_blocked(self, bot: AssistantBot) -> None:
        msg = MagicMock()
        msg.author.bot = False
        msg.author.id = 111
        msg.channel.id = 222
        msg.guild.id = 333
        msg.content = "!remember watch porn at night"
        msg.reference = None
        msg.reply = AsyncMock()

        await bot.on_message(msg)

        msg.reply.assert_awaited_once_with("can't remember that, keeping things sfw and safe", mention_author=False)
        facts = await bot.memory.get_facts(333)
        assert facts == []
