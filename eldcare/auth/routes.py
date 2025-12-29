from flask import jsonify, request, make_response
from app import app
from config import firebase_config
import json

import firebase_admin
from firebase_admin import credentials, auth, db as admin_db

# ===============================
# Firebase Admin initialization
# ===============================

if not firebase_admin._apps:
    try:
        # Check if serviceAccount is a dict (production) or string (local)
        if isinstance(firebase_config["serviceAccount"], dict):
            # Production: already a dictionary from environment variable
            cred = credentials.Certificate(firebase_config["serviceAccount"])
        else:
            # Local: it's a file path
            cred = credentials.Certificate(firebase_config["serviceAccount"])
        
        firebase_admin.initialize_app(cred, {
            "databaseURL": firebase_config["databaseURL"]
        })
        
        print("✓ Firebase Admin SDK initialized successfully")
    except Exception as e:
        print(f"✗ Firebase Admin initialization failed: {e}")
        raise

db = admin_db.reference()



# ===============================
# Register
# ===============================

@app.route("/auth/register", methods=["POST"])
def register():
    data = request.json
    fullName = data.get("fullName")
    email = data.get("email")
    userType = data.get("userType")
    gender = data.get("gender")
    id_token = data.get("idToken")

    if not id_token:
        return jsonify({"message": "ID token is required"}), 400

    try:
        decoded = auth.verify_id_token(id_token)
        uid = decoded["uid"]
    except Exception as e:
        return jsonify({"message": "Invalid token", "error": str(e)}), 401

    user_payload = {
        "userId": uid,
        "fullName": fullName,
        "email": email,
        "userType": userType,
        "gender": gender
    }

    try:
        # CORRECT ADMIN SDK SYNTAX:
        # db is admin_db.reference()
        db.child("users").child(uid).set(user_payload)

        if userType == "Doctor":
            db.child("doctors").child(uid).set({**user_payload, "patient_list": []})
        elif userType == "Relative":
            db.child("relatives").child(uid).set({**user_payload, "relative_list": []})
        elif userType == "Elderly":
            db.child("elderlies").child(uid).set({**user_payload, "doctor_list": [], "relative_list": []})

        # Fetching back: .get() returns the data directly in Admin SDK
        userDetails = db.child("users").child(uid).get()

        custom_token = auth.create_custom_token(uid).decode("utf-8")

        response = make_response(jsonify({
            "message": "Registration successful!",
            "userDetails": userDetails,
            "jwtToken": custom_token
        }), 200)

        response.set_cookie("jwtToken", custom_token, httponly=True, samesite="Strict")
        return response
    except Exception as e:
        print(f"Database Error: {e}")
        return jsonify({"message": "Database write failed", "error": str(e)}), 500

@app.route("/auth/login", methods=["POST"])
def login():
    id_token = request.json.get("idToken")
    
    if not id_token:
        return jsonify({"message": "ID token is required"}), 400
    
    try:
        # Verify this is working
        print("Attempting to verify token...")
        decoded = auth.verify_id_token(id_token)
        uid = decoded["uid"]
        print(f"✓ Token verified for user: {uid}")
        
        # Fetch user details
        userDetails = db.child("users").child(uid).get()
        
        if not userDetails:
            return jsonify({"message": "User record not found"}), 404
        
        response = make_response(jsonify({
            "message": "Login successful!",
            "userDetails": userDetails,
            "jwtToken": id_token
        }), 200)
        response.set_cookie("jwtToken", id_token, httponly=True, samesite="Strict")
        return response
        
    except auth.InvalidIdTokenError as e:
        print(f"Invalid ID Token Error: {e}")
        return jsonify({
            "message": "Login failed", 
            "error": "Invalid or expired token"
        }), 401
    except auth.ExpiredIdTokenError as e:
        print(f"Expired Token Error: {e}")
        return jsonify({
            "message": "Login failed", 
            "error": "Token has expired"
        }), 401
    except Exception as e:
        print(f"Login Error: {type(e).__name__}: {str(e)}")
        return jsonify({
            "message": "Login failed", 
            "error": str(e)
        }), 401
