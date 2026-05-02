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
# Browser-like headers (Enhanced to prevent 403)
# -----------------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "DNT": "1"
}


# -----------------------------
# Fetch page
# -----------------------------
async def fetch_page(url):
    # Added timeout to prevent hanging
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=15.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text


# -----------------------------
# Inline assets
# -----------------------------
async def inline_assets(html, base_url):

    soup = BeautifulSoup(html, "lxml")

    # Using the same enhanced headers and timeout for assets
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=10.0) as client:

        # CSS
        for link in soup.find_all("link", rel="stylesheet"):
            href = link.get("href")
            if not href:
                continue

            asset_url = urljoin(base_url, href)

            try:
                r = await client.get(asset_url)
                if r.status_code == 200:
                    style = soup.new_tag("style")
                    style.string = r.text
                    link.replace_with(style)
            except Exception:
                pass

        # JS
        for script in soup.find_all("script"):
            src = script.get("src")
            if not src:
                continue

            asset_url = urljoin(base_url, src)

            try:
                r = await client.get(asset_url)
                if r.status_code == 200:
                    new_script = soup.new_tag("script")
                    new_script.string = r.text
                    script.replace_with(new_script)
            except Exception:
                pass

        # Images
        for img in soup.find_all("img"):
            src = img.get("src")
            if not src:
                continue

            # Skip already encoded images
            if src.startswith("data:image"):
                continue

            asset_url = urljoin(base_url, src)

            try:
                r = await client.get(asset_url)
                if r.status_code == 200:
                    # Try to guess mime type from URL or fallback to png
                    ext = asset_url.split('.')[-1].lower()
                    mime_type = "png"
                    if ext in ['jpg', 'jpeg']: mime_type = "jpeg"
                    elif ext == 'svg': mime_type = "svg+xml"
                    elif ext == 'gif': mime_type = "gif"
                    elif ext == 'webp': mime_type = "webp"
                    
                    encoded = base64.b64encode(r.content).decode()
                    img["src"] = f"data:image/{mime_type};base64,{encoded}"
            except Exception:
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
        
        # Clean up the file after sending
        if os.path.exists(filename):
            os.remove(filename)

    except httpx.HTTPStatusError as e:
        await message.reply(f"HTTP Error: {e.response.status_code} - Could not fetch the page. Some sites block automated requests.")
    except Exception as e:
        await message.reply(f"Error:\n{str(e)}")


# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    bot.run()
