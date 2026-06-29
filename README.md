# Ascent Inventory

A desktop inventory management app for tracking employees, departments, IT equipment, and lab instruments. Built with **PyQt6** for the UI and **FastAPI** for a local API backed by **SQLite**.

## Overview

The master database starts empty. You organize people into departments (and sub-departments), attach hardware details to each employee, and browse or search the inventory from a single desktop window. Firebase Authentication controls who can sign in; role-based access limits viewers to read-only use while admins can create, edit, and delete records.

## Requirements

### Data model

- **Departments** — top-level departments with optional sub-departments
- **Employees** — each person belongs to a department and can have free-form notes
- **Computers** — per-employee or department/lab equipment with:
  - Employee ID (when assigned to a person)
  - Department + sub-department
  - Monitor model / PC model
  - Processor, RAM, storage
  - OS version
  - Webcam specs
  - Desk phone model
  - Notes
- **Instruments** — lab equipment (model, serial number, notes) tied to a department

### Capabilities

- View all departments on the first screen; select one to see its members
- Create sub-departments
- Search by employee ID, name, department, and related fields
- Edit existing records and add extra details when needed
- Role-based UI: **viewer** (browse only) and **admin** (full access)

## User flows

### Flow 1 — Accessing an employee

1. Start with a search (ID, name, department, etc.) or select a department from the sidebar
2. View members matching the search or selection
3. Open a member to see their profile, assigned computers, and notes

### Flow 2 — Adding an employee

1. Choose **Add Employee** (admin only)
2. Enter an employee ID — the app checks whether that ID already exists
3. Fill in name, department, and any other details
4. Save to create the database entry

### Flow 3 — Editing or deleting an employee

1. Find the employee via search or department browse
2. Open their detail view
3. Edit information or delete the record (admin only)
4. Changes are persisted through the API

## Tech stack

| Layer      | Technology                          |
| ---------- | ----------------------------------- |
| Desktop UI | PyQt6                               |
| API        | FastAPI + Uvicorn                   |
| Database   | SQLite (`backend/inventory.db`)     |
| Auth       | Firebase Authentication + Admin SDK |

## Project structure

```
Ascent-Inventory/
├── main.py                 # Desktop app entry point
├── config/
│   └── firebase_config.py  # Firebase + API settings
├── frontend/               # PyQt6 UI, services, API client
├── backend/
│   ├── api/                # FastAPI routes and middleware
│   ├── database.py         # Schema and DB helpers
│   └── inventory.db        # SQLite database (created on first run)
├── seed.py                 # Optional sample data for testing
└── requirements.txt
```

## Roles

| Role    | Access                                      |
| ------- | ------------------------------------------- |
| viewer  | Browse departments, employees, and inventory |
| admin   | Create, edit, and delete all records         |
