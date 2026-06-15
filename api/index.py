import re
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# =====================================================================
# 1. YAHAN BOTFATHER SE MILA TOKEN DALEIN
TOKEN = "8903632186:AAFpZ7EP4II3H7yY8O5u57fWYBUUkQKZQV8"

# 2. YAHAN APNE PRIVATE CHANNEL KI ID DALEIN (Bina quotes ke)
CHANNEL_ID = -1003758252316  # <--- Apni asli ID se replace karein
# =====================================================================

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

# Text ko saaf karne ka function
def clean_caption(text: str) -> str:
    if not text:
        return ""
    # 1. Sabhi website links (http, https, www) ko hatayein
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # 2. Telegram usernames (@username) ko hatayein
    text = re.sub(r'@\w+', '', text)
    return text.strip()

# Telegram API par message bhejne ka simple function (Bina connection pool error ke)
def send_to_telegram(endpoint, data):
    url = f"{TELEGRAM_API}/{endpoint}"
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Telegram Request Error: {e}")
        return None

def process_message(message):
    original_text = message.get('caption') if message.get('caption') else message.get('text')
    cleaned_text = clean_caption(original_text) if original_text else ""

    # Base payload jo har media ke sath jayega
    payload = {
        "chat_id": CHANNEL_ID,
        "parse_mode": "Markdown"
    }

    # 1. Normal Text Message
    if 'text' in message and not any(k in message for k in ['video', 'photo', 'animation', 'document']):
        if cleaned_text:
            payload["text"] = cleaned_text
            send_to_telegram("sendMessage", payload)
        return

    # 2. Video
    if 'video' in message:
        payload["video"] = message['video']['file_id']
        payload["caption"] = cleaned_text
        send_to_telegram("sendVideo", payload)
        return

    # 3. Photo
    if 'photo' in message:
        payload["photo"] = message['photo'][-1]['file_id']
        payload["caption"] = cleaned_text
        send_to_telegram("sendPhoto", payload)
        return

    # 4. Animation (GIF)
    if 'animation' in message:
        payload["animation"] = message['animation']['file_id']
        payload["caption"] = cleaned_text
        send_to_telegram("sendAnimation", payload)
        return

    # 5. Document / File
    if 'document' in message:
        payload["document"] = message['document']['file_id']
        payload["caption"] = cleaned_text
        send_to_telegram("sendDocument", payload)
        return

# Flask Route jo Vercel par incoming webhooks receive karega
@app.route('/', methods=['POST'])
def webhook():
    if request.method == "POST":
        try:
            update_json = request.get_json(force=True)
            
            if "message" in update_json:
                message_data = update_json["message"]
                # Normal synchronous function call (Koi async/await ya loop ka jhanjhat nahi)
                process_message(message_data)
                    
        except Exception as e:
            print(f"Error occurred: {e}")
            return jsonify({"status": "error", "message": str(e)}), 200
            
        return jsonify({"status": "success"}), 200
    return "OK", 200

@app.route('/', methods=['GET'])
def index():
    return "Bot is running flawlessly on Vercel via HTTP Requests!", 200
