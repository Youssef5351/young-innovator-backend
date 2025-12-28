from config import firebase_config
import firebase_admin
from firebase_admin import credentials, auth


# ===============================
# Firebase Admin initialization
# ===============================

if not firebase_admin._apps:  # Only initialize if no app exists
    cred = credentials.Certificate(firebase_config["serviceAccount"])
    firebase_admin.initialize_app(cred, {
        "databaseURL": firebase_config["databaseURL"]
    })


# ===============================
# Auth functions (same interface)
# ===============================

def sign_up(email, password):
    try:
        auth.create_user(
            email=email,
            password=password
        )
        return True
    except Exception as e:
        print(e)
        return False


def login(email, password):
    """
    firebase-admin does NOT verify passwords.
    This function now only checks if the user exists.
    (same signature, backend-safe behavior)
    """
    try:
        auth.get_user_by_email(email)
        return True
    except Exception as e:
        print(e)
        return False


def logout():
    # Backend has no session state
    return True
