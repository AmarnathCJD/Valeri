import asyncio

from modules._config import TOKEN, bot
from modules._helpers import load_modules
from modules.custdl import file_server

bot.start(bot_token=TOKEN)

load_modules()
asyncio.ensure_future(file_server())

bot.run_until_disconnected()
