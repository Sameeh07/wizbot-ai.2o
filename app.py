import os
from flask import Flask, send_from_directory, render_template, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from auth import auth_bp  # Blueprint for authentication
from chat import chat_bp  # Blueprint for chat
from transcribe import transcribe_bp  # Blueprint for transcription

app = Flask(
    __name__,
    static_folder="static",  # React’s JS/CSS lives here
    template_folder="templates"  # React’s index.html lives here
)
CORS(app)

# Set up the secret key for JWT (you can use an environment variable for security)
app.config["JWT_SECRET_KEY"] = "super-secret-key"  # This should be in your environment variables for production!
jwt = JWTManager(app)

# --- API routes ---
app.register_blueprint(auth_bp, url_prefix="/api/auth")  # Authentication blueprint
app.register_blueprint(chat_bp, url_prefix="/api/chat")  # Chat blueprint
app.register_blueprint(transcribe_bp, url_prefix="/api/chat")  # Transcription blueprint

# --- Health check ---
@app.route("/api/health")
def health():
    return jsonify(message="Medical Chatbot Backend is Running 🚀")

# --- Serve TTS audio files from `statics/` ---
@app.route("/statics/<path:filename>")
def serve_audio(filename):
    return send_from_directory("statics", filename)

# --- Catch-all to serve React UI ---
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Get port from environment or default to 5000
    app.run(host="0.0.0.0", port=port, debug=True)
