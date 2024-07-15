import os
from subprocess import PIPE, Popen

import requests
from yt_dlp import YoutubeDL


def gather_info(id: str):
    url = f"https://e83f-68-183-237-158.ngrok-free.app/{id}"
    resp = requests.get(url)

    return resp.json()


def download_season():
    season_id = input("Enter the season ID: ")
    season_number = input("Enter the season number: ")
    series_title = input("Enter the series title: ")

    season_number = "0" + season_number if len(season_number) == 1 else season_number
    out_file_title = f"{series_title} - S{season_number}E(?).mkv"

    url = f"https://e83f-68-183-237-158.ngrok-free.app/api/episodes?id={
        season_id}"
    resp = requests.get(url)

    print("-> downloader - gathering episodes info...")

    ids = [episode["episode_id"] for episode in resp.json()]

    print("-> downloader - found {} episodes...".format(len(ids)))
    ep_ids = []
    for i in ids:
        resp = get_embed_of_episode(i)
        ep_ids.append(
            {
                "id": i,
                "out_file": out_file_title.replace(
                    "(?)",
                    (
                        "0" + str(ids.index(i) + 1)
                        if len(str(ids.index(i) + 1)) == 1
                        else str(ids.index(i) + 1)
                    ),
                ),
            }
        )

    print("-> downloader - downloading season...")
    print("-> downloader - this may take a while...")

    i = 0
    for e in ep_ids:
        source_hash = requests.get(
            f"https://e83f-68-183-237-158.ngrok-free.app/api/embed?id={e['id']}&cat=tv"
        ).json()["source_hash"]

        print(
            "-> downloader - downloading ({}/{}): {}...".format(
                i + 1, len(ep_ids), e["out_file"]
            ),
            end="\r",
        )

        episode_info = gather_info(source_hash)

        download_url(episode_info["file"], "downloads", e["out_file"])
        merge_subs(os.path.join("downloads", e["out_file"]), episode_info["subs"])

        i += 1

    print("-> downloader - done downloading season...")


def get_embed_of_episode(episode_id: str):
    url = f"https://e83f-68-183-237-158.ngrok-free.app/api/embed?id={
        episode_id}"
    resp = requests.get(url)

    return resp.json()


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


def merge_subs(video_path, subs_paths):
    ffmpeg_command = generate_ffmpeg_command(video_path, subs_paths)

    print("-> downloader - merging {} subs...".format(len(subs_paths)))

    process = Popen(" ".join(ffmpeg_command), shell=True, stdout=PIPE, stderr=PIPE)
    process.communicate()


def download_url(url, out_folder, out_filename):
    ydl_opts = {
        "quiet": True,
        # "external_downloader": "aria2c",
        # 'external_downloader_args': ['-x', '16'],
        "outtmpl": os.path.join(out_folder, out_filename),
        "verbose": False,
        # "addmetadata": True,
        "no-warnings": True,
    }

    print("-> downloader - downloading video...")

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


if __name__ == "__main__":
    download_season()
    exec()
    title_id = input("Enter the ID: ")
    out_filename = input("Enter the output filename: ")
    out_folder = "downloads"

    url_info = gather_info(title_id)

    download_url(url_info["file"], out_folder, out_filename)
    merge_subs(os.path.join(out_folder, out_filename), url_info["subs"])

    print("-> downloader - removing temp files...")
    os.remove(os.path.join(out_folder, out_filename))

    print("-> downloader - done")
    print("-> downloader - exiting...")
