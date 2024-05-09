import os
import re
import sys
import time
from os import environ, execle, listdir, path, remove, system

import speedtest
import tinytag
from telethon import Button, events, types

from ._config import StartTime, bot
from ._handler import auth_only, master_only, new_cmd, newIn
from ._helpers import (
    generate_thumbnail,
    get_mention,
    get_text_content,
    get_user,
    get_video_metadata,
    human_readable_size,
    progress,
)
from ._transfers import download_file, upload_file
from .db.auth import add_auth, get_auth, is_auth, remove_auth

thumbs = []


@new_cmd(pattern="ping")
async def _ping_cmd(e):
    uptime = time.time() - StartTime

    ping_start = time.time()
    msg = await e.reply("Pong!")

    end_ping = time.time() - ping_start
    await msg.edit(f"**Pong!** `{end_ping * 1000:.3f}ms`\n**Uptime:** `{uptime:.2f}`")


@newIn(pattern="s (.*)")
async def _k_new_in(e):
    try:
        e.text.split(" ", 1)[1]
    except:
        return
    matches = (
        []
        # [stringw for stringw in list(DB.titles.find()) if re.search(str(q), str(stringw.get("name")), re.I)]
    )
    results = []
    for x in matches:
        results.append(
            await e.builder.document(
                title=x.get("name"),
                file="photo_2023-08-06_15-40-10.webp",
                text="**"
                + x.get("name", "")
                + "** \nPlease wait while Fetching File...",
            )
        )

    await e.answer(results)


def is_bl(code):
    if any([re.search(x, code.lower()) for x in ["net", "bat", "chmod"]]):
        return False
    return False


@new_cmd(pattern="ls")
@auth_only
async def _ls(e):
    try:
        directory = e.text.split(" ", 1)[1]
        directory = directory + "/" if not directory.endswith("/") else directory
    except IndexError:
        directory = "./"
    contents = listdir(directory)
    if len(contents) == 0:
        await e.reply("`No files found.`")
        return
    caption = "<b>Files in <code>{}</code>:</b>\n".format(directory)
    folder_count = 0
    file_count = 0
    for file in contents:
        size = path.getsize(directory + file)
        if path.isdir(directory + file):
            folder_count += 1
            caption += "📁 <code>{}</code> (<code>{}</code>)\n".format(
                file, human_readable_size(size)
            )
        else:
            file_count += 1
            if file.lower().endswith((".mp4", ".mkv", ".webm", ".3gp", ".mpeg")):
                emoji = "🎥"
            elif file.lower().endswith((".mp3", ".wav", ".flv", ".ogg", ".opus")):
                emoji = "🎵"
            elif file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                emoji = "🖼"
            elif file.lower().endswith(".gif"):
                emoji = "🎇"
            elif file.lower().endswith((".zip", ".rar", ".7z", ".tar", ".gzip")):
                emoji = "🗜"
            elif file.lower().endswith(
                (".json", ".xml", ".txt", ".text", ".csv", ".pptx", ".md")
            ):
                emoji = "📝"
            elif file.lower().endswith(".py"):
                emoji = "🐍"
            else:
                emoji = "📄"
            caption += "{} <code>{}</code> (<code>{}</code>)\n".format(
                emoji, file, human_readable_size(size)
            )
    caption += "\n<b>{} folders, {} files</b>".format(folder_count, file_count)
    await e.reply(caption, parse_mode="html")


@new_cmd(pattern="cd")
@auth_only
async def _cd(e):
    try:
        directory = e.text.split(" ", 1)[1]
        directory = directory + "/" if not directory.endswith("/") else directory
    except IndexError:
        directory = "./"
    if not path.isdir(directory):
        await e.reply("`No such directory found.`")
        return
    os.chdir(directory)
    curr = os.getcwd()
    await e.reply("`Changed directory to {}`".format(curr))


@new_cmd(pattern="rm")
@auth_only
async def _rm(e):
    try:
        arg = e.text.split(" ", 1)[1]
    except IndexError:
        arg = None
    if arg is not None:
        os.remove(arg)
        await e.reply("`Removed {} successfully.`".format(arg))
        return
    # list files as buttons
    try:
        directory = e.text.split(" ", 1)[1]
        directory = directory + "/" if not directory.endswith("/") else directory
    except IndexError:
        directory = "./"
    contents = listdir(directory)
    if len(contents) == 0:
        await e.reply("`No files found.`")
        return

    buttons = []
    btns = []
    for file in contents:
        if len(btns) == 2:
            buttons.append(btns)
            btns = []
        max_bytes = 50
        btns.append(Button.inline(file, data=f"rm {file[:max_bytes]}"))
    if btns:
        buttons.append(btns)
    await e.reply("Select the files to delete.", buttons=buttons)


@bot.on(events.CallbackQuery(pattern=r"rm_x"))
async def _rm_cbq_xedit(e):
    try:
        directory = e.data.decode().split(" ", 1)[1]
        directory = directory + "/" if not directory.endswith("/") else directory
    except IndexError:
        directory = "./"
    contents = listdir(directory)
    if len(contents) == 0:
        await e.edit("`No files found.`")
        return

    buttons = []
    btns = []
    for file in contents:
        if len(btns) == 2:
            buttons.append(btns)
            btns = []
        max_bytes = 50
        btns.append(Button.inline(file, data=f"rm {file[:max_bytes]}"))
    if btns:
        buttons.append(btns)
    await e.edit("Select the files to delete.", buttons=buttons)


@bot.on(events.CallbackQuery(pattern=r"rm (.*)"))
async def _rm_cbq(e):
    file = e.data_match.group(1)
    try:
        path = os.path.join(os.getcwd(), get_full_path(file.decode()))
        await e.edit(
            "Are you sure you want to delete this file?\n\n`{}`".format(path),
            buttons=[
                [
                    Button.inline("Yes", data=f"rmx {file.decode()}"),
                    Button.inline("No", data="cancel"),
                ],
                [Button.inline("Back", data="rm_x")],
            ],
        )
    except Exception as o:
        await e.answer(f"Error: {str(o)}")


@bot.on(events.CallbackQuery(pattern=r"cancel"))
async def _rm_cbq(e):
    await e.delete()


@bot.on(events.CallbackQuery(pattern=r"rmx (.*)"))
async def _rm_cbq(e):
    file = e.data_match.group(1)
    try:
        path = (os.path.join(os.getcwd(), get_full_path(file.decode()))).strip()
        if os.path.isdir(path):
            import shutil

            shutil.rmtree(path)
        else:
            os.remove(path)
        await e.answer("Deleted Successfully!")
        await _rm_cbq_xedit(e)
    except Exception as o:
        msg = await e.get_message()
        await msg.edit(msg.text + f"\n\nError: `{str(o)}`", buttons=msg.buttons)


def get_full_path(path):
    files = listdir(os.getcwd())
    for file in files:
        if file.startswith(path):
            return file
    return path


def extract_args_from_text(text):
    import re

    pattern = r"-(\w+)(?:\s+([^\s-]+))?"
    _text_without_any_args = re.sub(pattern, "", text)

    args_list = re.findall(pattern, text)
    return {
        key: value if value else True for key, value in args_list
    }, _text_without_any_args.strip()


@new_cmd(pattern="upl")
@auth_only
async def _upl(e):
    l = await get_text_content(e)
    if not l:
        return await e.reply("No input found.")
    _l, args = extract_args_from_text(l)
    if not _l:
        return await e.reply("No input file/folder specified.")
    _files = []
    _needed_ext = (
        args.get("ext", None) or args.get("e", None) or args.get("extension", None)
    )
    if os.path.isdir(_l):
        for f in os.listdir(_l):
            if _needed_ext and not f.endswith(_needed_ext):
                continue
            _file_path = os.path.join(_l, f)
            if os.path.isfile(_file_path):
                _file_name = f.split("/")[-1]
                _file_name_without_ext = "".join(_file_name.split(".")[:-1])
                _files.append(
                    {
                        "path": _file_path,
                        "name": _file_name,
                        "name_without_ext": _file_name_without_ext,
                    }
                )

    elif os.path.isfile(_l):
        _file_name = _l.split("/")[-1]
        _file_name_without_ext = (
            "".join(_file_name.split(".")[:-1])
            if args.get("name", "") == ""
            else args.get("name", "")
        )

        _files.append(
            {"path": _l, "name": _file_name, "name_without_ext": _file_name_without_ext}
        )

    if not _files:
        return await e.reply("No files found.")

    _caption = args.get("caption", None) or args.get("c", "")
    if args.get("nc", False) or args.get("no_caption", False):
        _caption = None

    _chat = args.get("chat", None) or args.get("c", "")
    if _chat == "":
        _chat = e.chat_id

    if not _caption and not any([args.get("nc", False), args.get("no_caption", False)]):
        _caption = _file_name_without_ext if len(_files) == 1 else ""

    message = await e.reply("Uploading {} file(s)...".format(len(_files)))
    _percent, _progress, _total = 0, 0, len(_files)
    for _file in _files:
        attributes, streamble_media, thumbnail = [], False, None
        if os.path.isfile(_file["path"]) and _file["path"].endswith(
            (".mp4", ".mkv", ".webm", ".3gp", ".mpeg")
        ):
            duration, width, height = await get_video_metadata(_file["path"])
            attributes.append(
                types.DocumentAttributeVideo(
                    duration=duration,
                    w=width,
                    h=height,
                    round_message=args.get("round", False),
                    supports_streaming=True,
                ),
                types.DocumentAttributeFilename(file_name=_file["name"]),
            )
            streamble_media = True
            if len(thumbs) == 0 and args.get("nothumb", False) == False:
                thumbnail = await generate_thumbnail(
                    _file["path"], _file["name"] + ".jpg"
                )
            elif len(thumbs) > 0:
                thumbnail = thumbs[0]

        elif os.path.isfile(_file["path"]) and _file["path"].endswith(
            (".mp3", ".wav", ".flv", ".ogg", ".opus", ".alac")
        ):
            metadata = tinytag.TinyTag.get(l)
            attributes = [
                types.DocumentAttributeAudio(
                    duration=int(metadata.duration or "0"),
                    performer=metadata.artist or "-",
                    title=metadata.title or "-",
                    voice=args.get("voice", False),
                ),
                types.DocumentAttributeFilename(file_name=_file["name"]),
            ]

        uploaded_file = await upload_file(e.client, _file["path"])
        if uploaded_file:
            await e.client.send_file(
                _chat,
                file=uploaded_file,
                caption=_caption,
                force_document=True,
                thumb=thumbnail,
                attributes=attributes,
                supports_streaming=streamble_media,
                parse_mode="html",
            )
            _progress += 1
            _percent = ((_progress) / _total) * 100
            if _percent % 10 == 0:
                await message.edit(
                    "Uploaded {}% of ({}/{}) files.".format(_percent, _progress, _total)
                )

        else:
            await message.edit("Failed to upload {}.".format(_file["name"]))
            return

    await message.edit("Upload Done.")


@new_cmd(pattern="ul")
@auth_only
async def _ul(e):
    l = await get_text_content(e)
    if not l:
        return await _ls(e)
    caption = ""
    chat = e.chat_id
    if any([re.search(x, l.lower()) for x in ["--chat", "-c"]]):
        if "--chat" in l.lower():
            args = l.split("--chat")
            l = re.sub("--chat (.*) -", "-", l).strip()
            if "--chat" in l.lower():
                l = re.sub("--chat (.*)", "", l).strip()
        else:
            args = l.split("-c")
            l = re.sub("-c (.*) -", "-", l).strip()
            if "-c" in l.lower():
                l = re.sub("-c (.*)", "", l).strip()
        chat = args[1].split("-")[0].strip() if len(args) > 1 else e.chat_id
        chat = int(chat) if str(chat).isdigit() else chat
    if any([re.search(x, l.lower()) for x in ["--text", "-t"]]):
        args = l.split("--text") if "--text" in l else l.split("-t")
        caption = args[1] if len(args) > 1 else ""
        l = args[0].strip()
    if any([re.search(x, l.lower()) for x in ["--folder", "-f"]]):
        args = l.split("--folder") if "--folder" in l else l.split("-f")
        ext = args[1] if len(args) > 1 else ""
        l = args[0].strip()
        directory = l + "/" if not l.endswith("/") else l
        try:
            files = []
            for f in os.listdir(l):
                if ext:
                    if f.endswith(ext.strip()):
                        files.append(f)
                else:
                    files.append(f)
            if len(files) == 0:
                return await e.reply("No files with that extension in Dir.")
        except Exception as o:
            return await e.reply(f"OSError: {o}")
    else:
        files = [l]
        directory = ""
    await upload_decorator(e, files, chat, caption, directory)


async def upload_decorator(e, files, chat, caption: str, directory: str):
    thumb, attributes, action, streamable = None, [], "document", False
    force_document = False
    if len(files) == 1:
        msg = await e.reply("`Uploading...`")
    else:
        msg = await e.reply(f"`Uploading...` **0/{len(files)}**.")
    done = 0
    for l in files:
        l = directory + l
        filename = l.split("\\")[-1]
        caption = filename
        filename = filename.split("/")[-1] if filename == l else filename
        if l.endswith(("mp4", "mkv", "3gp", "webm")):
            try:
                thumb = (
                    generate_thumbnail(l, l + "_thumb.jpg")
                    if len(thumbs) == 0
                    else thumbs[0]
                )
            except:
                thumb = None if len(thumbs) == 0 else thumbs[0]
            d, w, h = get_video_metadata(l)
            attributes = [
                types.DocumentAttributeVideo(
                    w=w, h=h, duration=d, supports_streaming=True
                )
            ]
            streamable = True
            action = "video"
            force_document = False
        elif l.endswith(("mp3", "wav", "flv", "ogg", "opus")):
            metadata = tinytag.TinyTag.get(l)
            attributes = [
                types.DocumentAttributeAudio(
                    duration=int(metadata.duration or "0"),
                    performer=metadata.artist or "Me",
                    title=metadata.title or "Unknown",
                )
            ]
            action = "audio"
        try:
            file = await upload_file(e.client, l)
            async with e.client.action(chat, action):
                await e.client.send_message(
                    chat,
                    caption,
                    file=file,
                    thumb=thumb,
                    attributes=attributes,
                    force_document=force_document,
                    supports_streaming=streamable,
                )
            if thumb and thumb != "thumb.jpg":
                remove(thumb)
            done += 1
        except Exception as exc:
            msg = await msg.edit("`error on uploading.\n{}`".format(str(exc)))
        if done > 1:
            msg = await msg.edit(
                f"`Uploading...` {done}/{len(files)} from `{directory}`."
            )
    await msg.delete()


@new_cmd(pattern="setthumb")
@auth_only
async def set_t(e):
    f = await e.get_reply_message()
    if not f or not f.media:
        return await e.reply("Reply to any image to set custom video thumbnail.")
    t = await f.download_media("thumb.jpg")
    await e.reply("`Sucessfully set custom thumb!`")
    thumbs.append(t)


@new_cmd(pattern="resetthumb")
@auth_only
async def _rsy_t(e):
    await e.reply("Set custom thumb to `None`.")
    thumbs.clear()


@new_cmd(pattern="dl")
@auth_only
async def _dl(e):
    r = await e.get_reply_message()
    if not r:
        return await e.reply("`Reply to a file.`")
    if not r.media:
        return await e.reply("`Reply to a file.`")
    await e.reply("`Downloading...`")
    with open(r, "wb") as f:
        dl = await download_file(e.client, r.name, r, progress_callback=progress)


@new_cmd(pattern="auth")
@master_only
async def _auth(e):
    if not e.reply_to and not len(e.text.split(None)) > 1:
        AUTH_LIST = "Auth list:\n"
        sno = 0
        for user in get_auth():
            sno += 1
            AUTH_LIST += (
                "<b>{sno}.</b> <a href='tg://user?id={user}'>{user_name}</a>\n".format(
                    sno=sno, user=user, user_name=user
                )
            )
        await e.reply(AUTH_LIST, parse_mode="HTML")
        return
    user, _ = await get_user(e)
    if is_auth(user.id):
        await e.reply(
            "<b>{}</b> is already authorized.".format(get_mention(user, "html")),
            parse_mode="html",
        )
        return
    add_auth(user.id)
    await e.reply(
        "<b>{}</b> is now authorized.".format(get_mention(user, "html")),
        parse_mode="html",
    )


@new_cmd(pattern="(unauth|rmauth)")
@master_only
async def _unauth(e):
    user, _ = await get_user(e)
    if user is None:
        return await e.reply("Specify a user to unauthorize.")
    if not is_auth(user.id):
        await e.reply(
            "<b>{}</b> is not authorized.".format(get_mention(user, "html")),
            parse_mode="html",
        )
        return
    remove_auth(user.id)
    await e.reply(
        "<b>{}</b> is now unauthorized.".format(get_mention(user, "html")),
        parse_mode="html",
    )


@new_cmd(pattern="update")
@master_only
async def update_origin(e):
    msg = await e.reply("`Updating...`")
    system("git pull")
    await msg.edit("`Restarting...`")
    args = [sys.executable, "main.py"]
    execle(sys.executable, *args, environ)


@new_cmd(pattern="restart")
@master_only
async def restart_process(e):
    await e.reply("`Restarting...`")
    args = [sys.executable, "main.py"]
    execle(sys.executable, *args, environ)


@new_cmd(pattern="speedtest")
@auth_only
async def _speedtest(e):
    msg = await e.reply("Testing internet speed...")
    st = speedtest.Speedtest()
    download = st.download()
    upload = st.upload()
    ping = st.results.ping
    server = st.results.server.get("name", "Unknown")
    isp = st.results.client.get("isp", "Unknown")
    ip = st.results.client.get("ip", "Unknown")
    country = st.results.client.get("country", "Unknown")
    result = (
        f"**Speedtest Results:**\n\n"
        f"**Download:** `{human_readable_size(download, True)}`\n"
        f"**Upload:** `{human_readable_size(upload, True)}`\n"
        f"**Ping:** `{ping} ms`\n"
        f"**Server:** `{server}`\n"
        f"**ISP:** `{isp}`\n"
        f"**IP:** `{ip}`\n"
        f"**Country:** `{country}`"
    )
    await msg.edit(result)
