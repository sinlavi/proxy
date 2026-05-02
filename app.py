import os
import base64
import httpx
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from balethon import Client

BALE_TOKEN = "1011430416:0-QaVTm8WjXtmVRcZKFvhfr_OGOL6OldiZs"

bot = Client(BALE_TOKEN)

# -----------------------------
# Real browser headers
# -----------------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.91 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# -----------------------------
# Shared client (keeps cookies)
# -----------------------------
client = httpx.AsyncClient(
    headers=HEADERS,
    follow_redirects=True,
    http2=True,
    timeout=30
)

# -----------------------------
# Fetch page
# -----------------------------
async def fetch_page(url):
    r = await client.get(url)
    r.raise_for_status()
    return r.text


# -----------------------------
# Inline assets
# -----------------------------
async def inline_assets(html, base_url):

    soup = BeautifulSoup(html, "lxml")

    # CSS
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href")
        if not href:
            continue

        asset_url = urljoin(base_url, href)

        try:
            r = await client.get(asset_url, headers={"Referer": base_url})
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
            r = await client.get(asset_url, headers={"Referer": base_url})
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
            r = await client.get(asset_url, headers={"Referer": base_url})
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

    url = message.text.strip()

    if not url.startswith("http"):
        await message.reply("Send a URL.")
        return

    await message.reply("Downloading page...")

    try:
        html = await fetch_page(url)
        final_html = await inline_assets(html, url)

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
