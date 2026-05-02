import os
import yt_dlp
from balethon import Client
from youtubesearchpython import VideosSearch

BALE_TOKEN = "1011430416:0-QaVTm8WjXtmVRcZKFvhfr_OGOL6OldiZs"

if not BALE_TOKEN:
    raise ValueError("BALE_TOKEN not set")

bot = Client(BALE_TOKEN)


# -----------------------
# Search SoundCloud
# -----------------------

def search_soundcloud(query):

    search = VideosSearch(query + " site:soundcloud.com", limit=5)
    results = search.result()["result"]

    tracks = []

    for r in results:
        tracks.append({
            "title": r["title"],
            "url": r["link"],
            "duration": r.get("duration", "unknown"),
            "channel": r["channel"]["name"]
        })

    return tracks


# -----------------------
# Download Track
# -----------------------

def download_track(url):

    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": "track.%(ext)s",
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    return filename, info


# -----------------------
# Message handler
# -----------------------

@bot.on_message()
async def handler(message):

    if not message.text:
        return

    text = message.text.strip()

    # -------------------
    # search
    # -------------------

    if text.startswith("/search"):

        query = text.replace("/search", "").strip()

        if not query:
            await message.reply("Usage:\n/search song name")
            return

        results = search_soundcloud(query)

        if not results:
            await message.reply("No results.")
            return

        reply = "Results:\n\n"

        for i, r in enumerate(results, 1):
            reply += f"{i}. {r['title']}\n"
            reply += f"Artist: {r['channel']}\n"
            reply += f"Duration: {r['duration']}\n"
            reply += f"{r['url']}\n\n"

        await message.reply(reply)
        return


    # -------------------
    # download
    # -------------------

    if "soundcloud.com" in text:

        await message.reply("Downloading...")

        try:

            file, info = download_track(text)

            title = info.get("title", "Track")
            uploader = info.get("uploader", "Unknown")

            caption = f"{title}\nby {uploader}"

            await message.reply_audio(file, caption=caption)

        except Exception as e:

            await message.reply(f"Download failed:\n{str(e)}")

        return


    # -------------------
    # help
    # -------------------

    await message.reply(
        "SoundCloud Bot\n\n"
        "/search song name\n"
        "or send a SoundCloud link"
    )


# -----------------------
# Run
# -----------------------

if __name__ == "__main__":
    bot.run()
