import dotenv
import logging
import os
from pyhabot.pyhabot import Pyhabot


dotenv.load_dotenv()

logger = logging.getLogger("pyhabot_logger")

if os.getenv("INTEGRATION") == "discord":
    from pyhabot.integrations.discord import DiscordIntegration as Integration

    TOKEN = os.getenv("DISCORD_TOKEN")
elif os.getenv("INTEGRATION") == "telegram":
    from pyhabot.integrations.telegram import TelegramIntegration as Integration

    TOKEN = os.getenv("TELEGRAM_TOKEN")
elif os.getenv("INTEGRATION") == "terminal":
    from pyhabot.integrations.terminal import TerminalIntegration as Integration

    TOKEN = ""
else:
    raise ValueError("INTEGRATION environment variable must be set to 'discord', 'telegram' or 'terminal'")


if __name__ == "__main__":
    Pyhabot(Integration(TOKEN)).run()
