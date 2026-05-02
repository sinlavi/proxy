import os
import yt_dlp
from balethon import Client

BALE_TOKEN = "1011430416:0-QaVTm8WjXtmVRcZKFvhfr_OGOL6OldiZs"

if not BALE_TOKEN:
    raise ValueError("BALE_TOKEN not set")

bot = Client(BALE_TOKEN)


# -------------------------------------------------
# SEARCH (Uses yt-dlp SoundCloud search engine)
# -------------------------------------------------

def search_soundcloud(query: str):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,   # Do NOT download
    }

    # scsearch10 => return 10 best results
    sc_query = f"scsearch10:{query}"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        data = ydl.extract_info(sc_query, download=False)

    results = []
    entries = data.get("entries", [])

    for e in entries:
        results.append({
            "title": e.get("title"),
            "url": e.get("url"),
            "duration": e.get("duration"),
            "uploader": e.get("uploader"),
        })

    return results


# -------------------------------------------------
# DOWNLOAD TRACK
# -------------------------------------------------

def download_track(url: str):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "track.%(ext)s",
        "quiet": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    # After postprocess, extension becomes .mp3
    if not filename.endswith(".mp3"):
        filename = filename.rsplit(".", 1)[0] + ".mp3"

    return filename, info


# -------------------------------------------------
# BOT HANDLER
# -------------------------------------------------

@bot.on_message()
async def handler(message):

    if not message.text:
        return

    text = message.text.strip()

    # --------------------------------------------
    # SEARCH
    # --------------------------------------------
    if text.startswith("/search"):

        query = text.replace("/search", "").strip()

        if not query:
            await message.reply("Usage: /search song name")
            return

        await message.reply("Searching SoundCloud...")

        results = search_soundcloud(query)

        if not results:
            await message.reply("No results found.")
            return

        reply = "SoundCloud Search Results:\n\n"

        for i, r in enumerate(results, start=1):
            reply += f"{i}. {r['title']}\n"
            reply += f"Artist: {r['uploader']}\n"
            reply += f"Duration: {r['duration']} sec\n"
            reply += f"{r['url']}\n\n"

        await message.reply(reply)
        return

    # --------------------------------------------
    # DOWNLOAD
    # --------------------------------------------
    if "soundcloud.com" in text:
        await message.reply("Downloading audio, please wait...")

        try:
            filename, info = download_track(text)

            caption = f"{info.get('title', 'Track')}\nby {info.get('uploader', 'Unknown')}"

            await message.reply_audio(filename, caption=caption)

        except Exception as e:
            await message.reply(f"Error downloading:\n{e}")

        return

    # --------------------------------------------
    # HELP
    # --------------------------------------------
    await message.reply(
        "SoundCloud Downloader Bot\n\n"
        "Commands:\n"
        "/search song name\n"
        "Or send a SoundCloud link directly."
    )


# -------------------------------------------------
# RUN BOT
# -------------------------------------------------

if __name__ == "__main__":
    bot.run()
