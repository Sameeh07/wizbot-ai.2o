# chat.py
import os
import json
import time
import logging
import requests
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from gtts import gTTS
from doctor_voice import text_to_speech_with_elevenlabs

logging.basicConfig(level=logging.INFO)

chat_bp = Blueprint('chat', __name__)
CHAT_HISTORY_FILE = "chat_history.json"

def load_chat_history():
    if not os.path.exists(CHAT_HISTORY_FILE):
        return []
    with open(CHAT_HISTORY_FILE, "r") as f:
        return json.load(f)

def save_chat_history(history):
    # keep only last 2 messages
    with open(CHAT_HISTORY_FILE, "w") as f:
        json.dump(history[-2:], f)

@chat_bp.route('', methods=['POST'])  # handles POST /api/chat
@jwt_required()
def chat():
    data = request.json or {}
    user_input     = data.get('message', '').strip()
    use_elevenlabs = data.get('use_elevenlabs', False)

    if not user_input:
        return jsonify(error="No input provided"), 400

    # build conversation
    history = load_chat_history()
    system_prompt = (
        "You are Wizbot, a medical assistant robot. "
        "Answer only medical queries(don't answer other questions), provide mental health support, "
        "and keep responses under 2 sentences."
    )
    convo = [{"role":"system","content":system_prompt}]
    for entry in history:
        convo.extend([
            {"role":"user",     "content":entry["user"]},
            {"role":"assistant","content":entry["assistant"]}
        ])
    convo.append({"role":"user","content":user_input})

    # call Groq API
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model":       "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages":    convo,
            "temperature": 0.7
        }
    )
    if resp.status_code != 200:
        logging.error(f"Groq API failed ({resp.status_code}): {resp.text}")
        return jsonify(error="Groq API failed"), 500

    reply = resp.json()["choices"][0]["message"]["content"]
    history.append({"user":user_input,"assistant":reply})
    save_chat_history(history)

    # Text-to-Speech with fallback
    audio_path = os.path.join("statics", "doctor_voice.mp3")
    if use_elevenlabs:
        try:
            audio_path = text_to_speech_with_elevenlabs(reply)
        except Exception as e:
            logging.warning(f"ElevenLabs TTS failed, falling back to gTTS: {e}")
            tts = gTTS(text=reply, lang="en")
            tts.save(audio_path)
    else:
        tts = gTTS(text=reply, lang="en")
        tts.save(audio_path)

    # cache-bust query param
    ts = int(time.time() * 1000)
    audio_url = request.host_url.rstrip("/") + f"/statics/doctor_voice.mp3?v={ts}"

    return jsonify(reply=reply, audio_url=audio_url)
