# doctor_voice.py
import os
import logging
import requests

logging.basicConfig(level=logging.INFO)

def text_to_speech_with_elevenlabs(text, voice_id=None):
    elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
    if not elevenlabs_api_key:
        raise ValueError("ELEVENLABS_API_KEY not set in environment")

    voice_id = voice_id or "9BWtsMINqrJLrRacOk9x"
    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        "?optimize_streaming_latency=0&output_format=mp3_22050_32"
    )
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "xi-api-key": elevenlabs_api_key,
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.7
        }
    }

    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        raise Exception(f"ElevenLabs API error: {resp.text}")

    os.makedirs("statics", exist_ok=True)
    audio_path = os.path.join("statics", "doctor_voice.mp3")
    with open(audio_path, "wb") as f:
        f.write(resp.content)

    return audio_path
