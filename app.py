from flask import Flask, request
import requests
import urllib.parse
import os

# --- توکن و آدرس‌های API بله ---
TOKEN = "1011430416:0-QaVTm8WjXtmVRcZKFvhfr_OGOL6OldiZs"
BALE_API = f"https://tapi.bale.ai/bot{TOKEN}"
API_MSG = f"{BALE_API}/sendMessage"
API_FILE = f"{BALE_API}/sendDocument"
API_PHOTO = f"{BALE_API}/sendPhoto"

app = Flask(__name__)

# ==========================================
# توابع مربوط به API ویکی‌پدیا (زبان فارسی)
# ==========================================

def search_wikipedia(query):
    """جستجوی عبارت در ویکی‌پدیای فارسی و برگرداندن 5 نتیجه اول"""
    url = f"https://fa.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&utf8=&format=json"
    response = requests.get(url).json()
    return response.get('query', {}).get('search', [])[:5]

def get_wiki_summary(title):
    """گرفتن خلاصه و عکس مقاله از ویکی‌پدیا"""
    title_encoded = urllib.parse.quote(title)
    url = f"https://fa.wikipedia.org/api/rest_v1/page/summary/{title_encoded}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def download_wiki_pdf(title, filepath):
    """دانلود PDF کامل مقاله مستقیما از سرور ویکی‌پدیا"""
    title_encoded = urllib.parse.quote(title)
    url = f"https://fa.wikipedia.org/api/rest_v1/page/pdf/{title_encoded}"
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    return False


# ==========================================
# توابع ارسال پیام در پیام‌رسان بله
# ==========================================

def send_msg(chat_id, txt, reply_markup=None):
    payload = {"chat_id": chat_id, "text": txt}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(API_MSG, json=payload)

def send_photo(chat_id, photo_url, caption="", reply_markup=None):
    payload = {"chat_id": chat_id, "photo": photo_url, "caption": caption}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(API_PHOTO, json=payload)

def send_file(chat_id, path, caption=""):
    with open(path, "rb") as f:
        requests.post(API_FILE, data={"chat_id": chat_id, "caption": caption}, files={"document": f})


# ==========================================
# هندلر اصلی وب‌هوک
# ==========================================

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.json

    # --- مدیریت دکمه‌های شیشه‌ای (Callback Queries) ---
    if "callback_query" in update:
        callback = update["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        data = callback["data"]

        # اگر کاربر روی یکی از نتایج جستجو کلیک کرد (برای دیدن خلاصه)
        if data.startswith("sum|"):
            title = data.split("|")[1]
            wiki_data = get_wiki_summary(title)
            
            if wiki_data:
                extract = wiki_data.get("extract", "خلاصه‌ای برای این مقاله یافت نشد.")
                # ساخت دکمه دانلود PDF
                markup = {
                    "inline_keyboard": [
                        [{"text": "📥 دانلود فایل PDF کامل مقاله", "callback_data": f"pdf|{title}"}]
                    ]
                }
                
                # اگر مقاله عکس داشت، عکس را با کپشن می‌فرستیم، وگرنه فقط متن
                if "thumbnail" in wiki_data:
                    photo_url = wiki_data["thumbnail"]["source"]
                    send_photo(chat_id, photo_url, caption=f"**{title}**\n\n{extract}", reply_markup=markup)
                else:
                    send_msg(chat_id, f"**{title}**\n\n{extract}", reply_markup=markup)
            else:
                send_msg(chat_id, "❌ خطایی در دریافت اطلاعات رخ داد.")

        # اگر کاربر روی دکمه دانلود PDF کلیک کرد
        elif data.startswith("pdf|"):
            title = data.split("|")[1]
            send_msg(chat_id, "⏳ در حال آماده‌سازی و دانلود فایل PDF از ویکی‌پدیا... لطفا کمی صبر کنید.")
            
            pdf_path = f"{title}.pdf"
            if download_wiki_pdf(title, pdf_path):
                send_file(chat_id, pdf_path, caption=f"📄 فایل PDF مقاله: {title}")
                os.remove(pdf_path) # پاک کردن فایل از سرور بعد از ارسال
            else:
                send_msg(chat_id, "❌ متاسفانه تولید PDF برای این مقاله با خطا مواجه شد.")

        return "ok"

    # --- مدیریت پیام‌های متنی ---
    if "message" not in update:
        return "ok"

    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "")

    # پیام شروع (Start)
    if text == "/start":
        welcome_text = (
            "👋 سلام! به ربات **جستجوگر ویکی‌پدیا** خوش آمدید.\n\n"
            "🔍 کافیست کلمه یا موضوعی که دنبالش هستید را برای من بفرستید تا آن را در ویکی‌پدیای فارسی جستجو کنم."
        )
        send_msg(chat_id, welcome_text)
        return "ok"

    # جستجوی متن ارسال شده توسط کاربر
    send_msg(chat_id, f"🔍 در حال جستجو برای «{text}»...")
    results = search_wikipedia(text)

    if not results:
        send_msg(chat_id, "❌ نتیجه‌ای در ویکی‌پدیای فارسی یافت نشد. کلمه دیگری را امتحان کنید.")
        return "ok"

    # ساخت دکمه‌های شیشه‌ای برای نتایج جستجو
    keyboard = []
    for res in results:
        title = res["title"]
        # محدودیت طول کالبک دیتا در تلگرام/بله معمولا 64 بایت است
        keyboard.append([{"text": title, "callback_data": f"sum|{title}"[:60]}])
    
    markup = {"inline_keyboard": keyboard}
    send_msg(chat_id, "✅ نتایج زیر یافت شد. برای مشاهده خلاصه، روی یکی از موارد کلیک کنید:", reply_markup=markup)

    return "ok"


if __name__ == "__main__":
    app.run(port=5000, debug=True)
