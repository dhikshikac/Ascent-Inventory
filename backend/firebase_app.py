import json
import os

import firebase_admin
from firebase_admin import credentials

_SERVICE_ACCOUNT = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "firebase-service-account.json",
)


def init_firebase():
    if not firebase_admin._apps:
        json_str = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
        if json_str:
            cred = credentials.Certificate(json.loads(json_str))
        else:
            cred = credentials.Certificate(_SERVICE_ACCOUNT)
        firebase_admin.initialize_app(cred)
