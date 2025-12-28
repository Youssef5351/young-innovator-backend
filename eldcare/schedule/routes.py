from flask import jsonify, request
from app import app
from config import firebase_config
import firebase_admin
from firebase_admin import credentials, auth as admin_auth, db as admin_db
import uuid 

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
# Create appointment
# ===============================
@app.route("/schedule", methods=["POST"])
def create_appointment():
    userId, error_response, status = get_uid_from_token()
    if error_response:
        return error_response, status

    startDate = request.json.get("startDate")
    endDate = request.json.get("endDate")
    title = request.json.get("title")
    allDay = request.json.get("allDay")
    description = request.json.get("description")
    byUserType = request.json.get("byUserType")

    try:
        appointmentId = str(uuid.uuid4())  # 🔹 توليد مفتاح عشوائي
        appointment_data = {
            "startDate": startDate,
            "endDate": endDate,
            "title": title,
            "allDay": allDay,
            "description": description,
            "byUserType": byUserType,
        }

        db.child("schedule").child(userId).child(appointmentId).set(appointment_data)

        return jsonify({
            "message": "Appointment created successfully!",
            "appointmentId": appointmentId
        }), 201

    except Exception as e:
        return jsonify({
            "message": "An error occurred while creating appointment.",
            "error": str(e)
        }), 402


# ===============================
# Get appointments
# ===============================
@app.route("/schedule/<userId>", methods=["GET"])
def get_appointments(userId):
    uid, error_response, status = get_uid_from_token()
    if error_response:
        return error_response, status

    try:
        appointments = db.child("schedule").child(userId).get()
        return jsonify({
            "message": "Appointments retrieved successfully!",
            "appointments": appointments
        }), 200
    except Exception as e:
        return jsonify({
            "message": "An error occurred while retrieving appointments.",
            "error": str(e)
        }), 402
