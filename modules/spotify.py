from .spotify_.spotify import Spotify
from ._handler import new_cmd
import re

@new_cmd(pattern='spotify')
async def spotify(e):
    s = Spotify()
    
    try:
        track_id = e.text.split(' ')[1]
    except IndexError:
        await e.reply('Please provide a track id')
        return
    
    if re.match(r"https://open.spotify.com/track/([a-zA-Z0-9]+)", track_id):
        track_id = re.match(
        r"https://open.spotify.com/track/([a-zA-Z0-9]+)", track_id).group(1)

    
    msg = await e.reply('Downloading...')
    out = s.download(track_id)
    
    if out:
        await e.reply(file=out)
        import os
        os.remove(out)
        
    else:
        return await msg.reply('Failed to download')
    await msg.delete()