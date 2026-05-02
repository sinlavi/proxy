import yt_dlp
from balethon import Client

BALE_TOKEN = "1011430416:0-QaVTm8WjXtmVRcZKFvhfr_OGOL6OldiZs"

bot = Client(BALE_TOKEN)


def get_direct_audio_url(url: str):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    # بهترین لینک صوتی را پیدا کن
    for f in info["formats"]:
        if f.get("acodec") != "none" and f.get("url"):
            return f["url"], info

    raise ValueError("Direct audio URL not found")


@bot.on_message()
async def handler(message):
    if not message.text:
        return

    text = message.text.strip()

    if "soundcloud.com" in text:
        await message.reply("Generating direct audio URL...")

        try:
            audio_url, info = get_direct_audio_url(text)

            caption = f"{info.get('title','Track')}\nby {info.get('uploader','Unknown')}"

            # ارسال مستقیم URL
            await message.reply_audio(
                audio=audio_url,
                caption=caption
            )

        except Exception as e:
            await message.reply(f"Error:\n{e}")


if __name__ == "__main__":
    bot.run()
