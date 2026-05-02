import os
import yt_dlp
from balethon import Client

BALE_TOKEN = "1011430416:0-QaVTm8WjXtmVRcZKFvhfr_OGOL6OldiZs"

if not BALE_TOKEN:
    raise ValueError("BALE_TOKEN not set")

bot = Client(BALE_TOKEN)


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

    if not filename.endswith(".mp3"):
        filename = filename.rsplit(".", 1)[0] + ".mp3"

    return filename, info


@bot.on_message()
async def handler(message):

    if not message.text:
        return

    text = message.text.strip()

    if "soundcloud.com" in text:

        await message.reply("Downloading...")

        try:
            filename, info = download_track(text)

            caption = f"{info.get('title','Track')}\nby {info.get('uploader','Unknown')}"

            await message.reply_audio(filename, caption=caption)

            # ✅ delete file after sending
            if os.path.exists(filename):
                os.remove(filename)

        except Exception as e:
            await message.reply(f"Error:\n{e}")


if __name__ == "__main__":
    bot.run()
