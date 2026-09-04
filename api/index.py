import os
import json
import requests
from flask import Flask, request
import telebot
from telebot import types

# التوكنات يسحبها من إعدادات Vercel
BOT_TOKEN = os.getenv('BOT_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
ADMIN_ID = 6799794121

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False)
app = Flask(__name__)

# --- أوامر البوت الأساسية ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = "أهلاً بك في <b>Hassany Store</b> 👑\nالمتجر الأول لتوقيع التطبيقات 🔥"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("توقيع تطبيق ✅", callback_data="sign"),
        types.InlineKeyboardButton("متجر التطبيقات 📱", web_app=types.WebAppInfo("https://no-bznl.vercel.app"))
    )
    if message.from_user.id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("لوحة التحكم ⚙️", callback_data="admin"))
    
    bot.reply_to(message, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "sign":
        bot.answer_callback_query(call.id, "سيتم تفعيل التوقيع قريباً!", show_alert=True)
    elif call.data == "admin":
        bot.answer_callback_query(call.id, "مرحباً بك يا مدير", show_alert=True)

# --- إعدادات الويب هوك (Vercel) ---
@app.route('/api', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return "OK", 200
        except Exception as e:
            return "Error", 500
    else:
        return "<h1>البوت شغال ومربوط بسيرفر فيرسل الأساسي 🚀</h1>", 200
