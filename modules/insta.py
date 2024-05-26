from aiohttp import ClientSession, ClientTimeout

from ._handler import new_cmd


@new_cmd(pattern="(insta|instagram|instadl|instadownload)")
async def _insta(message):
    try:
        url = message.text.split(" ", maxsplit=1)[1]
    except IndexError:
        return await message.reply("`Give me a link to download!`")

    resp = await message.reply("`Downloading media...`")

    caption, post_medias, code = await insta_dl(url)
    if code == -1:
        return await message.reply(f"**Error:**\n```{post_medias}```")

    if not post_medias:
        return await message.reply("`No media found!`")

    videos = []
    images = []
    stickers = []

    for media in post_medias:
        if media["type"] == "mp4":
            videos.append(media["url"])
        elif media["type"] == "jpg" or media["type"] == "png":
            images.append(media["url"])
        elif media["type"] == "webp":
            stickers.append(media["url"])

    caption_done = False

    if videos:
        await message.respond(caption, file=videos)
        caption_done = True
    if images:
        if caption_done:
            await message.respond(file=images)
        else:
            await message.respond(caption, file=images)
            caption_done = True
    if stickers:
        await message.respond(file=stickers)
        if not caption_done:
            await message.respond(caption)

    await resp.delete()


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://fastdl.app/en",
}


async def insta_dl(url: str):
    async with ClientSession(timeout=ClientTimeout(total=10)) as session:
        async with session.post(
            "https://fastdl.app/api/convert",
            json={"url": url},
            headers=DEFAULT_HEADERS,
        ) as resp:
            data = await resp.json()
            caption = ""
            post_medias = []

            try:
                if isinstance(data, dict):
                    if data.get("meta", {}).get("title"):
                        caption = data.get("meta", {}).get("title")

                    post_medias.append(
                        {
                            "url": data.get("url", {})[0].get("url"),
                            "type": data.get("url", {})[0].get("type"),
                        }
                    )
                elif isinstance(data, list):
                    for i in data:
                        if i.get("meta", {}).get("title"):
                            caption = i.get("meta", {}).get("title")

                        post_medias.append(
                            {
                                "url": i.get("url", {})[0].get("url"),
                                "type": i.get("url", {})[0].get("type"),
                            }
                        )

                return caption, post_medias, 0
            except Exception as e:
                return data, e, -1
