import os
import base64
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from balethon import Client
from curl_cffi.requests import AsyncSession

BALE_TOKEN = "1011430416:0-QaVTm8WjXtmVRcZKFvhfr_OGOL6OldiZs"

if not BALE_TOKEN:
    raise ValueError("BALE_TOKEN not set")

bot = Client(BALE_TOKEN)

# -----------------------------
# Fetch page with Browser Impersonation
# -----------------------------
async def fetch_page(url):
    # impersonate="chrome124" باعث می‌شود سرور کاملاً فکر کند درخواست از کروم واقعی می‌آید
    async with AsyncSession(impersonate="chrome124", timeout=15.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text


# -----------------------------
# Inline assets
# -----------------------------
async def inline_assets(html, base_url):
    soup = BeautifulSoup(html, "lxml")
    
    headers = {"Referer": base_url}

    async with AsyncSession(impersonate="chrome124", timeout=10.0, headers=headers) as client:

        # CSS
        for link in soup.find_all("link", rel="stylesheet"):
            href = link.get("href")
            if not href: continue
            asset_url = urljoin(base_url, href)
            try:
                r = await client.get(asset_url)
                if r.status_code == 200:
                    style = soup.new_tag("style")
                    style.string = r.text
                    link.replace_with(style)
            except: pass

        # JS
        for script in soup.find_all("script"):
            src = script.get("src")
            if not src: continue
            asset_url = urljoin(base_url, src)
            try:
                r = await client.get(asset_url)
                if r.status_code == 200:
                    new_script = soup.new_tag("script")
                    new_script.string = r.text
                    script.replace_with(new_script)
            except: pass

        # Images
        for img in soup.find_all("img"):
            src = img.get("src")
            if not src: continue
            asset_url = urljoin(base_url, src)
            try:
                r = await client.get(asset_url)
                if r.status_code == 200:
                    content_type = r.headers.get("content-type", "image/jpeg")
                    encoded = base64.b64encode(r.content).decode()
                    img["src"] = f"data:{content_type};base64,{encoded}"
            except: pass

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
        await message.reply("Send a valid URL starting with http/https.")
        return

    wait_msg = await message.reply("Downloading page... Please wait.")
    filename = f"page_{message.chat.id}.html"
    
    try:
        html = await fetch_page(text)
        final_html = await inline_assets(html, text)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_html)

        await message.reply_document(filename)
        await wait_msg.delete()

    except Exception as e:
        await message.reply(f"Error:\n{str(e)}")
        
    finally:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    bot.run()
