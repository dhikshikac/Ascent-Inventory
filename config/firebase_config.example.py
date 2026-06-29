# Copy to config/firebase_config.py and fill in values (firebase_config.py is gitignored).
# Environment variables override these defaults when set.

import os

FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "your-firebase-web-api-key")
FIREBASE_AUTH_DOMAIN = os.environ.get("FIREBASE_AUTH_DOMAIN", "your-project.firebaseapp.com")
FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "your-project-id")
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
