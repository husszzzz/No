import telebot
from flask import Flask, request

# التوكن مالتك جاهز
BOT_TOKEN = "7594385345:AAG4V4Nc9l-p-MsZam_L2U1HhllGajTnE40"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

# لحفظ خطوات الاستلام
user_steps = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_steps[user_id] = 'p12'
    bot.reply_to(message, "أهلاً بك! 👋\nأرسل ملف الشهادة `.p12` أولاً:", parse_mode="Markdown")

@bot.message_handler(content_types=['document', 'text'])
def handle_files(message):
    user_id = message.chat.id
    if user_id not in user_steps:
        return
    
    step = user_steps[user_id]
    
    if step == 'p12' and message.document and message.document.file_name.endswith('.p12'):
        user_steps[user_id] = 'prov'
        bot.reply_to(message, "ممتاز! ✅\nالآن أرسل ملف `.mobileprovision`:")
        
    elif step == 'prov' and message.document and message.document.file_name.endswith('.mobileprovision'):
        user_steps[user_id] = 'password'
        bot.reply_to(message, "حلو! هسه أرسل باسوورد الشهادة:")
        
    elif step == 'password' and message.text:
        bot.reply_to(message, "جاري التوقيع... انتظر ثواني ⏳")
        del user_steps[user_id]

# هذا هو الـ api اللي يستقبل الرسائل من فيرسل
@app.route('/', defaults={'path': ''}, methods=['POST', 'GET'])
@app.route('/<path:path>', methods=['POST', 'GET'])
def webhook(path):
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return "OK", 200
    else:
        return "Bot is Running!", 200
