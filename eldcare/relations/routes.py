from flask import jsonify, request
from app import app
from config import firebase_config
import firebase_admin
from firebase_admin import credentials, auth as admin_auth, db as admin_db

# ===============================
# Firebase Admin initialization
# ===============================
if not firebase_admin._apps:
    try:
        # Handle both dict (production) and string (local)
        if isinstance(firebase_config["serviceAccount"], dict):
            # Production: already a dictionary
            cred = credentials.Certificate(firebase_config["serviceAccount"])
        else:
            # Local: file path
            cred = credentials.Certificate(firebase_config["serviceAccount"])
        
        firebase_admin.initialize_app(cred, {
            "databaseURL": firebase_config["databaseURL"]
        })
        print("✓ Firebase Admin initialized in user routes")
    except Exception as e:
        print(f"✗ Firebase initialization failed: {e}")
        raise

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
# Add patient
# ===============================
@app.route("/addPatient", methods=["POST"])
def add_patient():
    doctorId, error_response, status = get_uid_from_token()
    if error_response:
        return error_response, status

    patientEmail = request.json.get("patientEmail")

    try:
        users = db.child("users").order_by_child("email").equal_to(patientEmail).get()
        
        # Check if user exists
        if not users:
            return jsonify({"message": "Patient with this email not found"}), 404
        
        patientId = list(users.keys())[0]

        db.child("doctors").child(doctorId).child("patient_list").push(patientId)
        db.child("elderlies").child(patientId).child("doctor_list").push(doctorId)

        return jsonify({"message": "Patient added successfully!"}), 201
    except Exception as e:
        return jsonify({"message": "An error occurred while adding patient.", "error": str(e)}), 402

# ===============================
# Add relative
# ===============================
@app.route("/addRelative", methods=["POST"])
def add_relative():
    patientId, error_response, status = get_uid_from_token()
    if error_response:
        return error_response, status

    relativeEmail = request.json.get("patientEmail")

    try:
        users = db.child("users").order_by_child("email").equal_to(relativeEmail).get()
        
        # Check if user exists
        if not users:
            return jsonify({"message": "User with this email not found"}), 404
        
        relativeId = list(users.keys())[0]

        db.child("relatives").child(patientId).child("relative_list").push(relativeId)
        db.child("elderlies").child(relativeId).child("relative_list").push(patientId)

        return jsonify({"message": "Relative added successfully!"}), 201
    except Exception as e:
        return jsonify({"message": "An error occurred while adding relative.", "error": str(e)}), 402


# ===============================
# Get patients
# ===============================
@app.route("/getPatients/<userId>", methods=["GET"])
def get_patients(userId):
    uid, error_response, status = get_uid_from_token()
    if error_response:
        return error_response, status

    try:
        patients = db.child("doctors").child(uid).child("patient_list").get()
        return jsonify({"message": "Patients retrieved successfully!", "patients": patients}), 200
    except Exception as e:
        return jsonify({"message": "An error occurred while retrieving patients.", "error": str(e)}), 402


# ===============================
# Get doctors
# ===============================
@app.route("/getDoctors/<userId>", methods=["GET"])
def get_doctors(userId):
    uid, error_response, status = get_uid_from_token()
    if error_response:
        return error_response, status

    try:
        doctors = db.child("elderlies").child(uid).child("doctor_list").get()
        return jsonify({"message": "Doctors retrieved successfully!", "doctors": doctors}), 200
    except Exception as e:
        return jsonify({"message": "An error occurred while retrieving doctors.", "error": str(e)}), 402


# ===============================
# Get relatives
# ===============================
@app.route("/getRelatives/<userId>", methods=["GET"])
def get_relatives(userId):
    uid, error_response, status = get_uid_from_token()
    if error_response:
        return error_response, status

    try:
        relatives = db.child("elderlies").child(uid).child("relative_list").get()
        return jsonify({"message": "Relatives retrieved successfully!", "relatives": relatives}), 200
    except Exception as e:
        return jsonify({"message": "An error occurred while retrieving relatives.", "error": str(e)}), 402


# ===============================
# Get single patient
# ===============================
@app.route("/getPatient/<userId>", methods=["GET"])
def get_patient(userId):
    uid, error_response, status = get_uid_from_token()
    if error_response:
        return error_response, status

    try:
        patient = db.child("elderlies").child(uid).get()
        return jsonify({"message": "Patient retrieved successfully!", "patient": patient}), 200
    except Exception as e:
        return jsonify({"message": "An error occurred while retrieving patient.", "error": str(e)}), 402


# ===============================
# Get single relative
# ===============================
@app.route("/getRelative/<userId>", methods=["GET"])
def get_relative(userId):
    uid, error_response, status = get_uid_from_token()
    if error_response:
        return error_response, status

    try:
        relative = db.child("relatives").child(uid).get()
        return jsonify({"message": "Relative retrieved successfully!", "relative": relative}), 200
    except Exception as e:
        return jsonify({"message": "An error occurred while retrieving relative.", "error": str(e)}), 402
