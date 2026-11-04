import logging
import sys

from bot.bot import AssistantBot
from bot.config import Config


def setup_logging(level: str) -> None:
    log_level = getattr(logging, level.upper(), logging.WARNING)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.ERROR)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def main() -> None:
    config = Config()
    try:
        config.validate()
    except ValueError as err:
        print(f"Config error: {err}", file=sys.stderr, flush=True)
        sys.exit(1)

    setup_logging(config.log_level)
    print(f"Connecting to Discord (model: {config.ollama_model})...", flush=True)

    bot = AssistantBot(config)
    bot.run(config.discord_token, log_handler=None)


if __name__ == "__main__":
    main()
