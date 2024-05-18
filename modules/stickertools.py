import asyncio
import os
from os import remove, rename

from requests import get, post
from telethon import types as t
from telethon.tl.functions import stickers
from telethon.tl.functions.messages import (
    GetCustomEmojiDocumentsRequest,
    GetStickerSetRequest,
)
from telethon.tl.functions.messages import UploadMediaRequest
from telethon.tl.functions.stickers import (
    AddStickerToSetRequest,
    CreateStickerSetRequest,
)

from telethon.errors import ShortNameOccupiedError

from ._config import bot
from ._handler import new_cmd


async def run_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    o, e = await proc.communicate()
    return str(o), str(e)


def color_image(path):
    with open(path, "rb") as file:
        r = post(
            "https://api.deepai.org/api/colorizer",
            files={"image": file},
            headers={"api-key": "8f9015f2-8358-420d-a294-1da9c488f67e"},
        )
        with open("color-" + path, "wb") as file:
            data = r.json()
            try:
                url = data["output_url"]
            except KeyError:
                return "", str(data)
            file.write(get(url).content)
    return "color-" + path, ""


def edit_image(path, arg):
    with open(path, "rb") as file:
        r = post(
            "https://api.deepai.org/api/image-editor",
            files={"image": file},
            data={"text": arg},
            headers={"api-key": "8f9015f2-8358-420d-a294-1da9c488f67e"},
        )
        with open("edit-" + path, "wb") as file:
            data = r.json()
            try:
                url = data["output_url"]
            except KeyError:
                return "", str(data)
            file.write(get(url).content)
    return "edit-" + path, ""


def similarize_image(image):
    from PIL import Image

    image1 = Image.open(image)
    image2 = Image.open("color-" + image)
    image2 = image2.resize((image1.size[0], image1.size[1]))
    image2.save("color-" + image)


FFMPEG_COMMAND = 'ffmpeg -loop 1 -framerate 30 -t 0.16 -i {}  -loop 1 -framerate 30 -t 0.16 -i {} -loop 1 -framerate 30 -t 0.16 -i {} -loop 1 -framerate 30 -t 0.16 -i {} -filter_complex "[0][1][2][3]concat=n=4:v=1:a=0[v1],[v1]loop=20:32767:0" {}'


@new_cmd(pattern="animate")
async def _animate(msg):
    if not msg.reply_to:
        return await msg.reply("Reply to sticker/photo to animate it")
    r = await msg.get_reply_message()
    mg = await msg.reply("`Processing..`")
    if not any([r.photo, r.sticker]):
        return await msg.reply("nil")
    f = await r.download_media()
    color_f, err = color_image(f)
    if err != "":
        return await mg.edit(str(err))
    similarize_image(f)
    await run_cmd(
        FFMPEG_COMMAND.format(f, color_f, f, color_f,
                              "{}-anim.mp4".format(msg.id))
    )
    await msg.respond(file="{}-anim.mp4".format(msg.id))
    await mg.delete()


@new_cmd(pattern="color")
async def _animate(msg):
    if not msg.reply_to:
        return await msg.reply("Reply to sticker/photo to color it")
    r = await msg.get_reply_message()
    mg = await msg.reply("`Processing..`")
    if not any([r.photo, r.sticker]):
        return await msg.reply("nil")
    f = await r.download_media()
    color_f, err = color_image(f)
    if err != "":
        return await mg.edit(str(err))
    await msg.respond(file=color_f)
    await mg.delete()
    os.remove(f)
    os.remove("color-" + f)


@new_cmd(pattern="edit")
async def _animate(msg):
    if not msg.reply_to:
        return await msg.reply("Reply to sticker/photo to edit it")
    r = await msg.get_reply_message()
    mg = await msg.reply("`Processing..`")
    if not any([r.photo, r.sticker]):
        return await msg.reply("no media found")
    f = await r.download_media()
    try:
        a = msg.text.split(None, 1)[1]
    except IndexError:
        a = "enhance image"
    color_f, err = edit_image(f, a)
    if err != "":
        return await mg.edit(str(err))
    await msg.respond(file=color_f)
    await mg.delete()
    os.remove(f)
    os.remove("edit-" + f)


@new_cmd(pattern="(stoi|itos)")
async def _stoi(message):
    if not message.reply_to:
        return await message.reply("Reply to a media to convert it to sticker.")
    r = await message.get_reply_message()
    if not r.media:
        return await message.reply("Reply to a media to convert it to sticker.")
    if not any([r.photo, r.sticker]):
        return await message.reply("Reply to a media to convert it to sticker.")
    media = await r.download_media()
    if "stoi" in message.text:
        rename(media, media + ".png")
        media += ".png"
    else:
        rename(media, media + ".webp")
        media += ".webp"
    await message.respond(file=media)
    remove(media)
    remove(media.replace("." + media.split(".")[-1], ""))


async def get_shortname(title: str):
    r = await bot(stickers.SuggestShortNameRequest(title))
    return r.short_name


@new_cmd(pattern="kang")
async def _kang(message):
    await message.reply("Kang is not implemented yet.")


@new_cmd(pattern="ke")
async def q_s(e):
    try:
        emoji_pack = e.text.split(None, 1)[1]
    except IndexError:
        return await e.reply("Give me the emoji pack name")
    if "t.me" in emoji_pack:
        emoji_pack = emoji_pack.split("/")[-1]
    shortname = emoji_pack + "{}e_to_m_by_missvaleri_bot".format(e.sender.id)
    s = await bot(GetStickerSetRequest(t.InputStickerSetShortName(emoji_pack), 0))
    _i = 0
    msg = await e.reply("Kanging emojis...")
    try:
        for i in s.packs:
            doc = await bot(GetCustomEmojiDocumentsRequest(i.documents))
            _i += 1
            _j = 0
            for j in doc:
                if j.mime_type == "image/webp":
                    j = await resize_and_upload(j, 512, 512)
                
                doc_inp = t.InputDocument(
                    id=j.id, access_hash=j.access_hash, file_reference=j.file_reference
                )
                if _i == 1 and _j == 0:
                    s = await bot(
                        CreateStickerSetRequest(
                            user_id=e.sender,
                            title=e.sender.first_name + " CustomWebm",
                            short_name=shortname,
                            stickers=[
                                t.InputStickerSetItem(
                                    document=doc_inp,
                                    emoji="🤍",
                                )
                            ],
                            videos=j.mime_type == "video/webm",
                            text_color=True,
                            software="MissValeri_ENCODER",
                        )
                    )
                    _j += 1
                    continue

                s = await bot(
                    AddStickerToSetRequest(
                        stickerset=t.InputStickerSetShortName(shortname),
                        sticker=t.InputStickerSetItem(
                            document=doc_inp,
                            emoji="🤍",
                        ),
                    )
                )
    except ShortNameOccupiedError:
        return await msg.edit(
            "Already kanged: [{}]({})".format("PACK", f"https://t.me/addstickers/{shortname}")
        )
    except Exception as e:
        return await msg.edit(str(e))

    await msg.edit(
        f"Stickers added to [{shortname}](https://t.me/addstickers/{shortname})"
    )
    
from PIL import Image as PIL
import os

async def resize_and_upload(file, W, H):    
    file_dl = await bot.download_media(file)
    im = PIL.open(file_dl)
    im = im.resize((W, H))
    
    im.save(file_dl.replace(".webp", "_resized.webp"), "WEBP")
    
    file = await bot.upload_file(file_dl.replace(".webp", "_resized.webp"))
    
    file_media = await bot(
        UploadMediaRequest(
            media=t.InputMediaUploadedDocument(
                file=file,
                mime_type="image/webp",
                attributes=[t.DocumentAttributeFilename("sticker.webp")]
            ),
            peer=t.InputPeerSelf()
        )
    )
    
    os.remove(file_dl)
    os.remove(file_dl.replace(".webp", "_resized.webp"))
    
    return file_media.document
    
    