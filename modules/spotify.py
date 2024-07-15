from .spotify_.spotify import Spotify
from ._handler import new_cmd

@new_cmd(pattern='spotify')
async def spotify(e):
    s = Spotify()
    
    try:
        track_id = e.text.split(' ')[1]
    except IndexError:
        await e.reply('Please provide a track id')
        return
    
    await e.reply('Downloading...')
    out = s.download(track_id)
    
    if out:
        await e.reply(file=out)
        
    else:
        await e.reply('Failed to download')