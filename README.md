# 📝 Online Exam System

A web-based online examination system built with **Python (Flask)** and **MySQL**. Admins create exams and MCQ questions, students take timed tests and get instant results.

## Features
- Student registration and login (passwords are hashed)
- Admin panel: create/delete exams, add/delete MCQ questions, view all results
- Timed exams with countdown and auto-submit
- Instant result with score, percentage and pass/fail
- One attempt per student per exam

## Tech Stack
- Backend: Python, Flask
- Database: MySQL
- Frontend: HTML, CSS, JavaScript (Jinja2 templates)

## Project Structure
```
online_exam_system/
├── app.py            # routes and logic
├── config.py         # database settings
├── schema.sql        # database tables + sample exam
├── requirements.txt
└── templates/        # HTML pages
```

## Setup
1. Clone the repo:
   `git clone https://github.com/solankidev989-svg/online-exam-system.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Import the database: `mysql -u root -p < schema.sql`
4. Open `config.py` and set your MySQL password.
5. Run: `python app.py`
6. Open http://127.0.0.1:5000

## Default Admin Login
- Email: `admin@exam.com`
- Password: `admin123`

(Change this after the first login/setup.)

## Author
**Dev Solanki** — 
