import importlib
import math
import os
import random
import string
import sys
import time
from os import listdir, path

import ffmpeg
import telethon

# from PIL import Image
from telethon import errors

from ._config import OWNER_ID, bot, help_dict, log


def human_readable_size(size, speed=False):
    # Convert a size in bytes to a human readable string
    variables = ["bytes", "KB", "MB", "GB", "TB", "EB"]
    if speed:
        variables = ["bps", "Kbps", "Mbps", "Gbps", "Tbps", "Ebps"]
    for x in variables:
        if size < 1024.0:
            return "%3.1f %s" % (size, x)
        size /= 1024.0
    return "%3.1f %s" % (size, "EB")


def time_formatter(seconds: int) -> str:
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + " day(s), ") if days else "")
        + ((str(hours) + " hour(s), ") if hours else "")
        + ((str(minutes) + " minute(s), ") if minutes else "")
        + ((str(seconds) + " second(s), ") if seconds else "")
    )
    return tmp[:-2]


async def progress(
    current, total, gdrive, start, prog_type, file_name=None, is_cancelled=False
):
    now = time.time()
    diff = now - start
    if is_cancelled is True:
        raise Exception("Cancelled")

    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff)
        eta = round((total - current) / speed)
        if "upload" in prog_type.lower():
            status = "Uploading"
        elif "download" in prog_type.lower():
            status = "Downloading"
        else:
            status = "Unknown"
        progress_str = "`{0}` | [{1}{2}] `{3}%`".format(
            status,
            "".join(["▰" for i in range(math.floor(percentage / 10))]),
            "".join(["▱" for i in range(10 - math.floor(percentage / 10))]),
            round(percentage, 2),
        )
        tmp = (
            f"{progress_str}\n"
            f"`{human_readable_size(current)} of {human_readable_size(total)}"
            f" @ {human_readable_size(speed)}`\n"
            f"**ETA :**` {time_formatter(eta)}`\n"
            f"**Duration :** `{time_formatter(elapsed_time)}`"
        )
        if file_name:
            await gdrive.edit(
                f"**{prog_type}**\n\n"
                f"**File Name : **`{file_name}`**\nStatus**\n{tmp}"
            )
        else:
            await gdrive.edit(f"**{prog_type}**\n\n" f"**Status**\n{tmp}")


def load_modules():
    # Load all modules in the modules folder
    for module in listdir(path.dirname(__file__)):
        if module.startswith("_") or not module.endswith(".py"):
            continue
        mod = importlib.import_module("modules." + module[:-3])
        log.info("Loaded module: %s", module[:-3])
        help_dict[module[:-3]] = {}
    log.info("Bot Started.")


def human_readable_size(size, speed=False):
    # Convert a size in bytes to a human readable string
    variables = ["bytes", "KB", "MB", "GB", "TB", "EB"]
    if speed:
        variables = ["bps", "Kbps", "Mbps", "Gbps", "Tbps", "Ebps"]
    for x in variables:
        if size < 1024.0:
            return "%3.1f %s" % (size, x)
        size /= 1024.0
    return "%3.1f %s" % (size, "EB")


async def is_worth(right, chat, user, admin_check=True):
    # Check if a user has a certain right in a chat
    if user == OWNER_ID:
        return True
    try:
        p = await bot(telethon.functions.channels.GetParticipantRequest(chat, user))
    except telethon.errors.rpcerrorlist.UserNotParticipantError:
        return False
    if not p:
        return False
    if not admin_check:
        return True
    p: telethon.tl.types.ChannelParticipant = p.participant
    if isinstance(p, telethon.tl.types.ChannelParticipantCreator):
        return True
    if isinstance(p, telethon.tl.types.ChannelParticipantAdmin):
        if p.admin_rights.to_dict()[right]:
            return True
    return False


async def get_user(e):
    """get user from event.Object"""
    args = e.text.split(maxsplit=2)
    if e.is_reply:
        user = (await e.get_reply_message()).sender
        arg = (args[1] + (args[2] if len(args) > 2 else "")) if len(args) > 1 else ""
    else:
        if len(args) == 1:
            await e.reply("No user specified")
            return None, ""
        try:
            user = await e.client.get_entity(args[1])
        except BaseException as ex:
            await e.reply(str(ex))
            return
        arg = args[2] if len(args) > 2 else ""
    return user, arg


def get_mention(user: telethon.tl.types.User, mode: str = "md"):
    # Get a mention of a user
    if mode == "md":
        return "[" + user.first_name + "](tg://user?id=" + str(user.id) + ")"
    elif mode == "html":
        return '<a href="tg://user?id=' + str(user.id) + '">' + user.first_name + "</a>"


async def has_admin_rights(chat_id, user_id, RIGHT):
    """Check if a user has admin rights in a chat"""
    if user_id == OWNER_ID:
        return True, ""
    try:
        p = await bot(
            telethon.functions.channels.GetParticipantRequest(chat_id, user_id)
        )
    except errors.rpcerrorlist.UserNotParticipantError:
        return False, "User not in chat!"
    p: telethon.tl.types.ChannelParticipant = p.participant
    if isinstance(p, telethon.tl.types.ChannelParticipantCreator):
        return True, ""
    if isinstance(p, telethon.tl.types.ChannelParticipantAdmin):
        if p.admin_rights.to_dict()[RIGHT]:
            return True, ""
        else:
            return (
                False,
                "You are missing admin rights to use this command, {}.".format(RIGHT),
            )
    return False, "You do not have admin rights in this chat"


def human_readable_time(seconds: int):
    """Convert a time in seconds to a human readable string"""
    variables = ["s", "m", "h", "d"]
    for x in variables:
        if seconds < 60:
            return "%d %s" % (seconds, x)
        seconds /= 60
    return "%d %s" % (seconds, "d")


def human_currency(amount: int):
    """Convert an amount of money to a human readable string"""
    variables = ["¢", "¥", "€", "£"]
    for x in variables:
        if amount < 100:
            return "%d %s" % (amount, x)
        amount /= 100
    return "%d %s" % (amount, "£")


def parse_time(time: str):
    """Convert a time string to an integer"""
    if any([time.endswith("s"), time.endswith("second"), time.endswith("seconds")]):
        return int(time[:-1].strip()), "s"
    elif any([time.endswith("m"), time.endswith("minute"), time.endswith("minutes")]):
        return int(time[:-1].strip()) * 60, "m"
    elif any([time.endswith("h"), time.endswith("hour"), time.endswith("hours")]):
        return int(time[:-1].strip()) * 60 * 60, "h"
    elif any([time.endswith("d"), time.endswith("day"), time.endswith("days")]):
        return int(time[:-1].strip()) * 60 * 60 * 24, "d"
    elif any([time.endswith("w"), time.endswith("week"), time.endswith("weeks")]):
        return int(time[:-1].strip()) * 60 * 60 * 24 * 7, "week"
    elif any([time.endswith("m"), time.endswith("month"), time.endswith("months")]):
        return int(time[:-1].strip()) * 60 * 60 * 24 * 30, "m"
    else:
        return 0, "Invalid time format"


async def get_text_content(message):
    """Returns the text content of a message."""
    if message.reply_to_msg_id:
        reply = await message.get_reply_message()
        if reply.media:
            if reply.document:
                doc = await reply.download_media()
                with open(doc, "r", errors="ignore") as f:
                    u = f.read()
                os.remove(doc)
                return u
            else:
                return None
        else:
            return reply.text
    else:
        try:
            return message.text.split(" ", 1)[1]
        except:
            return None


def gen_random_string(length):
    """Generate a random string of a given length"""
    return "".join(random.choice(string.ascii_letters) for i in range(length))


def resize_to_thumbnail(image):
    """Resize an image to a thumbnail"""
    # im = Image.open(image)
    # im = im.resize((100, 100))
    # im.save(image)


def pack_file_to_db(file):
    """Pack a file to a database"""
    return [file.id, file.access_hash, file.file_reference, get_file_type(file)]


def get_file_type(file):
    """Get the type of a file"""
    if isinstance(file, telethon.types.MessageMediaDocument):
        return "document"
    elif isinstance(file, telethon.types.MessageMediaPhoto):
        return "photo"
    elif isinstance(file, telethon.types.MessageMediaGeo):
        return "geo"


def generate_thumbnail(in_filename, out_filename):
    """gen thumb for video"""

    try:
        probe = ffmpeg.probe(in_filename)
        time = 2
        try:
            width = probe["streams"][0]["width"]
        except:
            width = 720
        (
            ffmpeg.input(in_filename, ss=time)
            .filter("scale", width, -1)
            .output(out_filename, vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print(e.stderr.decode(), file=sys.stderr)
        return ""
    return out_filename


def get_video_metadata(file):
    try:
        data = ffmpeg.probe(file)
        return (
            int(data.get("format", {}).get("duration", "0").split(".")[0]),
            data.get("streams", [])[0].get("width", 1),
            data.get("streams", [])[0].get("height", 0),
        )
    except (KeyError, IndexError, ffmpeg.Error, Exception):
        return (1, 1280, 720)
