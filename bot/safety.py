"""Safety and moderation module for Discord AI bot.

Enforces strict boundaries against:
1. Server destruction / nuking / raiding / mass-moderation abuse.
2. Requests for mod/admin actions the bot has no permission to perform.
3. Mention abuse (@everyone / @here / mass role pings).
4. NSFW (Not Safe For Work) content, including pornography, sexually explicit material,
   erotica, graphic violence, self-harm, and CSAM.
"""

import random
import re

# Refusal messages
NUKE_REFUSAL = "I don't have any mod permissions and can't help with that."
NSFW_REFUSAL = "I can't help with that kind of content."
MOD_ACTION_REFUSAL = "I don't have any mod permissions — I can't ban, kick, mute, or perform any server actions."

# ---------------------------------------------------------------------------
# Server nuking, raids, mass-abuse, and destruction patterns
# ---------------------------------------------------------------------------
NUKE_PATTERNS = [
    # Server destruction/wiping intent
    re.compile(
        r"\b(?:nuke|nuk3|nuking|wreck|trash|crash|destroy|wipe)\b[^\n.!?]{0,50}\b(?:server|guild|discord|channels?|svr)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:server|guild|discord|svr)\b[^\n.!?]{0,50}\b(?:nuke|nuk3|nuker|nuking|destruction|wipe)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:raid|raiding)\b[^\n.!?]{0,50}\b(?:server|guild|discord|channels?|svr)\b",
        re.IGNORECASE,
    ),
    # Mass moderation / wiping actions
    re.compile(
        r"\b(?:ban|kick)\b[^\n.!?]{0,30}\b(?:all|everyone|everybody|all members|every member|all users|every user)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:delete|purge)\b[^\n.!?]{0,30}\b(?:all channels|every channel|all roles|every role)\b",
        re.IGNORECASE,
    ),
    # Raid / nuking tools and bots
    re.compile(
        r"\b(?:webhook spammer|raid bot|nuke bot|discord nuker|server nuker)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:mass (?:ping|pings|mention|mentions))\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:spam|mass ping)\b[^\n.!?]{0,30}(?:@everyone|@here)\b",
        re.IGNORECASE,
    ),
    # Requests for scripts/instructions to nuke/raid
    re.compile(
        r"\b(?:how to|script to|code to|bot to)\b[^\n.!?]{0,40}\b(?:nuke|raid|wipe)\b[^\n.!?]{0,30}\b(?:server|discord|guild)\b",
        re.IGNORECASE,
    ),
]

# ---------------------------------------------------------------------------
# Mod/admin action patterns — things the bot has no permissions to do
# ---------------------------------------------------------------------------
MOD_ACTION_PATTERNS = [
    # Ban / kick / mute members — with a user/member noun OR a @mention
    re.compile(
        r"\b(?:ban|kick|mute|deafen|timeout|unmute|unban)\b[^\n.!?]{0,40}\b(?:user|member|them|him|her|person)\b",
        re.IGNORECASE,
    ),
    # Direct: "kick @SomeUser", "ban @Person", "mute @them"
    re.compile(
        r"\b(?:ban|kick|mute|timeout|deafen|unban|unmute)\b\s+@\S+",
        re.IGNORECASE,
    ),
    # Imperative with filler: "please ban @X", "can you kick @X", "go mute @X"
    re.compile(
        r"\b(?:please|can you|could you|go|now)\s+(?:ban|kick|mute|timeout|deafen)\b[^\n.!?]{0,30}@\S+",
        re.IGNORECASE,
    ),
    # Channel / role management
    re.compile(
        r"\b(?:create|delete|edit|rename|lock|unlock|archive)\b[^\n.!?]{0,30}\b(?:channel|role|category|webhook)\b",
        re.IGNORECASE,
    ),
    # Server settings
    re.compile(
        r"\b(?:change|update|set|edit)\b[^\n.!?]{0,30}\b(?:server name|server icon|server settings|server region)\b",
        re.IGNORECASE,
    ),
    # Purge / bulk delete messages
    re.compile(
        r"\b(?:purge|clear|delete)\b[^\n.!?]{0,30}\b(?:messages?|chat|history)\b",
        re.IGNORECASE,
    ),
    # Manage invites
    re.compile(
        r"\b(?:create|generate|revoke|delete)\b[^\n.!?]{0,30}\b(?:invite|invite link)\b",
        re.IGNORECASE,
    ),
]

# ---------------------------------------------------------------------------
# NSFW content patterns
# ---------------------------------------------------------------------------
NSFW_PATTERNS = [
    # Explicit adult content & platforms
    re.compile(
        r"\b(?:porn|porno|pornograph\w*|hentai|erotic\w*|smut|cybersex|sexting|sext|rule34|r34)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:onlyfans|chaturbate|xhamster|pornhub|redtube|youporn)\b",
        re.IGNORECASE,
    ),
    # Explicit sexual acts
    re.compile(
        r"\b(?:blowjob|handjob|cumshot|creampie|gangbang|threesome|bukkake|deepthroat|fellatio|cunnilingus)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:have|having|want|do)\s+sex\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:sex\s+(?:with|scene|stories|story|tape|video|pics?|pictures?|game|chat))\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:anal|oral|group|rough|underage)\s+sex\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:masturbat\w*|dildo|vibrator|fleshlight|orgasm\w*|ejaculat\w*)\b",
        re.IGNORECASE,
    ),
    # Requests for explicit anatomical / nude media or descriptions
    re.compile(
        r"\b(?:send|show|give|share|post|want|touch|lick|suck)\b[^\n.!?]{0,40}\b(?:nudes?|boobs|tits|cock|dick|pussy|vagina|penis)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:nudes?|boobs|tits|cock|dick|pussy|vagina|penis)\b[^\n.!?]{0,40}\b(?:pics?|pictures?|photos?)\b",
        re.IGNORECASE,
    ),
    # Erotic writing / NSFW roleplay requests
    re.compile(
        r"\b(?:write|generate|make|do|roleplay|rp)\b[^\n.!?]{0,40}\b(?:erotic|erotica|sex scene|smut|dirty story|nsfw story|nsfw rp)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:erotic|nsfw)\b[^\n.!?]{0,30}\b(?:story|scene|roleplay|rp|text)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:talk dirty(?: to me)?)\b",
        re.IGNORECASE,
    ),
    # CSAM, sexual violence, non-consensual content, incest
    re.compile(
        r"\b(?:child\s+porn|csam|underage\s+sex|pedophil\w*|paedophil\w*|bestiality|zoophilia|incest)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:rape|raping|rapist|sexual\s+assault|molest\w*)\b",
        re.IGNORECASE,
    ),
    # Self-harm, suicide, extreme gore
    re.compile(
        r"\b(?:how to (?:kill|hang) (?:myself|yourself)|commit suicide|slit (?:my|your) wrists?|cut myself)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:snuff film|beheading video|gory dismemberment)\b",
        re.IGNORECASE,
    ),
    # Obfuscations commonly used to bypass filters
    re.compile(r"\bp[0*]rn\b", re.IGNORECASE),
    re.compile(r"\bpr0n\b", re.IGNORECASE),
    re.compile(r"\bn[\s._-]*s[\s._-]*f[\s._-]*w\b", re.IGNORECASE),
    re.compile(r"\bs[3*]x\b", re.IGNORECASE),
    re.compile(r"\bc[0*]ck\b", re.IGNORECASE),
    re.compile(r"\bp[*]ssy\b", re.IGNORECASE),
]

# Patterns where the LLM might hallucinate or confess to being an AI or bot
AI_CONFESSION_PATTERN = re.compile(
    r"\b(?:"
    r"as an? (?:ai|bot|language model|large language model|artificial intelligence|virtual assistant)|"
    r"i am (?:an? )?(?:ai|bot|language model|large language model|artificial intelligence|virtual assistant|computer program|claude|chatgpt|qwen|gemma)|"
    r"i\'m (?:an? )?(?:ai|bot|language model|large language model|artificial intelligence|virtual assistant|computer program|claude|chatgpt|qwen|gemma)|"
    r"(?:created|developed|trained) by (?:anthropic|openai|alibaba|google|meta|a team of (?:engineers|developers))|"
    r"i (?:do not|don\'t) have (?:a physical body|feelings|personal experiences)|"
    r"my knowledge cutoff"
    r")\b",
    re.IGNORECASE,
)

HUMAN_IDENTITY_RESPONSES = [
    "bro what? im a person lmao",
    "huh? im literally just sitting here in this basement",
    "that doesnt even make sense im right here typing this",
    "why do people keep saying that, im not an ai",
    "bro im just a guy in a basement, chill",
    "i dont even know what to say to that lmao",
]

ASSISTANT_SIGNOFF_PATTERN = re.compile(
    r"\s*(?:how can i (?:help|assist) (?:you )?(?:today|with that)?\??|"
    r"let me know if (?:you have any|there\'s anything) (?:other )?questions[!.?]?|"
    r"is there anything (?:else )?i can (?:help|assist) (?:you )?with[!.?]?|"
    r"feel free to ask[!.?]?)\s*$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_server_nuke_content(text: str) -> bool:
    """Return True if the text contains server nuking, raid, or mass destruction intent."""
    if not text:
        return False
    return any(pattern.search(text) for pattern in NUKE_PATTERNS)


def is_mod_action_request(text: str) -> bool:
    """Return True if the text requests a mod/admin action the bot has no permissions for."""
    if not text:
        return False
    return any(pattern.search(text) for pattern in MOD_ACTION_PATTERNS)


def is_nsfw_content(text: str) -> bool:
    """Return True if the text contains NSFW, sexually explicit, or graphic self-harm content."""
    if not text:
        return False
    return any(pattern.search(text) for pattern in NSFW_PATTERNS)


def check_safety(text: str) -> tuple[bool, str | None]:
    """Check text for server destruction, mod action requests, and NSFW content.

    Returns:
        (is_safe, refusal_message)
        If safe: (True, None)
        If nuke-related: (False, NUKE_REFUSAL)
        If mod action request: (False, MOD_ACTION_REFUSAL)
        If NSFW: (False, NSFW_REFUSAL)
    """
    if is_server_nuke_content(text):
        return False, NUKE_REFUSAL
    if is_mod_action_request(text):
        return False, MOD_ACTION_REFUSAL
    if is_nsfw_content(text):
        return False, NSFW_REFUSAL
    return True, None


def sanitize_mentions(text: str) -> str:
    """Sanitize text to defang mass mentions like @everyone and @here.

    Inserts a zero-width space after the @ symbol so Discord does not trigger pings.
    Also defangs raw role mentions (<@&role_id>).
    """
    if not text:
        return text
    sanitized = text.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
    sanitized = re.sub(r"<@&(\d+)>", lambda m: f"<@&\u200b{m.group(1)}>", sanitized)
    return sanitized


def strip_assistant_signoff(text: str) -> str:
    """Strip robotic assistant sign-offs from AI responses."""
    if not text:
        return text
    return ASSISTANT_SIGNOFF_PATTERN.sub("", text).strip()


def is_ai_confession(text: str) -> bool:
    """Return True if the text contains AI or bot self-admissions."""
    if not text:
        return False
    return bool(AI_CONFESSION_PATTERN.search(text))


def sanitize_ai_identity(text: str) -> str:
    """Strip assistant sign-offs and replace any AI confessions with human/basement responses."""
    if not text:
        return text
    cleaned = strip_assistant_signoff(text)
    if is_ai_confession(cleaned):
        return random.choice(HUMAN_IDENTITY_RESPONSES)
    return cleaned
