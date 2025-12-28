from flask import jsonify, request
from app import app
from config import firebase_config
from eldcare.chatClassifier.classifier_model import classify_chat
from eldcare.Chat.OpenAiChat import get_schedule_answer, get_general_answer, set_reminder

import firebase_admin
from firebase_admin import credentials, auth as admin_auth, db as admin_db

# ===============================
# Firebase Admin initialization
# ===============================
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_config["serviceAccount"])
    firebase_admin.initialize_app(cred, {
        "databaseURL": firebase_config["databaseURL"]
    })
db = admin_db.reference()

# ===============================
# Helper: verify ID token
# ===============================
def get_uid_from_token():
    id_token = request.headers.get("Authorization")
    if not id_token:
        return None, jsonify({"message": "Missing authorization token"}), 401
    try:
        decoded_token = admin_auth.verify_id_token(id_token)
        return decoded_token["uid"], None, None
    except Exception:
        return None, jsonify({"message": "Invalid token"}), 401

# ===============================
# Chat route
# ===============================
@app.route("/chat", methods=["POST"])
def get_chat():
    userId, error_response, status = get_uid_from_token()
    if error_response:
        return error_response, status
    
    input_text = request.json.get("message")
    
    if not input_text:
        return jsonify({"message": "Message is required"}), 400
    
    # Simple mock responses for testing
    res = f"I received your message: '{input_text}'. (AI disabled - add OpenAI credits or use mock mode)"
    
    return jsonify({"message": res}), 200