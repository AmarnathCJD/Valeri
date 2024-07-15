import re
import logging
from spotify import Spotify
import subprocess

if subprocess.call('ffmpeg -version', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
    raise Exception('ffmpeg not installed')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

track_id = input('Enter the Spotify track ID: ')
if not track_id:
    track_id = "1n5gnI3Wue9WBpYFOIQNh1" # dummy track id

if re.match(r"https://open.spotify.com/track/([a-zA-Z0-9]+)", track_id):
    track_id = re.match(
        r"https://open.spotify.com/track/([a-zA-Z0-9]+)", track_id).group(1)

spot_dl = Spotify()

spot_dl.download(track_id)
