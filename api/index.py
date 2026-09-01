from flask import Flask, request, jsonify
import requests
import json
import base64
import os

app = Flask(__name__)

# جلب المتغيرات من بيئة Vercel
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER", "husszzzz")
REPO_NAME = os.getenv("REPO_NAME", "special-octo-engine")
FILE_PATH = "data.json"

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# 1. دالة لقراءة ملف JSON من GitHub API
def get_github_json():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        content = res.json()
        sha = content['sha']  # مطلوب للتعديل لاحقاً
        decoded = base64.b64decode(content['content']).decode('utf-8')
        return json.loads(decoded), sha
    return {}, None

# 2. دالة لتحديث وتعديل ملف JSON على GitHub API
def update_github_json(data, sha, commit_message="تحديث البيانات بواسطة البوت"):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    content_str = json.dumps(data, ensure_ascii=False, indent=2)
    encoded = base64.b64encode(content_str.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": commit_message,
        "content": encoded,
        "sha": sha
    }
    res = requests.put(url, headers=headers, json=payload)
    return res.status_code == 200

# 3. دالة لإرسال رسالة لتليجرام
def send_telegram_message(chat_id, text):
    requests.post(f"{TELEGRAM_API}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    })

# نقطة الـ Webhook التي يستدعيها تليجرام
@app.route('/', methods=['POST', 'GET'])
@app.route('/api', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return "البوت يعمل بنجاح!"

    update = request.get_json()
    if not update or "message" not in update:
        return jsonify({"status": "ok"})
    
    message = update["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    # الأوامر
    if text == "/start":
        send_telegram_message(chat_id, "👋 أهلاً بك! البوت يعمل 24/7 عبر Vercel ويقوم بالحفظ في GitHub مباشرة.")

    # مثال على التعديل والحفظ في ملف JSON
    elif text.startswith("/save "):
        new_value = text.replace("/save ", "").strip()
        data, sha = get_github_json()
        
        # إضافة أو تعديل قيمة
        data["last_message"] = new_value
        
        if update_github_json(data, sha, f"Bot Update: {new_value}"):
            send_telegram_message(chat_id, f"✅ تم حفظ القيمة بنجاح في `data.json` على GitHub:\n`{new_value}`")
        else:
            send_telegram_message(chat_id, "❌ حدث خطأ أثناء التحديث على GitHub.")

    # قراءة البيانات المحفوظة
    elif text == "/read":
        data, _ = get_github_json()
        val = data.get("last_message", "لا توجد بيانات محفوظة بعد.")
        send_telegram_message(chat_id, f"📄 القيمة المحفوظة حالياً في JSON:\n`{val}`")

    return jsonify({"status": "ok"})
