# chat.py
import os
import json
import time
import requests
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from gtts import gTTS
from doctor_voice import text_to_speech_with_elevenlabs

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

@chat_bp.route('', methods=['POST'])  # handles POST /chat
@jwt_required()
def chat():
    data = request.json
    user_input     = data.get('message', '').strip()
    use_elevenlabs = data.get('use_elevenlabs', False)

    if not user_input:
        return jsonify(error="No input provided"), 400

    # load & build conversation
    history = load_chat_history()
    system_prompt = (
        "You are Wizbot, a medical assistant robot. "
        "Answer only medical queries, provide mental health support, "
        "and keep responses under 2 sentences."
    )
    convo = [{"role":"system","content":system_prompt}]
    for entry in history:
        convo.append({"role":"user",     "content":entry["user"]})
        convo.append({"role":"assistant","content":entry["assistant"]})
    convo.append({"role":"user","content":user_input})

    # call Groq API
    headers = {
      "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
      "Content-Type": "application/json"
    }
    payload = {
      "model":       "llama-3.1-8b-instant",
      "messages":    convo,
      "temperature": 0.7
    }
    resp = requests.post(
      "https://api.groq.com/openai/v1/chat/completions",
      headers=headers,
      json=payload
    )
    if resp.status_code != 200:
        return jsonify(error="Groq API failed"), 500

    # extract reply & update history
    reply = resp.json()["choices"][0]["message"]["content"]
    history.append({"user":user_input,"assistant":reply})
    save_chat_history(history)

    # TTS: ElevenLabs or gTTS
    if use_elevenlabs:
        audio_path = text_to_speech_with_elevenlabs(reply)
    else:
        audio_path = os.path.join("statics","doctor_voice.mp3")
        tts = gTTS(text=reply, lang="en")
        tts.save(audio_path)

    # cache‑bust so each reply is fetched anew
    ts = int(time.time()*1000)
    audio_url = request.host_url.rstrip("/") + f"/statics/doctor_voice.mp3?v={ts}"

    return jsonify(reply=reply, audio_url=audio_url)
