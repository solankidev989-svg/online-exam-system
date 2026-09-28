# Online Exam System (Python Flask + MySQL)

## Features
- Student registration / login (hashed passwords)
- Admin: exam create/delete, MCQ questions add/delete, sabhi results dekhna
- Student: exams list, timer ke saath exam, auto-submit, instant result (score, %, pass/fail)
- Ek student ek exam sirf ek baar de sakta hai

## Setup
1. Python 3 + MySQL install hona chahiye.
2. `pip install -r requirements.txt`
3. MySQL mein schema import karo:  `mysql -u root -p < schema.sql`
4. `config.py` mein apna MySQL password daalo.
5. Run: `python app.py`  ->  http://127.0.0.1:5000

## Default Admin
Email: admin@exam.com | Password: admin123  (pehli run par auto-create hota hai)

## Structure
app.py (routes + logic) | config.py | schema.sql | templates/ (HTML pages)
