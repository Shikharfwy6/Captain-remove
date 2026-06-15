import re
import os
import asyncio
from flask import Flask, request, jsonify
from telegram import Bot

app = Flask(__name__)

# =====================================================================
# 1. YAHAN BOTFATHER SE MILA TOKEN DALEIN
TOKEN = "8903632186:AAFpZ7EP4II3H7yY8O5u57fWYBUUkQKZQV8"

# 2. YAHAN APNE PRIVATE CHANNEL KI ID DALEIN (Bina quotes ke)
CHANNEL_ID = -1003758252316 # <--- Apni asli ID se replace karein
# =====================================================================

# Direct Bot client initialize karein (Isme event loop ka jhanjhat nahi hota)
bot = Bot(token=TOKEN)

# Text ko saaf karne ka function
def clean_caption(text: str) -> str:
    if not text:
        return ""
    # 1. Sabhi website links (http, https, www) ko hatayein
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # 2. Telegram usernames (@username) ko hatayein
    text = re.sub(r'@\w+', '', text)
    return text.strip()

# Async function jo actual me message send karega
async def send_to_channel(message):
    original_text = message.get('caption') if message.get('caption') else message.get('text')
    cleaned_text = clean_caption(original_text) if original_text else ""

    # 1. Normal Text Message
    if 'text' in message and not any(k in message for k in ['video', 'photo', 'animation', 'document']):
        if cleaned_text:
            await bot.send_message(chat_id=CHANNEL_ID, text=cleaned_text, parse_mode="Markdown")
        return

    # 2. Video
    if 'video' in message:
        await bot.send_video(chat_id=CHANNEL_ID, video=message['video']['file_id'], caption=cleaned_text, parse_mode="Markdown")
        return

    # 3. Photo
    if 'photo' in message:
        # Sabse badi photo select karne ke liye [-1]
        await bot.send_photo(chat_id=CHANNEL_ID, photo=message['photo'][-1]['file_id'], caption=cleaned_text, parse_mode="Markdown")
        return

    # 4. Animation (GIF)
    if 'animation' in message:
        await bot.send_animation(chat_id=CHANNEL_ID, animation=message['animation']['file_id'], caption=cleaned_text, parse_mode="Markdown")
        return

    # 5. Document / File
    if 'document' in message:
        await bot.send_document(chat_id=CHANNEL_ID, document=message['document']['file_id'], caption=cleaned_text, parse_mode="Markdown")
        return

# Flask Route jo Vercel par incoming webhooks receive karega
@app.route('/', methods=['POST'])
def webhook():
    if request.method == "POST":
        try:
            update_json = request.get_json(force=True)
            
            # Agar message update me hai to process karein
            if "message" in update_json:
                message_data = update_json["message"]
                
                # Naya loop banakar async function run karein bina purane loop ko disturb kiye
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(send_to_channel(message_data))
                finally:
                    loop.close()
                    
        except Exception as e:
            print(f"Error occurred: {e}")
            # Internal error hone par bhi 200 bhejenge taaki Telegram baar-baar same request na bheje
            return jsonify({"status": "error", "message": str(e)}), 200
            
        return jsonify({"status": "success"}), 200
    return "OK", 200

@app.route('/', methods=['GET'])
def index():
    return "Bot is running perfectly on Vercel via Webhook without loop errors!", 200
