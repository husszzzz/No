import os
import json
import time
import base64
import threading
import requests
from flask import Flask, request, abort
from telebot import TeleBot, types

# =======================================================
# 1. الإعدادات والمتغيرات السرية (من إعدادات Vercel)
# =======================================================
BOT_TOKEN = os.getenv('BOT_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
ADMIN_ID = 6799794121  # الأيدي الخاص بك
REPO_OWNER = "husszzzz"
REPO_NAME = "No"

bot = TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False)
app = Flask(__name__)

# =======================================================
# 2. نظام الرموز التعبيرية المتحركة (Custom Emojis)
# =======================================================
def custom_emoji(fallback, emoji_id):
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

E_CROWN = custom_emoji("👑", "6008233706039284019")
E_MONEY = custom_emoji("💰", "5891198677606732755")
E_FIRE = custom_emoji("🔥", "5967522716062847679")
E_DIAMOND = custom_emoji("💎", "5803175856905917502")
E_CHECK = custom_emoji("✅", "5447448489149625830")
E_GEAR = custom_emoji("⚙️", "5445347129155419150")
E_SAD = custom_emoji("😞", "5926940334587122131")
E_BELL = custom_emoji("🔔", "5888974760720732797")
E_BOLT = custom_emoji("⚡", "5931730919634244412")
E_WAIT = custom_emoji("⏳", "5926940334587122131") # يمكن تعديله لاحقاً

# =======================================================
# 3. نظام قاعدة البيانات السحابية (عبر GitHub API)
# =======================================================
# هذا النظام يحل مشكلة حذف الملفات في Vercel، حيث يقوم بحفظها في المستودع
class GitHubDatabase:
    def __init__(self, filename="data.json"):
        self.filename = filename
        self.url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{self.filename}"
        self.headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

    def load(self):
        try:
            res = requests.get(self.url, headers=self.headers)
            if res.status_code == 200:
                content = base64.b64decode(res.json()['content']).decode('utf-8')
                return json.loads(content), res.json()['sha']
            else:
                return {"users": [], "blocked": [], "store_apps": [], "certs": {}, "states": {}}, None
        except Exception as e:
            return {"users": [], "blocked": [], "store_apps": [], "certs": {}, "states": {}}, None

    def save(self, data, sha):
        try:
            content = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8')).decode('utf-8')
            payload = {
                "message": "Auto-update database by Bot",
                "content": content,
                "branch": "main"
            }
            if sha:
                payload["sha"] = sha
            requests.put(self.url, headers=self.headers, json=payload)
        except Exception as e:
            print(f"Error saving DB: {e}")

db_manager = GitHubDatabase()

# =======================================================
# 4. دوال الاتصال الأساسية (GitHub Actions & Webhooks)
# =======================================================
def trigger_github_workflow(chat_id, p12_path, prov_path, password):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/sign.yml/dispatches"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "ref": "main",
        "inputs": {
            "p12_path": p12_path,
            "prov_path": prov_path,
            "password": password,
            "chat_id": str(chat_id)
        }
    }
    requests.post(url, headers=headers, json=payload)

def process_fake_loading(chat_id, message_id, p12, prov, pwd):
    percentages = [15, 30, 45, 60, 85, 100]
    for p in percentages:
        time.sleep(1.2)
        try:
            if p < 100:
                bot.edit_message_text(f"جاري سحب وتوقيع التطبيق... {p}% {E_WAIT}", chat_id, message_id)
            else:
                bot.edit_message_text(f"{E_GEAR} جاري تهيئة الرابط... يرجى الانتظار.", chat_id, message_id)
                trigger_github_workflow(chat_id, p12, prov, pwd)
        except:
            pass

# =======================================================
# 5. دوال الترحيب ولوحات التحكم (UI/UX)
# =======================================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    db, sha = db_manager.load()
    
    # الإشعارات والتسجيل
    if user_id not in db["users"]:
        db["users"].append(user_id)
        db_manager.save(db, sha)
        bot.send_message(ADMIN_ID, f"{E_BELL} <b>دخول عضو جديد!</b>\nالاسم: {message.from_user.first_name}\nالأيدي: <code>{user_id}</code>")

    text = f"أهلاً بك في <b>Hassany Store</b> {E_CROWN}\n\nالمتجر الأول والحصري لتوقيع التطبيقات الاحترافية {E_FIRE}\nقم باختيار الخدمة المطلوبة من القائمة أدناه {E_DIAMOND}:"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_sign = types.InlineKeyboardButton(f"توقيع تطبيق {E_CHECK}", callback_data="sign_app_direct")
    btn_store = types.InlineKeyboardButton(f"متجر التطبيقات 📱", web_app=types.WebAppInfo("https://no-bznl.vercel.app"))
    btn_certs = types.InlineKeyboardButton(f"إدارة الشهادات 🪪", callback_data="certs_menu")
    
    markup.add(btn_sign, btn_store)
    markup.add(btn_certs)
    
    # صلاحيات الأدمن
    if int(user_id) == ADMIN_ID:
        markup.add(types.InlineKeyboardButton(f"لوحة تحكم الإدارة {E_GEAR}", callback_data="admin_panel"))

    bot.send_message(user_id, text, reply_markup=markup)

# =======================================================
# 6. معالج الأزرار الشفافة (Callbacks Handler)
# =======================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = str(call.from_user.id)
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    db, sha = db_manager.load()

    # ---- نظام التوقيع المباشر ----
    if call.data == "sign_app_direct":
        if user_id not in db["certs"] or not db["certs"][user_id].get("default"):
            bot.answer_callback_query(call.id, "⚠️ يجب تعيين شهادة أساسية من قسم الشهادات أولاً!", show_alert=True)
            return
        
        cert = db["certs"][user_id]["default"]
        msg = bot.edit_message_text(f"جاري الاتصال بخوادم Hassany VIP... {E_BOLT}", chat_id, msg_id)
        # تشغيل في الخلفية لعدم إيقاف Vercel
        threading.Thread(target=process_fake_loading, args=(chat_id, msg.message_id, cert["p12"], cert["prov"], cert["pwd"])).start()

    # ---- نظام إدارة الشهادات ----
    elif call.data == "certs_menu":
        text = f"<b>قسم الشهادات الخاصة بك</b> 🪪\n\nقم برفع شهادتك لتوقيع التطبيقات مباشرة:"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(f"إضافة شهادة جديدة ➕", callback_data="cert_add"))
        
        if user_id in db["certs"] and db["certs"][user_id].get("default"):
            cert_name = db["certs"][user_id]["default"]["name"]
            text += f"\n\nالشهادة الأساسية الحالية: <b>{cert_name}</b> {E_CHECK}"
            markup.add(types.InlineKeyboardButton(f"حذف الشهادة الأساسية 🗑️", callback_data="cert_delete"))
            
        markup.add(types.InlineKeyboardButton(f"رجوع 🔙", callback_data="back_home"))
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup)

    elif call.data == "cert_add":
        db["states"][user_id] = {"step": "WAITING_CERT_NAME"}
        db_manager.save(db, sha)
        bot.edit_message_text("أرسل الآن <b>اسم الشهادة</b> (مثال: شهادتي الأساسية):", chat_id, msg_id)

    elif call.data == "cert_delete":
        if user_id in db["certs"]:
            del db["certs"][user_id]["default"]
            db_manager.save(db, sha)
            bot.answer_callback_query(call.id, "تم حذف الشهادة الأساسية بنجاح ✅", show_alert=True)
            bot.delete_message(chat_id, msg_id)
            send_welcome(call.message)

    # ---- لوحة تحكم الأدمن الشاملة ----
    elif call.data == "admin_panel" and int(user_id) == ADMIN_ID:
        users_count = len(db.get("users", []))
        apps_count = len(db.get("store_apps", []))
        
        text = f"<b>لوحة التحكم الاحترافية</b> {E_CROWN}\n\n"
        text += f"👥 إجمالي المستخدمين: <b>{users_count}</b>\n"
        text += f"📱 تطبيقات المتجر: <b>{apps_count}</b>\n\n"
        text += "اختر الإجراء المطلوب:"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("توقيع البليارد 🎱", callback_data="admin_billiard"))
        markup.add(types.InlineKeyboardButton("إضافة تطبيق 📥", callback_data="admin_add_app"),
                   types.InlineKeyboardButton("استيراد JSON 📂", callback_data="admin_import_json"))
        markup.add(types.InlineKeyboardButton("إرسال إذاعة 📢", callback_data="admin_broadcast"))
        markup.add(types.InlineKeyboardButton("رجوع 🔙", callback_data="back_home"))
        
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup)

    # --- إجراءات الأدمن ---
    elif call.data == "admin_billiard":
        db["states"][user_id] = {"step": "ADMIN_BILLIARD_P12"}
        db_manager.save(db, sha)
        bot.edit_message_text("أرسل ملف الشهادة بصيغة <b>.p12</b> لتوقيع البليارد 🎱:", chat_id, msg_id)

    elif call.data == "admin_add_app":
        db["states"][user_id] = {"step": "ADMIN_ADD_APP_NAME"}
        db_manager.save(db, sha)
        bot.edit_message_text("أرسل <b>اسم التطبيق</b> الجديد:", chat_id, msg_id)

    elif call.data == "admin_import_json":
        db["states"][user_id] = {"step": "ADMIN_IMPORT_JSON"}
        db_manager.save(db, sha)
        bot.edit_message_text("أرسل <b>رابط JSON</b> لاستيراد التطبيقات للمتجر:", chat_id, msg_id)

    elif call.data == "back_home":
        bot.delete_message(chat_id, msg_id)
        send_welcome(call.message)

# =======================================================
# 7. نظام استقبال البيانات المتسلسل (State Machine)
# =======================================================
@bot.message_handler(content_types=['text', 'document'])
def handle_user_input(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    db, sha = db_manager.load()
    
    if user_id not in db.get("states", {}):
        return

    state_info = db["states"][user_id]
    step = state_info.get("step")

    # ---- خطوات إضافة شهادة المستخدم ----
    if step == "WAITING_CERT_NAME" and message.text:
        db["states"][user_id]["cert_name"] = message.text
        db["states"][user_id]["step"] = "WAITING_CERT_P12"
        db_manager.save(db, sha)
        bot.send_message(chat_id, f"تم حفظ الاسم {E_CHECK}\nالآن أرسل ملف الشهادة <b>.p12</b>:")

    elif step == "WAITING_CERT_P12" and message.document:
        if message.document.file_name.endswith('.p12'):
            db["states"][user_id]["p12"] = message.document.file_id
            db["states"][user_id]["step"] = "WAITING_CERT_PROV"
            db_manager.save(db, sha)
            bot.send_message(chat_id, f"تم الاستلام {E_CHECK}\nالآن أرسل ملف <b>.mobileprovision</b>:")
        else:
            bot.send_message(chat_id, "يرجى إرسال ملف بصيغة .p12 حصراً!")

    elif step == "WAITING_CERT_PROV" and message.document:
        if message.document.file_name.endswith('.mobileprovision'):
            db["states"][user_id]["prov"] = message.document.file_id
            db["states"][user_id]["step"] = "WAITING_CERT_PWD"
            db_manager.save(db, sha)
            bot.send_message(chat_id, f"تم الاستلام {E_CHECK}\nالآن أرسل <b>كلمة مرور الشهادة</b>:")
        else:
            bot.send_message(chat_id, "يرجى إرسال ملف بصيغة .mobileprovision حصراً!")

    elif step == "WAITING_CERT_PWD" and message.text:
        if user_id not in db["certs"]:
            db["certs"][user_id] = {}
            
        db["certs"][user_id]["default"] = {
            "name": db["states"][user_id]["cert_name"],
            "p12": db["states"][user_id]["p12"],
            "prov": db["states"][user_id]["prov"],
            "pwd": message.text
        }
        del db["states"][user_id]
        db_manager.save(db, sha)
        bot.send_message(chat_id, f"تم حفظ الشهادة وتفعيلها كـ <b>أساسية</b> بنجاح {E_FIRE}")

    # ---- خطوات توقيع البليارد للأدمن ----
    elif step == "ADMIN_BILLIARD_P12" and message.document:
        db["states"][user_id]["p12"] = message.document.file_id
        db["states"][user_id]["step"] = "ADMIN_BILLIARD_PROV"
        db_manager.save(db, sha)
        bot.send_message(chat_id, "أرسل الآن ملف <b>.mobileprovision</b>:")

    elif step == "ADMIN_BILLIARD_PROV" and message.document:
        db["states"][user_id]["prov"] = message.document.file_id
        db["states"][user_id]["step"] = "ADMIN_BILLIARD_PWD"
        db_manager.save(db, sha)
        bot.send_message(chat_id, "أرسل <b>كلمة المرور</b>:")

    elif step == "ADMIN_BILLIARD_PWD" and message.text:
        pwd = message.text
        p12 = db["states"][user_id]["p12"]
        prov = db["states"][user_id]["prov"]
        del db["states"][user_id]
        db_manager.save(db, sha)
        
        msg = bot.send_message(chat_id, f"بدء توقيع البليارد... {E_GEAR}")
        threading.Thread(target=process_fake_loading, args=(chat_id, msg.message_id, p12, prov, pwd)).start()

    # ---- خطوات إضافة تطبيق JSON ----
    elif step == "ADMIN_IMPORT_JSON" and message.text:
        try:
            bot.send_message(chat_id, f"جاري استيراد التطبيقات... {E_WAIT}")
            response = requests.get(message.text)
            apps = response.json()
            count = 0
            for app in apps:
                name = app.get("name") or app.get("title", "تطبيق بدون اسم")
                url = app.get("downloadURL") or app.get("ipa_url", "")
                img = app.get("iconURL") or app.get("image", "")
                if url:
                    db["store_apps"].append({"name": name, "url": url, "image": img, "category": "جديد"})
                    count += 1
            del db["states"][user_id]
            db_manager.save(db, sha)
            bot.send_message(chat_id, f"تم استيراد {count} تطبيق بنجاح وتم تحديث المتجر {E_CHECK}")
        except Exception as e:
            bot.send_message(chat_id, f"حدث خطأ أثناء الاستيراد {E_SAD}\nتأكد من الرابط.")
            del db["states"][user_id]
            db_manager.save(db, sha)

# =======================================================
# 8. إعدادات خادم Vercel (Flask Webhook)
# =======================================================
@app.route('/', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        try:
            update = types.Update.de_json(request.get_json(force=True))
            bot.process_new_updates([update])
            return "OK", 200
        except Exception as e:
            return "ERROR", 500
    else:
        # إعداد الويب هوك تلقائياً عند فتح الرابط
        webhook_url = f"https://no-bznl.vercel.app/" # تأكد من تحديث هذا الرابط
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        return f"<h1>Hassany Store Bot is Running! 🚀</h1><p>Webhook connected to: {webhook_url}</p>", 200

# لا تقم بتشغيل app.run() هنا لأن Vercel سيقوم بتشغيل التطبيق تلقائياً
