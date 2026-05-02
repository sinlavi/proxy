import os
import base64
import httpx
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from balethon import Client

BALE_TOKEN = "1011430416:0-QaVTm8WjXtmVRcZKFvhfr_OGOL6OldiZs"

if not BALE_TOKEN:
    raise ValueError("BALE_TOKEN not set")

bot = Client(BALE_TOKEN)


# -----------------------------
# Browser-like headers
# -----------------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "*/*"
}


# -----------------------------
# Fetch page
# -----------------------------
async def fetch_page(url):
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text


# -----------------------------
# Inline assets
# -----------------------------
async def inline_assets(html, base_url):

    soup = BeautifulSoup(html, "lxml")

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:

        # CSS
        for link in soup.find_all("link", rel="stylesheet"):
            href = link.get("href")
            if not href:
                continue

            asset_url = urljoin(base_url, href)

            try:
                r = await client.get(asset_url)
                style = soup.new_tag("style")
                style.string = r.text
                link.replace_with(style)
            except:
                pass

        # JS
        for script in soup.find_all("script"):
            src = script.get("src")
            if not src:
                continue

            asset_url = urljoin(base_url, src)

            try:
                r = await client.get(asset_url)
                new_script = soup.new_tag("script")
                new_script.string = r.text
                script.replace_with(new_script)
            except:
                pass

        # Images
        for img in soup.find_all("img"):
            src = img.get("src")
            if not src:
                continue

            asset_url = urljoin(base_url, src)

            try:
                r = await client.get(asset_url)
                encoded = base64.b64encode(r.content).decode()
                img["src"] = f"data:image;base64,{encoded}"
            except:
                pass

    return str(soup)


# -----------------------------
# Bale handler
# -----------------------------
@bot.on_message()
async def handle(message):

    if not message.text:
        return

    text = message.text.strip()

    if not text.startswith("http"):
        await message.reply("Send a URL.")
        return

    await message.reply("Downloading page...")

    try:
        html = await fetch_page(text)
        final_html = await inline_assets(html, text)

        filename = "page.html"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_html)

        await message.reply_document(filename)

    except Exception as e:
        await message.reply(f"Error:\n{str(e)}")


# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    bot.run()
