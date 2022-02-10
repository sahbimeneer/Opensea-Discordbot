import os

OPENSEA_API_KEY = os.environ.get("OPENSEA_API_KEY", "")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")

NOTIFIERS_FILE_NAME = "notifiers.josn"
BOT_SETTINGS_FILE_NAME = "bot.json"

NOT_ENOUGH_ARGUMENTS = 0