import math
import binascii
import subprocess

OggS = b"OggS"
OggStart = b"\x00\x02"
Zeroes = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
VorbisStart = b"\x01\x1E\x01vorbis"
Channels = b"\x02"
SampleRate = b"\x44\xAC\x00\x00"
BitRate = b"\x00\xE2\x04\x00"
PacketSizes = b"\xB8\x01"

def rebuild_ogg(filename):
    with open(filename, "r+b") as ogg_file:
            ogg_file.write(OggS)
            ogg_file.seek(4)
            ogg_file.write(OggStart)
            ogg_file.seek(6)
            ogg_file.write(Zeroes)
            
            ogg_file.seek(72)
            buffer = ogg_file.read(4)
            ogg_file.seek(14)
            ogg_file.write(buffer)
            ogg_file.seek(18)
            ogg_file.write(Zeroes)
            ogg_file.seek(26)
            ogg_file.write(VorbisStart)

            ogg_file.seek(35)
            ogg_file.write(Zeroes)
            ogg_file.seek(39)
            ogg_file.write(Channels)
            ogg_file.seek(40)
            ogg_file.write(SampleRate)
            ogg_file.seek(48)
            ogg_file.write(BitRate)
    
            ogg_file.seek(56)
            ogg_file.write(PacketSizes)
            ogg_file.seek(58)
            ogg_file.write(OggS)
            ogg_file.seek(62)
            ogg_file.write(Zeroes)

class Base62:
    standard_base = 256
    target_base = 62
    alphabet: bytes
    lookup: bytearray

    def __init__(self, alphabet: bytes):
        self.alphabet = alphabet
        self.create_lookup_table()

    @staticmethod
    def create_instance_with_inverted_character_set():
        return Base62(Base62.CharacterSets.inverted)

    def decode(self, encoded: bytes, length: int = -1):
        prepared = self.translate(encoded, self.lookup)
        return self.convert(prepared, self.target_base, self.standard_base,
                            length)

    def translate(self, indices: bytes, dictionary: bytes):
        translation = bytearray(len(indices))
        for i in range(len(indices)):
            translation[i] = dictionary[int.from_bytes(indices[i].encode(),
                                                       "big")]
        return translation

    def convert(self, message: bytes, source_base: int, target_base: int,
                length: int):
        estimated_length = self.estimate_output_length(
            len(message), source_base, target_base) if length == -1 else length
        out = b""
        source = message
        while len(source) > 0:
            quotient = b""
            remainder = 0
            for b in source:
                accumulator = int(b & 0xff) + remainder * source_base
                digit = int(
                    (accumulator - (accumulator % target_base)) / target_base)
                remainder = int(accumulator % target_base)
                if len(quotient) > 0 or digit > 0:
                    quotient += bytes([digit])
            out += bytes([remainder])
            source = quotient
        if len(out) < estimated_length:
            size = len(out)
            for _ in range(estimated_length - size):
                out += bytes([0])
            return self.reverse(out)
        if len(out) > estimated_length:
            return self.reverse(out[:estimated_length])
        return self.reverse(out)

    def estimate_output_length(self, input_length: int, source_base: int,
                               target_base: int):
        return int(
            math.ceil((math.log(source_base) / math.log(target_base)) *
                      input_length))

    def reverse(self, arr: bytes):
        length = len(arr)
        reversed_arr = bytearray(length)
        for i in range(length):
            reversed_arr[length - i - 1] = arr[i]
        return bytes(reversed_arr)

    def create_lookup_table(self):
        self.lookup = bytearray(256)
        for i in range(len(self.alphabet)):
            self.lookup[self.alphabet[i]] = i & 0xff

    class CharacterSets:
        inverted = b'0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

def _get_track_id(track_id: str) -> str:
    return binascii.unhexlify(binascii.hexlify(
        Base62.create_instance_with_inverted_character_set().decode(track_id, 16)).lower()).hex()

def beautify_out(out: str):
    if len(out) > 40:
        return out[:20]
    return out

def get_track_url(track_id):
    return f'https://spclient.wg.spotify.com/metadata/4/track/{track_id}?market=from_token'


def find_quality(track, quality):
    for file in track['file']:
        if file['format'] == quality:
            return file
    return None

def is_ffmpeg_installed():
    return subprocess.call('ffmpeg -version', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0