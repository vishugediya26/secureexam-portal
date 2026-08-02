# SecureExam Portal

An exam paper management system with time-locked, encrypted access — built to demonstrate insider-threat mitigation and data security controls.

## Tech Stack
- Backend: Python, Flask
- Database: SQLite (dev) → PostgreSQL (planned for later)
- ORM: SQLAlchemy
- Frontend: Jinja2 templates, Bootstrap 5

## How to Run Locally
1. Clone this repo
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with `SECRET_KEY` and `DATABASE_URL`
6. Run: `python run.py`
7. Visit `http://127.0.0.1:5000`

## Progress Log
- Week 1: Project setup, Flask app skeleton, database models (User, Exam, Paper, AuditLog) created and tested