import os
import re
import time
import sys
import pytube
from threading import Thread
from pytube.cli import on_progress
from colorama import just_fix_windows_console
from termcolor import cprint
import helper_func

# use Colorama to make Termcolor work on Windows too
just_fix_windows_console()

# get the inital timee before running the script
t1 = time.perf_counter()


def header(url):
    yt = pytube.YouTube(url)
    title = yt.title
    other = f"Views: {yt.views} Duration: {yt.length}"
    return title, other


def mp3(url, save_out, count):
    try:
        titles = f"Title: {header(url)[0]}\n{header(url)[1]}"
        cprint(titles, "green")
        out_file = (
            pytube.YouTube(url, on_progress_callback=on_progress)
            .streams.filter(only_audio=True)
            .first()
            .download(helper_func.create_folder(rf"Youtube\{save_out}"))
        )
        cprint(f":) {count if count else 1} \n", "cyan")
        base, ext = os.path.splitext(out_file)
        new_file = base + ".mp3"
        os.rename(out_file, new_file)
    except pytube.exceptions.LiveStreamError:
        cprint(f"Unable to download {header(url)[0]} as it's streaming live..", "red")
    except pytube.exceptions.VideoUnavailable:
        cprint(f"{header(url)[1]} music is unavailable, skipping.", "red")
    except FileExistsError:
        cprint(f"Looks like {header(url)[0]} music is already present. \n", "red")


def solo_video(url, save_out, count):
    try:
        titles = f"Title: {header(url)[0]}\n{header(url)[1]}"
        cprint(titles, "green")
        pytube.YouTube(
            url, on_progress_callback=on_progress
        ).streams.get_highest_resolution().download(
            helper_func.create_folder(rf"Youtube\{save_out}")
        )
        cprint(f":) {count if count else 1} \n", "cyan")
    except pytube.exceptions.LiveStreamError:
        cprint(f"Unable to download {header(url)[0]} as it's streaming live..", "red")
    except pytube.exceptions.VideoUnavailable:
        cprint(f"{header(url)[0]} Video is unavailable, skipping.", "red")


def regex_audio(ask):
    return re.search(
        "audio|mp3|music|flac|wav|aac|ogg|audios", ask, flags=re.IGNORECASE
    )


def playlists(link, ask):
    playlist = pytube.Playlist(link)
    cprint(
        "\nNumber of videos in playlist: %s"
        % (final_count := len(playlist.video_urls)),
        "blue",
    )
    threads = []
    if regex_audio(ask):
        cprint("Starting to download MP3s of the videos\n", "yellow")
        for count, music_url in enumerate(playlist.video_urls, start=1):
            yt = pytube.YouTube(music_url)
            th = Thread(
                target=mp3,
                args=(
                    music_url,
                    rf"Audios\{yt.author}",
                    f"{count}/{final_count}",
                ),
            )
            threads.append(th)
            th.start()
    else:
        cprint("Starting to download videos in 720p\n", "yellow")
        for count, video_url in enumerate(playlist.video_urls, start=1):
            yt = pytube.YouTube(video_url)
            th = Thread(
                target=solo_video,
                args=(
                    video_url,
                    rf"Videos\{yt.author}",
                    f"{count}/{final_count}",
                ),
            )
            threads.append(th)
            th.start()
    for k in threads:
        k.join()


def askuser(link, ask):
    try:
        if regex_audio(ask):
            cprint("\nStarting to download MP3s of the video", "yellow")
            mp3(link, "Audios", None)
        else:
            cprint("\nStarting to download video in 720p", "yellow")
            solo_video(link, "Videos", None)
    except pytube.exceptions.RegexMatchError:
        cprint("\nPlease enter a valid server URL!", "red")
        sys.exit(1)


def roulette(link):
    ask = input("Which type do you prefer mp3 or mp4: ")
    try:
        if pytube.Playlist(link):
            cprint("Playlist Detected..calling playlist function", "green")
            return playlists(link, ask)
        else:
            return askuser(link, ask)
    except KeyError:
        return askuser(link, ask)


t2 = time.perf_counter()


def main():
    try:
        roulette(str(input("Please provide the YouTube link for download: ")))
        helper_func.view_file(helper_func.Path)
        cprint(f"It took {t2-t1} seconds to download!\n", "cyan")
    except (NameError, AttributeError):
        cprint(
            "Some of your input or your network connection looks fishy as my AI smells it..",
            "red",
        )
    except KeyboardInterrupt:
        print("Exiting from the script....")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
