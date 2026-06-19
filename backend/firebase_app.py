import os
import firebase_admin
from firebase_admin import credentials

_SERVICE_ACCOUNT = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "firebase-service-account.json",
)

def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(_SERVICE_ACCOUNT)
        firebase_admin.initialize_app(cred)