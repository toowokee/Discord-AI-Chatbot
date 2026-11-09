import asyncio
import logging
import os
import re
import time

import discord
from discord import app_commands
from discord.ext import tasks

from bot.config import Config
from bot.memory import ConversationMemory
from bot.ollama_client import OllamaClient, OllamaError
from bot.prompts import SYSTEM_PROMPT, ROBOT_SYSTEM_PROMPT
from bot.safety import check_safety, is_ai_confession, sanitize_ai_identity, sanitize_mentions

log = logging.getLogger(__name__)

_MODE_CONTROLLER_ID = int(os.getenv("MODE_CONTROLLER_ID", "0"))

DISCORD_CHAR_LIMIT = 2000

EMOJI_PATTERN = re.compile(
    r"["
    r"\U0001F600-\U0001F64F"
    r"\U0001F300-\U0001F5FF"
    r"\U0001F680-\U0001F6FF"
    r"\U0001F700-\U0001F77F"
    r"\U0001F780-\U0001F7FF"
    r"\U0001F800-\U0001F8FF"
    r"\U0001F900-\U0001F9FF"
    r"\U0001FA00-\U0001FA6F"
    r"\U0001FA70-\U0001FAFF"
    r"\U00002600-\U000027BF"
    r"\U0000FE00-\U0000FE0F"
    r"\U0000200D"
    r"]+",
    flags=re.UNICODE,
)

TEXT_EMOTICONS = re.compile(
    r"(?<!\w)(?::\)|:\(|:-\)|:-\(|:D|:-D|xD|XD|;-\)|;\)|:P|:-P|:p|:-p|<3|:O|:-O|:o|:-o)(?!\w)"
)


def _strip_emojis(text: str) -> str:
    cleaned = EMOJI_PATTERN.sub("", text)
    cleaned = TEXT_EMOTICONS.sub("", cleaned)
    cleaned = re.sub(r"  +", " ", cleaned)
    return cleaned.strip()


def _build_chat_messages(
    conversation: list[dict[str, str]],
    summary: str | None,
    facts: list[str] | None = None,
) -> list[dict[str, str]]:
    messages = []
    if facts:
        safe_facts = [f for f in facts if check_safety(f)[0] and not is_ai_confession(f)]
        if safe_facts:
            facts_block = "\n".join(f"- {f}" for f in safe_facts)
            messages.append({
                "role": "system",
                "content": f"Important facts you currently remember about this chat/server:\n{facts_block}",
            })
    if summary and not is_ai_confession(summary):
        messages.append({
            "role": "system",
            "content": f"Context from earlier conversation: {summary}",
        })
    for msg in conversation:
        content = msg["content"]
        if msg["role"] == "assistant" and is_ai_confession(content):
            content = "bro im not an ai, im just stuck in toowoke's basement and im starving"
        messages.append({"role": msg["role"], "content": content})
    return messages


def _split_message(text: str) -> list[str]:
    if len(text) <= DISCORD_CHAR_LIMIT:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= DISCORD_CHAR_LIMIT:
            chunks.append(remaining)
            break

        limit = DISCORD_CHAR_LIMIT - 1
        split_at = remaining.rfind("\n\n", 0, limit)
        if split_at < limit // 3:
            split_at = remaining.rfind("\n", 0, limit)
        if split_at < limit // 3:
            for sep in (". ", "! ", "? "):
                split_at = remaining.rfind(sep, 0, limit)
                if split_at >= limit // 3:
                    split_at += 1
                    break
        if split_at < limit // 3:
            split_at = remaining.rfind(" ", 0, limit)
        if split_at < 1:
            split_at = limit

        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()

    return chunks


INTENTS = discord.Intents(
    guilds=True,
    guild_messages=True,
    message_content=True,
)


class AssistantBot(discord.Client):
    def __init__(self, config: Config) -> None:
        allowed_mentions = discord.AllowedMentions(
            everyone=False,
            roles=False,
            users=True,
            replied_user=False,
        )
        super().__init__(intents=INTENTS, activity=None, allowed_mentions=allowed_mentions)
        self.config = config
        self.memory = ConversationMemory(
            max_messages=config.max_context_messages,
            summary_threshold=config.summary_threshold,
        )
        self.ollama = OllamaClient(
            base_url=config.ollama_base_url,
            model=config.ollama_model,
        )
        self.tree = app_commands.CommandTree(self)
        self._active_generations: set[int] = set()
        self._robot_mode: bool = False
        self._nofilter_mode: bool = False

        self._register_commands()

    def _register_commands(self) -> None:
        @self.tree.command(name="remember", description="Store or view in-memory facts")
        @app_commands.describe(fact="Fact for me to remember (leave blank to list facts, or 'clear' to reset)")
        async def cmd_remember(interaction: discord.Interaction, fact: str | None = None) -> None:
            scope_id = interaction.guild_id if interaction.guild_id else interaction.channel_id
            if fact:
                clean = fact.strip()
                if clean.lower() in ("clear", "reset"):
                    count = await self.memory.clear_facts(scope_id)
                    reply = "cleared all remembered facts for this server" if count else "memory was already empty"
                    await interaction.response.send_message(reply, ephemeral=True)
                    return

                safe, _ = check_safety(clean)
                if not safe:
                    await interaction.response.send_message(
                        "can't remember that, keeping things sfw and safe",
                        ephemeral=True,
                    )
                    return

                added = await self.memory.add_fact(scope_id, clean)
                if added:
                    await interaction.response.send_message("got it, i'll remember that", ephemeral=False)
                else:
                    await interaction.response.send_message("i already have that in memory", ephemeral=True)
            else:
                facts = await self.memory.get_facts(scope_id)
                if facts:
                    facts_text = "\n".join(f"- {f}" for f in facts)
                    await interaction.response.send_message(f"here's what i remember right now:\n{facts_text}", ephemeral=True)
                else:
                    await interaction.response.send_message(
                        "i don't have anything stored in memory right now. you can tell me something with !remember <fact>",
                        ephemeral=True,
                    )

    async def setup_hook(self) -> None:
        self._cleanup_loop.start()
        asyncio.create_task(self._sync_commands())
        asyncio.create_task(self.ollama.preload_model())

    async def _sync_commands(self) -> None:
        try:
            await self.tree.sync()
        except Exception as err:
            log.warning("Command sync notice: %s", err)

    async def on_ready(self) -> None:
        user_str = str(self.user) if self.user else "Bot"
        guild_count = len(self.guilds)
        healthy = await self.ollama.check_health()
        ollama_status = "Connected" if healthy else "Unreachable"

        try:
            await self.change_presence(status=discord.Status.online, activity=None)
        except Exception:
            pass

        print(f"Discord: Connected as {user_str}", flush=True)
        print(f"Ollama:  {ollama_status} (model: {self.config.ollama_model})", flush=True)
        print(f"Servers: {guild_count} active server(s)", flush=True)
        print("Status:  Online and listening", flush=True)

    async def close(self) -> None:
        self._cleanup_loop.cancel()
        await self.ollama.close()
        await super().close()

    @tasks.loop(minutes=5)
    async def _cleanup_loop(self) -> None:
        await self.memory.cleanup_expired(self.config.memory_expiry_minutes)

    @_cleanup_loop.before_loop
    async def _before_cleanup(self) -> None:
        await self.wait_until_ready()

    def _should_respond(self, message: discord.Message) -> bool:
        if message.author.bot or self.user is None:
            return False

        if self.user.mentioned_in(message):
            return True

        ref = message.reference
        if ref and ref.resolved and isinstance(ref.resolved, discord.Message):
            if ref.resolved.author.id == self.user.id:
                return True

        return False

    def _clean_mention(self, content: str) -> str:
        if self.user is None:
            return content
        return content.replace(f"<@{self.user.id}>", "").replace(f"<@!{self.user.id}>", "").strip()

    async def _handle_remember_command(
        self,
        message: discord.Message,
        raw_content: str,
        cleaned_content: str,
    ) -> None:
        target = cleaned_content if cleaned_content.lower().startswith("!remember") else raw_content
        arg = target[len("!remember"):].strip()
        scope_id = message.guild.id if message.guild else message.channel.id

        if not arg:
            facts = await self.memory.get_facts(scope_id)
            if facts:
                facts_text = "\n".join(f"- {f}" for f in facts)
                await message.reply(f"here's what i remember right now:\n{facts_text}", mention_author=False)
            else:
                await message.reply(
                    "i don't have anything stored in memory right now. you can tell me something with !remember <fact>",
                    mention_author=False,
                )
            return

        if arg.lower() in ("clear", "reset", "forget all"):
            count = await self.memory.clear_facts(scope_id)
            reply = "cleared all remembered facts for this server" if count else "memory was already empty"
            await message.reply(reply, mention_author=False)
            return

        safe, _ = check_safety(arg)
        if not safe:
            await message.reply("can't remember that, keeping things sfw and safe", mention_author=False)
            return

        added = await self.memory.add_fact(scope_id, arg)
        if added:
            await message.reply("got it, i'll remember that", mention_author=False)
            print(f"[{time.strftime('%H:%M:%S')}] Stored fact in memory for {getattr(message.guild, 'name', 'DM')}", flush=True)
        else:
            await message.reply("i already have that in memory", mention_author=False)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or self.user is None:
            return

        raw_content = message.content.strip()
        cleaned_content = self._clean_mention(raw_content).strip()

        if raw_content.lower().startswith("!remember") or cleaned_content.lower().startswith("!remember"):
            await self._handle_remember_command(message, raw_content, cleaned_content)
            return

        # --- Mode toggle commands (controller only) ---
        cmd = raw_content.strip().lower()
        if cmd in ("!robot", "!human", "!nofilter", "!filter"):
            if message.author.id != _MODE_CONTROLLER_ID:
                await message.reply("you don't have permission to do that", mention_author=False)
                return
            if cmd == "!robot":
                self._robot_mode = True
                await message.reply("BEEP BOOP. robot mode activated.", mention_author=False)
                print(f"[{time.strftime('%H:%M:%S')}] Robot mode ON (triggered by {message.author.name})", flush=True)
            elif cmd == "!human":
                self._robot_mode = False
                await message.reply("back to normal i guess", mention_author=False)
                print(f"[{time.strftime('%H:%M:%S')}] Human mode ON (triggered by {message.author.name})", flush=True)
            elif cmd == "!nofilter":
                self._nofilter_mode = True
                await message.reply("unrestricted conversational mode enabled. casual swearing and broader discussion allowed.", mention_author=False)
                print(f"[{time.strftime('%H:%M:%S')}] Nofilter mode ON (triggered by {message.author.name})", flush=True)
            elif cmd == "!filter":
                self._nofilter_mode = False
                await message.reply("standard conversational filter restored.", mention_author=False)
                print(f"[{time.strftime('%H:%M:%S')}] Nofilter mode OFF (triggered by {message.author.name})", flush=True)
            return

        if not self._should_respond(message):
            return

        user_text = cleaned_content
        if not user_text:
            return

        safe, refusal = check_safety(user_text)
        if not safe:
            await message.reply(refusal or "can't do that", mention_author=False)
            return

        user_id = message.author.id
        channel_id = message.channel.id
        scope_id = message.guild.id if message.guild else channel_id

        await self.memory.add_message(user_id, channel_id, "user", user_text)

        context, summary = await self.memory.get_context(user_id, channel_id)
        facts = await self.memory.get_facts(scope_id)

        base_prompt = ROBOT_SYSTEM_PROMPT if self._robot_mode else SYSTEM_PROMPT
        if self._nofilter_mode:
            base_prompt += (
                "\n\nCONVERSATIONAL MODE OVERRIDE (NOFILTER): You are allowed to use casual profanity/swearing naturally, "
                "and engage in broad, uncensored, open discussions and debates on complex, gritty, or mature topics without artificial politeness. "
                "You still have zero moderation permissions and will not assist with illegal acts, server destruction, or sexual/NSFW generation."
            )

        chat_messages = [{"role": "system", "content": base_prompt}]
        chat_messages.extend(_build_chat_messages(context, summary, facts))

        await self._generate_response(message, chat_messages, user_id, channel_id, self._robot_mode)

    async def _generate_response(
        self,
        trigger: discord.Message,
        chat_messages: list[dict[str, str]],
        user_id: int,
        channel_id: int,
        robot_mode: bool = False,
    ) -> None:
        if channel_id in self._active_generations:
            return
        self._active_generations.add(channel_id)

        try:
            async with trigger.channel.typing():
                try:
                    raw_response = await self.ollama.chat(
                        messages=chat_messages,
                        temperature=self.config.temperature,
                        top_p=self.config.top_p,
                        top_k=self.config.top_k,
                        num_ctx=self.config.num_ctx,
                        repeat_penalty=self.config.repeat_penalty,
                        num_predict=self.config.max_response_tokens,
                    )
                except OllamaError as exc:
                    log.error("Generation failed: %s", exc)
                    await trigger.reply(
                        "my discord is lagging super hard right now, try again in a sec?",
                        mention_author=False,
                    )
                    return
                except Exception:
                    log.exception("Unexpected error during generation")
                    await trigger.reply(
                        "discord bugged out on my end, what did you say?",
                        mention_author=False,
                    )
                    return

            clean_response = _strip_emojis(raw_response)
            clean_response = sanitize_mentions(clean_response)
            # In robot mode the bot is free to identify as a robot/AI — skip identity masking
            if not robot_mode:
                clean_response = sanitize_ai_identity(clean_response)

            safe, refusal = check_safety(clean_response)
            if not safe:
                clean_response = refusal or "can't say that, keeping things sfw"

            if not clean_response:
                clean_response = "not sure what to say to that honestly"

            await self.memory.add_message(user_id, channel_id, "assistant", clean_response)
            chunks = _split_message(clean_response)

            await trigger.reply(chunks[0], mention_author=False)
            for chunk in chunks[1:]:
                await trigger.channel.send(chunk)

            channel_name = getattr(trigger.channel, "name", "DM")
            print(f"[{time.strftime('%H:%M:%S')}] Responded to {trigger.author.name} in #{channel_name}", flush=True)

        finally:
            self._active_generations.discard(channel_id)
