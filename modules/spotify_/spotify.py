import requests

from .bin import playplay_pb2
from utils import rebuild_ogg, _get_track_id, beautify_out, get_track_url
from const import refresh_token

import subprocess
import os
import tempfile
import logging

import time

from dotenv import load_dotenv

from Crypto.Cipher import AES
from Crypto.Util import Counter

log = logging.getLogger('spotify')
load_dotenv()

class Spotify:
    access_token: str
    download_folder: str

    def __init__(self, access_token: str = '', download_folder: str = ''):
        self.access_token = access_token
        
        if self.access_token == '':
            self.get_token()
        self.download_folder = download_folder
        
    def get_token(self):
        sp_c = os.getenv('SPOTIFY_DC')
        self.access_token = refresh_token(sp_c=sp_c)

    def download(self, track_id: str, output_path: str = ''):
        _dl_req = download_song(track_id, output_path, self.access_token, self.download_folder)
        if _dl_req == 401:
            self.get_token()
            _dl_req = download_song(track_id, output_path, self.access_token, self.download_folder)
            
        return _dl_req
    
    def download_by_file_id(self, file_id: str, track_id: str):
        if len(track_id) == 22:
            track_id = _get_track_id(track_id)
        elif 'spotify:track:' in track_id:
            track_id = _get_track_id(track_id.replace('spotify:track:', ''))
        track = get_track(track_id, self.access_token)
        downloaded_file = _download_song(file_id, self.access_token)
    
        log.info(f"rebuilding - ogg_vorbis_320 header")
        rebuild_ogg(downloaded_file)
        
        output_path = f'{track["name"]}.mp3'
        output_path = beautify_out(output_path)
        if not output_path.endswith('.mp3'):
            output_path += '.mp3'
        
        out = add_metadata(downloaded_file, output_path, track)
    
        # os.remove(downloaded_file)
        # os.remove(downloaded_file.replace('.ogg', ''))
    
        if not os.path.exists(out):
            print('Error: failed to download (probably due to DRM)')
            return None
    
        log.info(f"downloaded - {output_path}")    
        return out
    
    def extract_info(self, track_id: str):
        if len(track_id) == 22:
            track_id = _get_track_id(track_id)
        elif 'spotify:track:' in track_id:
            track_id = _get_track_id(track_id.replace('spotify:track:', ''))
        track = get_track(track_id, self.access_token)
        
        return_data = {
            'name': track['name'],
            'artists': ', '.join([artist['name'] for artist in track['artist']]),
            'album': track['album']['name'],
            'release_date': track['album']['date']['year'],
            'cover': 'https://i.scdn.co/image/' + track['album']['cover_group']['image'][0]['file_id']
        }
        
        return_data["file"] = track['file']
        
        return return_data

def download_song(track_id: str, output_path: str = '', access_token: str = '', download_folder: str = ''):
    if len(track_id) == 22:
        track_id = _get_track_id(track_id)
    elif 'spotify:track:' in track_id:
        track_id = _get_track_id(track_id.replace(
            'spotify:track:', ''))
    track = get_track(track_id, access_token)
    
    if track == 401:
        return 401
    
    log.info(f"downloading - {track['name']} by {', '.join([artist['name'] for artist in track['artist']])}")
    file_id = track['file'][0]['file_id'] if len(track) > 1 else ''
    
    if not file_id:
        print('Error: No file_id found.')
        return None
    
    downloaded_file = _download_song(file_id, access_token)
    
    log.info(f"rebuilding - ogg_vorbis_320 header")
    rebuild_ogg(downloaded_file)
    if not output_path:
        output_path = f'{track["name"]}.mp3'
        output_path = beautify_out(output_path)
        if not output_path.endswith('.mp3'):
            output_path += '.mp3'
    
    if download_folder:
        if not os.path.exists(download_folder):
            os.makedirs(download_folder, exist_ok=True)
        output_path = os.path.join(download_folder, output_path)
        
    out = add_metadata(downloaded_file, output_path, track)
    
    # os.remove(downloaded_file)
    # os.remove(downloaded_file.replace('.ogg', ''))
    
    if not os.path.exists(out):
        print('Error: failed to download (probably due to DRM)')
        return None
    
    log.info(f"downloaded - {output_path}")    
    return out


def _download_song(file_id, access_token):
    req = playplay_pb2.PlayPlayLicenseRequest(
        version=2,
        token=bytes.fromhex("01e132cae527bd21620e822f58514932"),
        interactivity=playplay_pb2.Interactivity.INTERACTIVE,
        content_type=playplay_pb2.AUDIO_TRACK
    )

    r = requests.post(
        url=f"https://gew4-spclient.spotify.com/playplay/v1/key/{file_id}",
        headers={
            "Authorization": "Bearer {}".format(access_token),
        },
        data=req.SerializeToString()
    )

    resp = playplay_pb2.PlayPlayLicenseResponse()
    resp.ParseFromString(r.content)

    output = subprocess.check_output([
        './modules/spotify_/bin/playplay',
        file_id,
        resp.obfuscated_key.hex()
    ])
    
    key = bytes.fromhex(output.strip().decode('utf-8'))

    cipher = AES.new(
        key=key,
        mode=AES.MODE_CTR,
        counter=Counter.new(
            128,
            initial_value=int.from_bytes(b'r\xe0g\xfb\xdd\xcb\xcfw\xeb\xe8\xbcd?c\r\x93', "big")
        )
    )

    url = get_audio_urls(file_id, access_token)

    with requests.get(url[0], stream=True) as r:
        with open(f"{file_id}", "wb") as f:
            for chunk in r.iter_content(chunk_size=8092):
                if chunk:
                    f.write(chunk)

    decrypted_buffer = cipher.decrypt(open(file_id, 'rb').read())

    with open(f"{file_id}.ogg", "wb") as f:
        f.write(decrypted_buffer)
        
    return f"{file_id}.ogg"


def add_metadata(input_path, output_path, track):
    temp_song = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    temp_song.close()

    temp_cover = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')

    log.info(f"downloading - cover Art (id3v2)")
    cover_file = 'https://i.scdn.co/image/' + \
        track['album']['cover_group']['image'][0]['file_id']
    req = requests.get(cover_file, stream=True)
    for chunk in req.iter_content(chunk_size=1024):
        temp_cover.write(chunk)
    temp_cover.close()

    log.info(f"ffmpeg - adding metadata")
    subprocess.run([
        "ffmpeg", "-i", input_path, "-c:a", "libmp3lame", "-q:a", "0", "-b:a", "320k", "-loglevel", "quiet",
        "-metadata", f"title={track['name']}",
        "-metadata", f"artist={' & '.join([artist['name'] for artist in track['artist']])}",
        "-metadata", f"album={track['album']['name']}",
        "-metadata", f"release_date={track['album']['date']['year']}",
        "-metadata", f"lyrics='I'm a description'",
        "-loglevel", "quiet",
        "-y", temp_song.name
    ], stdout=None, stderr=None)

    subprocess.run([
        "ffmpeg", "-i", temp_song.name, "-i", temp_cover.name, "-map", "0:0", "-map", "1:0", "-c", "copy", "-id3v2_version", "3", "-metadata:s:v", "title='Album cover'", "-metadata:s:v",
        "comment='Cover (front)'", output_path, "-loglevel", "quiet",
        "-y"], stdout=None, stderr=None)

    os.remove(temp_song.name)
    os.remove(temp_cover.name)

    return output_path

def get_track(track_id, access_token):
    url = get_track_url(track_id)
    headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en',
        'Authorization': f'Bearer {access_token}',
        'Connection': 'keep-alive',
        'Host': 'spclient.wg.spotify.com',
        'Origin': 'https://open.spotify.com',
        'Prefer': 'safe',
        'Referer': 'https://open.spotify.com/',
        'Sec-GPC': '1',
        'TE': 'Trailers',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    }
    request = requests.get(url, headers=headers)
    if request.status_code == 401:
        return 401
    json = request.json()

    return json


def get_audio_urls(file_id, access_token):
    url = f'https://gew1-spclient.spotify.com/storage-resolve/v2/files/audio/interactive/11/{file_id}'
    params = {
        'version': 10000000,
        'product': 9,
        'platform': 39,
        'alt': 'json'
    }
    headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en',
        'Authorization': f'Bearer {access_token}',
        'Connection': 'keep-alive',
        'Host': 'gew1-spclient.spotify.com',
        'Origin': 'https://open.spotify.com',
        'Prefer': 'safe',
        'Referer': 'https://open.spotify.com/',
        'Sec-GPC': '1',
        'TE': 'Trailers',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    }
    request = requests.get(url, params=params, headers=headers)
    request.raise_for_status()
    json = request.json()
    
    if 'cdnurl' not in json:
        return 401

    return json['cdnurl']
