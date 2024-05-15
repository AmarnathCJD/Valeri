from modules._config import TOKEN, bot
from modules._helpers import load_modules

# from sticker import task

bot.start(bot_token=TOKEN)

load_modules()
# bot.loop.run_until_complete(task())
# asyncio.ensure_future(file_server())

bot.run_until_disconnected()
