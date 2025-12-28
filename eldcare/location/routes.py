from flask import jsonify, request, make_response
from app import app
from config import firebase_config

import firebase_admin
from firebase_admin import credentials, db as admin_db

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
# Location route
# ===============================
@app.route("/location/<userId>", methods=["GET"])
def get_location(userId):
    from eldcare.auth.methods import auth

    try:
        # 🔹 التحقق من المستخدم: backend لا يحتفظ بالـ current_user
        # يجب إرسال ID token من الفرونت للتحقق
        if not request.headers.get("Authorization"):
            return jsonify({"message": "Missing authorization token"}), 401

        # 🔹 قراءة location من Firebase Realtime Database
        location_ref = db.child("location").child(userId)
        location = location_ref.get()
        
        return jsonify({
            "message": "Location retrieved successfully!",
            "location": location
        }), 200

    except Exception as e:
        return jsonify({
            "message": "An error occurred while retrieving location.",
            "error": str(e)
        }), 402
