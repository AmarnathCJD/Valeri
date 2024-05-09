from asyncio.subprocess import PIPE, create_subprocess_shell

from aiofiles.os import mkdir, remove
from aiofiles.ospath import exists
from aiohttp import ClientSession as Client
from aiohttp import ClientTimeout as Timeout
from telethon import Button

from ._config import OWNER_ID
from ._handler import new_cmd, newCall

COMMAND_FOR_DL = "yt-dlp --downloader aria2c '{url}'"
SERIES_BACKEND_URL = "https://6301-2-59-134-198.ngrok-free.app"
SERVIO_TEMP = "https://8dc2d949f885aaa3a1a29df5cb09b89c.serveo.net"


async def file_server():
    import os

    from aiohttp import web

    async def handle(request):
        path = request.match_info.get("path", "")
        if os.path.isfile(path):
            return web.FileResponse(os.path.join(os.getcwd(), "downloads", path))
        else:
            return web.FileResponse(os.path.join(os.getcwd(), "downloads", path))

    app = web.Application()
    app.router.add_get("/{path:.*}", handle)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 2002)
    await site.start()


async def search_series(query: str, client: Client):
    async with client.get(
        f"{SERIES_BACKEND_URL}/api/search", params={"query": query}
    ) as resp:
        return (await resp.json()).get("titles", [])


def get_id_from_href(href: str):
    return href.split("-")[-1]


async def get_series_info(series_id: str, client: Client):
    async with client.get(f"{SERIES_BACKEND_URL}/api/info?id={series_id}") as resp:
        return await resp.json()


async def get_seasons(series_id: str, client: Client):
    series_id = get_id_from_href(series_id)

    print(f"{SERIES_BACKEND_URL}/api/seasons?id={series_id}")
    async with client.get(f"{SERIES_BACKEND_URL}/api/seasons?id={series_id}") as resp:
        return await resp.json()


async def get_episodes(series_id: str, season_id: str, client: Client):
    series_id = get_id_from_href(series_id)
    async with client.get(f"{SERIES_BACKEND_URL}/api/episodes?id={season_id}") as resp:
        return await resp.json()


async def get_embed(media_id: str, category: str, client: Client):
    print(f"{SERIES_BACKEND_URL}/api/embed?id={media_id}&cat={category.lower()}")
    async with client.get(
        f"{SERIES_BACKEND_URL}/api/embed",
        params={"id": media_id, "cat": category.lower()},
    ) as resp:
        try:
            resp = await resp.json()
            source_hash = resp.get("source_hash")

            if not source_hash:
                return None

            print(f"{SERIES_BACKEND_URL}/{source_hash}")
            async with client.get(f"{SERIES_BACKEND_URL}/{source_hash}") as source_resp:
                return await source_resp.json()

        except:

            return None


series_meta_cache = {}


@new_cmd(pattern="series")
# @auth_only
async def search_series_x(e):
    try:
        q = e.text.split(" ", 1)[1]
    except IndexError:
        return await e.reply("Give me a query.")

    async with Client(timeout=Timeout(10)) as client:
        titles = await search_series(q, client)
        if not titles:
            return await e.reply("No results found.")

        buttons = []
        for title in titles:
            buttons.append(
                [
                    Button.inline(
                        title["title"], data=f"series_{get_id_from_href(title['href'])}"
                    )
                ]
            )
            series_meta_cache[get_id_from_href(title["href"])] = title

            if len(buttons) == 15:
                break

        await e.reply(
            "Choose a series:",
            buttons=buttons,
            file="https://envs.sh/eET.png",
            force_document=True,
        )


m3u8_cache = {}


@newCall(pattern="series_(.*)")
async def series_x(e):
    series_id = e.data.decode().split("_", 1)[1]

    async with Client(timeout=Timeout(10)) as client:
        try:
            series = series_meta_cache[series_id]
        except KeyError:
            return await e.edit("Series not found.")

        metadata = await get_series_info(
            "/{}/x-{}".format(series.get("category").lower(), series_id), client
        )
        if not metadata:
            return await e.edit("Failed to get metadata.")

        CAPTION = ""
        CAPTION += f"**Title:** {series['title']}\n"
        CAPTION += f"**Category:** {series['category']}\n"
        CAPTION += f"\n**Description:** __{metadata.get('description', 'No description available.')}__\n"
        CAPTION += f"**Quality:** {metadata.get('quality', 'N/A')}\n"
        CAPTION += f"**IMDB:** `{metadata.get('imdb_rating', 'IMDB: N/A').split('IMDB:')[1].strip()}`\n"
        CAPTION += f"**Genres:** {metadata.get('genres', 'N/A')}\n"
        CAPTION += f"**Release Date:** {metadata.get('release', 'N/A')}\n"
        CAPTION += f"**Runtime:** {metadata.get('runtime', 'N/A')}\n"
        CAPTION += f"**Casts:** {metadata.get('casts', 'N/A')}\n"
        CAPTION += f"**Country:** {metadata.get('country', 'N/A')}\n"
        CAPTION += (
            f"**Trailer:** **[YouTube Link]({metadata.get('trailer', 'N/A')})**\n"
        )
        CAPTION += "\n\n"

        if series.get("category") == "Movie":
            src = await get_embed(series_id, "movie", client)
            if src is None:
                return await e.edit("Failed to get source.")
            tick_emoji = "✅"

            await e.edit(
                CAPTION
                + f"**Source Avaliable {tick_emoji}**\n\n**SUBS: {', '.join([sub['label'] for sub in src['subs']])}**",
                buttons=[
                    [
                        Button.inline(
                            "Download", data=f"dl_{src['id']}_movie_{series_id}_0_0"
                        )
                    ],
                    [Button.inline("Back", data=f"series_{series_id}")],
                ],
            )
            m3u8_cache[src["id"]] = src
            return

        seasons = await get_seasons(series_id, client)

        buttons = []
        for season in seasons:
            buttons.append(
                [
                    Button.inline(
                        season["title"],
                        data=f"season_{series_id}_{season['season_id']}_{series['category']}_{len(buttons)+1}",
                    )
                ]
            )

        buttons.append([Button.inline("Back", data="back")])

        await e.edit(
            CAPTION + f"Choose a season for {series['title']}:",
            buttons=buttons,
            file=(SERIES_BACKEND_URL + series["poster"]).replace("184x275", "500x750"),
        )


@newCall(pattern="season_(.*)")
async def season_x(e):
    series_id, season_id, category, season_index = e.data.decode().split("_", 4)[1:]

    async with Client(timeout=Timeout(10)) as client:
        episodes = await get_episodes(series_id, season_id, client)

        buttons = []
        for episode in episodes:
            buttons.append(
                [
                    Button.inline(
                        episode["title"],
                        data=f"episode_{series_id}_{season_id}_{episode['episode_id']}_{category}_{season_index}_{len(buttons)+1}",
                    )
                ]
            )

        buttons.append([Button.inline("Download All", data=f"download_all")])
        buttons.append([Button.inline("Back", data=f"series_{series_id}")])

        await e.edit(
            f"Choose an episode for {series_meta_cache[series_id]['title']}:",
            buttons=buttons,
        )


@newCall(pattern="episode_(.*)")
async def episode_x(e):
    series_id, season_id, episode_id, category, season_index, episode_index = (
        e.data.decode().split("_", 6)[1:]
    )

    async with Client(timeout=Timeout(10)) as client:
        src = await get_embed(episode_id, category, client)
        if src is None:
            return await e.edit("Failed to get source.")
        tick_emoji = "✅"
        metadata = await get_series_info(
            "/{}/x-{}".format(category.lower(), series_id), client
        )
        if not metadata:
            return await e.edit("Failed to get metadata.")

        CAPTION = ""
        CAPTION += f"**Title:** {metadata['title']}\n"
        CAPTION += f"**Category:** {category}\n"
        CAPTION += f"\n**Description:** __{metadata.get('description', 'No description available.')}__\n"
        CAPTION += f"**Quality:** {metadata.get('quality', 'N/A')}\n"
        CAPTION += f"**IMDB:** `{metadata.get('imdb_rating', 'IMDB: N/A').split('IMDB:')[1].strip()}`\n"
        CAPTION += f"**Genres:** {metadata.get('genres', 'N/A')}\n"
        CAPTION += f"**Release Date:** {metadata.get('release', 'N/A')}\n"
        CAPTION += f"**Runtime:** {metadata.get('runtime', 'N/A')}\n"
        CAPTION += f"**Casts:** {metadata.get('casts', 'N/A')}\n"
        CAPTION += f"**Country:** {metadata.get('country', 'N/A')}\n"
        CAPTION += (
            f"**Trailer:** **[YouTube Link]({metadata.get('trailer', 'N/A')})**\n"
        )
        CAPTION += "\n\n"
        _season_index_f = "0" + season_index if len(season_index) == 1 else season_index
        _episode_index_f = (
            "0" + episode_index if len(episode_index) == 1 else episode_index
        )
        CAPTION += "**E{}S{}**\n\n".format(_episode_index_f, _season_index_f)
        CAPTION += f"**Source Avaliable {tick_emoji}**\n\n**SUBS: {', '.join([sub['label'] for sub in src['subs']])}**"
        if len(CAPTION) > 1023:
            CAPTION = f"**Source Avaliable {tick_emoji}**\n\n**SUBS: {', '.join([sub['label'] for sub in src['subs']])}**"

        await e.edit(
            CAPTION,
            buttons=[
                [
                    Button.inline(
                        "Download",
                        data=f"dl_{src['id']}_{category}_{season_index}_{episode_index}_{series_id}",
                    )
                ],
                [
                    Button.inline(
                        "Back",
                        data=f"season_{series_id}_{season_id}_{category}_{season_index}",
                    )
                ],
            ],
        )
        m3u8_cache[src["id"]] = src


import time


def generate_ffmpeg_command(mp4_file_path, subs):
    ffmpeg_command = ["ffmpeg", "-y", "-i", '"{}"'.format(mp4_file_path)]

    for sub in subs:
        ffmpeg_command.extend(["-i", sub["file"]])

    output_file_path = mp4_file_path.replace(".mkv", "_subs.mkv")

    ffmpeg_command.extend(["-map", "0:v", "-map", "0:a"])

    for i in range(len(subs)):
        ffmpeg_command.extend(["-map", f"{i + 1}:s:0"])
        ffmpeg_command.extend(
            ["-metadata:s:s:%d" % i, 'language="' + subs[i]["label"] + '"']
        )

    ffmpeg_command.extend(["-c", "copy", '"{}"'.format(output_file_path)])

    return ffmpeg_command


@newCall(pattern="dl_(.*)")
async def download_x(e):
    _, media_id, category, season_index, episode_index, series_id = (
        e.data.decode().split("_", 5)
    )

    url_with_meta = m3u8_cache.get(media_id)
    if not url_with_meta:
        return await e.edit("Invalid media ID.")

    url = url_with_meta["file"]

    subs_urls = url_with_meta["subs"]

    # await e.edit("Downloading...", buttons=[Button.inline("Back", data=f"episode_{series_id}_{season_index}_{episode_index}_{category}_{season_index}_{episode_index}")])

    try:
        series = series_meta_cache[series_id]
    except KeyError:
        return await e.edit("Series not found.")

    out_folder = "downloads"
    if not await exists(out_folder):
        await mkdir(out_folder)
    out_filename = (
        f"{series['title']}_{category}_{season_index}_{episode_index}.mkv"
        if "movie" not in category.lower()
        else f"{series['title']}.mkv"
    )

    _season_index_f = "0" + season_index if len(season_index) == 1 else season_index
    _episode_index_f = "0" + episode_index if len(episode_index) == 1 else episode_index
    await e.edit(
        f"**E{_episode_index_f}S{_season_index_f}**\nDownloading, please wait...",
        buttons=[Button.inline("Back", data=f"series_{series_id}")],
    )
    ms = await e.respond("Downloading...")
    t = time.time()
    cmd = f"yt-dlp --downloader aria2c '{url}' -o '{out_folder}/{out_filename}'"

    process = await create_subprocess_shell(
        cmd=cmd,
        stdout=PIPE,
        stderr=PIPE,
    )

    await process.wait()
    # merge all subs to the file

    ffmpeg_command = generate_ffmpeg_command(f"{out_folder}/{out_filename}", subs_urls)
    await ms.edit("Merging subs...")
    print("FFMPEG CMD: " + " ".join(ffmpeg_command))
    # await ms.respond("FFMPEG CMD: `"+" ".join(ffmpeg_command) + "`")
    (await create_subprocess_shell(" ".join(ffmpeg_command))).wait()

    # os.remove(f"{out_folder}/{out_filename}")
    # await create_subprocess_shell(f"mv '{out_folder}/{out_filename.replace('.mkv', '_subs.mkv')}' downloads/").wait()

    await ms.edit(
        f"Downloaded {out_filename} in {time.time() - t:.2f} seconds.",
        buttons=[
            [
                Button.inline(
                    "Back",
                    data=f"episode_{series_id}_{season_index}_{episode_index}_{category}_{season_index}_{episode_index}",
                )
            ],
            [Button.url("Index Link", f"{SERVIO_TEMP}")],
        ],
    )
    await remove(f"{out_folder}/{out_filename}")

    # move the file to downloads folder


dl_all_queue = []


@newCall(pattern="download_all")
async def download_all(e):
    if e.sender_id != OWNER_ID and e.sender_id in dl_all_queue:
        await e.answer("You're already in the queue, wait for your turn.", alert=True)
        return
    msg = await e.get_message()

    buttons = msg.reply_markup.rows

    print(len(buttons))


def progress_stdout_yielded_downloadx(url, out_folder, out_filename):
    import shlex
    import subprocess

    cmd = f"youtube-dl -o '{out_folder}/{out_filename}' {url}"
    print(cmd)
    process = subprocess.Popen(
        shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    while True:
        output = process.stdout.readline()
        if output == b"" and process.poll() is not None:
            break
        if output:
            yield output
    rc = process.poll()

    return rc


async def progress_stdout_yielded_download(url, out_folder, out_filename):
    if not await exists(out_folder):
        await mkdir(out_folder)

    cmd = f"yt-dlp --downloader aria2c '{url}' -o '{out_folder}/{out_filename}'"
    print("Command:", cmd)

    process = await create_subprocess_shell(
        cmd=cmd,
        stdout=PIPE,
        stderr=PIPE,
    )

    while True:
        output = await process.stdout.readline()
        if output == b"" and process.returncode is not None:
            break
        if output:
            yield output.decode("utf-8")

    await process.wait()
