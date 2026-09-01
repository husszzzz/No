import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") # توكن حسابك في جيت هب (PAT)
REPO_OWNER = os.getenv("REPO_OWNER", "husszzzz")
REPO_NAME = os.getenv("REPO_NAME", "special-octo-engine")

# حفظ مؤقت للملفات بالذاكرة (يجب إرسال الملفات بشكل متتالي وبدون تأخير طويل)
sessions = {}

def send_message(chat_id, text):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": text})

def get_file_path(file_id):
    res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
    return res['result']['file_path']

def trigger_github_action(p12_path, prov_path, password, chat_id):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/sign.yml/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "ref": "main",
        "inputs": {
            "p12_path": p12_path,
            "prov_path": prov_path,
            "password": password,
            "chat_id": str(chat_id)
        }
    }
    requests.post(url, headers=headers, json=data)

@app.route('/api', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return "Vercel Bot is Running!"

    update = request.get_json()
    if not update or "message" not in update:
        return jsonify({"status": "ok"})

    chat_id = update["message"]["chat"]["id"]
    if chat_id not in sessions:
        sessions[chat_id] = {}

    if "text" in update["message"]:
        text = update["message"]["text"]
        if text == "/start":
            sessions[chat_id] = {}
            send_message(chat_id, "👋 أهلاً بك! أرسل ملف الشهادة `.p12` أولاً:")
        elif "p12_path" in sessions[chat_id] and "prov_path" in sessions[chat_id] and "password" not in sessions[chat_id]:
            # استلام الباسورد وبدء العملية
            sessions[chat_id]["password"] = text
            send_message(chat_id, "⚙️ تم استلام البيانات! جاري تشغيل سيرفرات GitHub للتوقيع (قد يستغرق الأمر دقيقتين)، سيصلك رابط التثبيت قريباً...")
            trigger_github_action(sessions[chat_id]["p12_path"], sessions[chat_id]["prov_path"], text, chat_id)
            sessions[chat_id] = {} # تفريغ الجلسة

    elif "document" in update["message"]:
        doc = update["message"]["document"]
        file_name = doc.get("file_name", "")
        file_id = doc["file_id"]

        if file_name.endswith(".p12"):
            sessions[chat_id]["p12_path"] = get_file_path(file_id)
            send_message(chat_id, "✅ تم استلام الشهادة. أرسل الآن ملف `.mobileprovision`:")
        elif file_name.endswith(".mobileprovision"):
            sessions[chat_id]["prov_path"] = get_file_path(file_id)
            send_message(chat_id, "🔐 أرسل كلمة مرور الشهادة:")

    return jsonify({"status": "ok"})
