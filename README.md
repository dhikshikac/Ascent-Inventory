# Ascent-Inventory

General Requirements:

The master database starts completely empty
Have different departments 
People are categorized into these; you should be able to view the depts, select one, and a (selectable) list of all the ppl in it should show up.

Each person’s thing should: 
Employee ID
Department + Sub Department
Monitor model / PC model 
Ram
Storage Space
OS Version 
Webcam Specs 
Desk Phone Model 

Must be able to edit previous data
Must display all the depts on the first screen
Must be able to create sub-depts 
Must be able to add extra details to a person if needed 


General functionalities:

Flow 1 - Accessing an employee:
Begin with either a search (id#, name, department, etc.) or select a department 
Access database
View all members available based on the search or selection results 
Either have a member card, pop-up, or spreadsheet-style view of info 

Flow 2 - Adding an employee: 
Add employee by id# 
Checks if the employee exists
Add other info
Create an entry in the database

Flow 3 - Editing/Deleting an employee:
Find employee 
Edit information or delete the employee 
Update database

## Running with authentication

1. Install dependencies: `pip install -r requirements.txt`
2. Configure Firebase in `config/firebase_config.py` and place `firebase-service-account.json` in the project root.
3. Create a user in Firebase Console → Authentication → Users.

**Run the app (API starts automatically):**
```bash
cd Ascent-Inventory
python3 main.py
```

The desktop app launches a local API in the background on `API_BASE_URL` (default `http://127.0.0.1:8000`). You do not need a second terminal.

To run the API alone for development:
```bash
uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
```

After your first login, promote yourself to admin:
```bash
sqlite3 backend/inventory.db "UPDATE app_users SET role = 'admin' WHERE email = 'you@company.com';"
```

Roles: `viewer` (read-only) and `admin` (full access).
