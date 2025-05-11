# transcribe.py
import os
import requests
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

transcribe_bp = Blueprint('transcribe', __name__)

@transcribe_bp.route('/transcribe', methods=['POST'])
@jwt_required()
def transcribe():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio = request.files['audio']

    response = requests.post(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
        files={"file": (audio.filename, audio.stream, audio.mimetype)},
        data={"model": "whisper-large-v3", "language": "en"}
    )

    if response.status_code != 200:
        return jsonify({"error": "Whisper API failed"}), 500

    text = response.json().get('text', '')
    return jsonify({"text": text})
