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
    cred = credentials.Certificate(firebase_config["serviceAccount"])
    firebase_admin.initialize_app(cred, {
        "databaseURL": firebase_config["databaseURL"]
    })

db = admin_db.reference()


# ===============================
# Register
# ===============================

@app.route("/auth/register", methods=["POST"])
def register():
    fullName = request.json.get("fullName")
    email = request.json.get("email")
    userType = request.json.get("userType")
    gender = request.json.get("gender")
    id_token = request.json.get("idToken")  # Frontend sends this

    if not id_token:
        return jsonify({"message": "ID token is required"}), 400

    try:
        # Verify the token (user already created by frontend)
        decoded = auth.verify_id_token(id_token)
        uid = decoded["uid"]
    except Exception as e:
        return jsonify({"message": "Invalid token"}), 401

    # Save user data to database
    db.child("users").child(uid).set({
        "userId": uid,
        "fullName": fullName,
        "email": email,
        "userType": userType,
        "gender": gender
    })

    # Note: Changed to match frontend casing (Doctor, Relative)
    if userType == "Doctor":
        db.child("doctors").child(uid).set({
            "userId": uid,
            "fullName": fullName,
            "email": email,
            "patient_list": []
        })

    elif userType == "Relative":
        db.child("relatives").child(uid).set({
            "userId": uid,
            "fullName": fullName,
            "email": email,
            "relative_list": []
        })

    elif userType == "Elderly":
        db.child("elderlies").child(uid).set({
            "userId": uid,
            "fullName": fullName,
            "email": email,
            "doctor_list": [],
            "relative_list": []
        })

        userDetails = db.child("users").child(uid).get()

        return jsonify({
            "message": "Registration successful!",
            "userDetails": userDetails,
            "idToken": id_token  # Return same token
        }), 200

    # ⚠️ backend cannot sign in → generate custom token instead
    custom_token = auth.create_custom_token(uid).decode("utf-8")

    response = make_response(jsonify({
        "message": "Registration successful!",
        "userDetails": userDetails,
        "jwtToken": custom_token
    }), 200)

    response.set_cookie(
        "jwtToken",
        custom_token,
        expires=99999999,
        httponly=True,
        samesite="Strict"
    )

    return response, 200


# ===============================
# Login
# ===============================

@app.route("/auth/login", methods=["POST"])
def login():
    id_token = request.json.get("idToken")

    if not id_token:
        return jsonify({"message": "ID token is required"}), 400

    try:
        decoded = auth.verify_id_token(id_token)
        uid = decoded["uid"]
    except Exception as e:
        return jsonify({"message": "Invalid token"}), 401

    userDetails = db.child("users").child(uid).get()

    response = make_response(jsonify({
        "message": "Login successful!",
        "userDetails": userDetails,
        "jwtToken": id_token
    }), 200)

    response.set_cookie(
        "jwtToken",
        id_token,
        expires=9999999,
        httponly=True,
        samesite="Strict"
    )

    return response, 200
