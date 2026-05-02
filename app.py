from flask import Flask, request
import requests
import os
import zipfile
from crawler import crawl_single_page

TOKEN = "1011430416:0-QaVTm8WjXtmVRcZKFvhfr_OGOL6OldiZs"
API_FILE = f"https://tapi.bale.ai/bot{TOKEN}/sendDocument"
API_MSG = f"https://tapi.bale.ai/bot{TOKEN}/sendMessage"

app = Flask(__name__)

def zip_folder(folder, zipname):
    with zipfile.ZipFile(zipname, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(folder):
            for f in files:
                path = os.path.join(root, f)
                z.write(path, os.path.relpath(path, folder))


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.json
    if "message" not in update:
        return "ok"

    chat = update["message"]["chat"]["id"]
    text = update["message"].get("text", "")

    if not text.startswith("http"):
        send_msg(chat, "Send me a link to crawl:")
        return "ok"

    url = text.strip()

    folder = "page_data"
    zip_name = "page.zip"

    # clean old output
    if os.path.exists(folder):
        for f in os.listdir(folder):
            os.remove(os.path.join(folder, f))
    else:
        os.makedirs(folder)

    # crawl
    index_path = crawl_single_page(url, folder)

    # zip
    zip_folder(folder, zip_name)

    # send
    send_file(chat, zip_name, caption="Here is the crawled page (open index.html)")

    return "ok"


def send_msg(chat_id, txt):
    requests.post(API_MSG, json={"chat_id": chat_id, "text": txt})


def send_file(chat_id, path, caption=""):
    with open(path, "rb") as f:
        requests.post(API_FILE, data={"chat_id": chat_id, "caption": caption},
                      files={"document": f})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
