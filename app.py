import os
import yt_dlp
import asyncio
from aiohttp import web
from balethon import Client

BALE_TOKEN = "1011430416:0-QaVTm8WjXtmVRcZKFvhfr_OGOL6OldiZs"

bot = Client(BALE_TOKEN)

# A simple static file server for MP3 files
app = web.Application()
routes = web.RouteTableDef()

@routes.get("/{filename}")
async def serve_file(request):
    filename = request.match_info["filename"]
    path = f"./{filename}"
    if os.path.exists(path):
        return web.FileResponse(path)
    return web.Response(status=404, text="File not found")

app.add_routes(routes)

def start_server():
    runner = web.AppRunner(app)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    loop.run_until_complete(site.start())
    print("HTTP file server running on port 8080...")


def download_mp3_sync(url: str):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "audio.%(ext)s",
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


async def download_mp3(url: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, download_mp3_sync, url)


@bot.on_message()
async def handler(message):
    if not message.text:
        return

    text = message.text.strip()

    if "soundcloud.com" in text:
        await message.reply("Downloading as MP3...")

        try:
            filename, info = await download_mp3(text)

            # Ensure file exists
            if not os.path.exists(filename):
                await message.reply("Error: MP3 not created.")
                return

            # Build public URL
            public_url = f"http://your-server-ip:8080/{filename}"

            caption = f"{info.get('title','Track')}\nby {info.get('uploader','Unknown')}"

            # Send MP3 by URL
            await message.reply_audio(
                audio=public_url,
                caption=caption
            )

            # Optional: delete after sending
            # os.remove(filename)

        except Exception as e:
            await message.reply(f"Error:\n{e}")


if __name__ == "__main__":
    start_server()  # Start the MP3 HTTP server
    bot.run()
