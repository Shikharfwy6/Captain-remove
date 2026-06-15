import re
import os
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

app = Flask(__name__)

# =====================================================================
# YAHAN BOTFATHER SE MILA TOKEN DALEIN
TOKEN = "YOUR_BOT_TOKEN_HERE"
# =====================================================================

# Global application instance (Vercel ke liye initialization)
telegram_app = Application.builder().token(TOKEN).updater(None).build()

# Text ko saaf karne ka function
def clean_caption(text: str) -> str:
    if not text:
        return ""
    # 1. Sabhi website links (http, https, www) ko hatayein
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # 2. Telegram usernames (@username) ko hatayein
    text = re.sub(r'@\w+', '', text)
    return text.strip()

# Post handle karne ka function
async def handle_post(update: Update, context):
    message = update.message
    if not message:
        return

    original_text = message.caption if message.caption else message.text
    cleaned_text = clean_caption(original_text) if original_text else ""

    # 1. Normal Text Message
    if message.text and cleaned_text:
        await message.reply_text(cleaned_text, parse_mode="Markdown")
        return

    # 2. Video
    if message.video:
        await message.reply_video(video=message.video.file_id, caption=cleaned_text, parse_mode="Markdown")
        return

    # 3. Photo
    if message.photo:
        await message.reply_photo(photo=message.photo[-1].file_id, caption=cleaned_text, parse_mode="Markdown")
        return

    # 4. Animation (GIF)
    if message.animation:
        await message.reply_animation(animation=message.animation.file_id, caption=cleaned_text, parse_mode="Markdown")
        return

    # 5. Document / File
    if message.document:
        await message.reply_document(document=message.document.file_id, caption=cleaned_text, parse_mode="Markdown")
        return

# Handler ko register karna (sirf ek baar initialize hoga)
telegram_app.add_handler(MessageHandler(filters.ALL, handle_post))

# Flask Route jo Vercel par incoming webhooks receive karega
@app.route('/', methods=['POST'])
def webhook():
    if request.method == "POST":
        update_json = request.get_json(force=True)
        
        # Async function ko Flask ke andar chalane ke liye loop ka use
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Telegram update process karein
        update = Update.de_json(update_json, telegram_app.bot)
        loop.run_until_complete(telegram_app.initialize())
        loop.run_until_complete(telegram_app.process_update(update))
        loop.close()
        
        return jsonify({"status": "success"}), 200
    return "OK", 200

@app.route('/', methods=['GET'])
def index():
    return "Bot is running on Vercel via Webhook!", 200
