# main.py — entry point for Ascent Inventory desktop app
from frontend.main_window import run

if __name__ == "__main__":
    run()

#run this to start api port: uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
#then run main

#to make someone an admin (local SQLite):
# sqlite3 backend/inventory.db "UPDATE app_users SET role = 'admin' WHERE email = 'their@email.com';"
# hosted Postgres (Neon SQL editor):
# UPDATE app_users SET role = 'admin' WHERE email = 'their@email.com';