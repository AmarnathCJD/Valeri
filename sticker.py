from telethon.tl.functions.messages import GetCustomEmojiDocumentsRequest as get_emojis
from telethon.tl.functions.messages import GetStickerSetRequest as get_sticker
from modules._config import bot
from telethon.tl.types import InputStickerSetShortName

PACK_ID = 'epicmix'
CHAT = 'rosexchat'

async def task():
    stickerset = await bot(get_sticker(InputStickerSetShortName(PACK_ID), 0))
    for sticker in stickerset.packs:
        doc = await bot(get_emojis(sticker.documents))
        
        dl = await bot.download_media(doc[0], 'stickers')
        break

def task_A():
    FILE_NAME = 'stickers.webm'
    
    # make a 512x512 transparent webm and save as transparent.webm
    import ffmpeg
    ffmpeg.input('stickers.webm').output('transparent.webm', vf='alphaextract').run(overwrite_output=True)
    
    # place FILE_NAME at centre of transparent.webm and save as stickers_e.webm
    
    ffmpeg.input('transparent.webm').output('stickers_e.webm', i=FILE_NAME, filter_complex='overlay=(W-w)/2:(H-h)/2').run(overwrite_output=True)
    
task_A()

# TEST