import re
import os
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

app = Flask(__name__)

# =====================================================================
# 1. YAHAN BOTFATHER SE MILA TOKEN DALEIN
TOKEN = "8903632186:AAFpZ7EP4II3H7yY8O5u57fWYBUUkQKZQV8"

# 2. YAHAN APNE PRIVATE CHANNEL KI ID DALEIN 
# Note: Private channel ID hamesha -100 se shuru hoti hai aur isme quotes '' nahi lagane hain kyunki yeh ek Number (Integer) hota hai.
CHANNEL_ID = -1003758252316  # <--- Apni asli ID se replace karein
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

    try:
        # 1. Normal Text Message
        if message.text:
            if cleaned_text:
                await context.bot.send_message(chat_id=CHANNEL_ID, text=cleaned_text, parse_mode="Markdown")
                await message.reply_text("✅ Text message clean karke private channel me bhej diya gaya hai!")
            return

        # 2. Video
        if message.video:
            await context.bot.send_video(chat_id=CHANNEL_ID, video=message.video.file_id, caption=cleaned_text, parse_mode="Markdown")
            await message.reply_text("✅ Video clean karke private channel me bhej di gayi hai!")
            return

        # 3. Photo
        if message.photo:
            await context.bot.send_photo(chat_id=CHANNEL_ID, photo=message.photo[-1].file_id, caption=cleaned_text, parse_mode="Markdown")
            await message.reply_text("✅ Photo clean karke private channel me bhej di gayi hai!")
            return

        # 4. Animation (GIF)
        if message.animation:
            await context.bot.send_animation(chat_id=CHANNEL_ID, animation=message.animation.file_id, caption=cleaned_text, parse_mode="Markdown")
            await message.reply_text("✅ GIF clean karke private channel me bhej diya gaya hai!")
            return

        # 5. Document / File
        if message.document:
            await context.bot.send_document(chat_id=CHANNEL_ID, document=message.document.file_id, caption=cleaned_text, parse_mode="Markdown")
            await message.reply_text("✅ Document clean karke private channel me bhej diya gaya hai!")
            return
            
    except Exception as e:
        # Agar bot admin nahi hoga to error show karega
        await message.reply_text(f"❌ Channel me bhejne me dikkat aayi. Check karein ki Bot channel ka Admin hai ya nahi.\nError: {e}")

# Handler ko register karna
telegram_app.add_handler(MessageHandler(filters.ALL, handle_post))

# Flask Route jo Vercel par incoming webhooks receive karega
@app.route('/', methods=['POST'])
def webhook():
    if request.method == "POST":
        update_json = request.get_json(force=True)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        update = Update.de_json(update_json, telegram_app.bot)
        loop.run_until_complete(telegram_app.initialize())
        loop.run_until_complete(telegram_app.process_update(update))
        loop.close()
        
        return jsonify({"status": "success"}), 200
    return "OK", 200

@app.route('/', methods=['GET'])
def index():
    return "Bot is running on Vercel via Webhook with Private Channel Support!", 200
