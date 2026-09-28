from functools import wraps

import mysql.connector
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


# ---------- Database helper ----------
def query(sql, args=(), one=False, commit=False):
    conn = mysql.connector.connect(**config.DB_CONFIG)
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, args)
        if commit:
            conn.commit()
            return cur.lastrowid
        rows = cur.fetchall()
        return (rows[0] if rows else None) if one else rows
    finally:
        cur.close()
        conn.close()


def create_default_admin():
    if not query("SELECT id FROM users WHERE role='admin'", one=True):
        query(
            "INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,'admin')",
            ("Admin", config.ADMIN_EMAIL, generate_password_hash(config.ADMIN_PASSWORD)),
            commit=True,
        )


# ---------- Auth decorators ----------
def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if session.get("role") != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapper


# ---------- Common routes ----------
@app.route("/")
def index():
    return redirect(url_for("dashboard" if "user_id" in session else "login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        pwd = request.form["password"]
        if not name or not email or len(pwd) < 4:
            flash("Sab fields bharo (password min 4 characters).", "error")
        elif query("SELECT id FROM users WHERE email=%s", (email,), one=True):
            flash("Ye email already registered hai.", "error")
        else:
            query(
                "INSERT INTO users (name,email,password) VALUES (%s,%s,%s)",
                (name, email, generate_password_hash(pwd)),
                commit=True,
            )
            flash("Registration successful! Ab login karo.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        user = query("SELECT * FROM users WHERE email=%s", (email,), one=True)
        if user and check_password_hash(user["password"], request.form["password"]):
            session.update(user_id=user["id"], name=user["name"], role=user["role"])
            return redirect(url_for("admin" if user["role"] == "admin" else "dashboard"))
        flash("Galat email ya password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- Student ----------
@app.route("/dashboard")
@login_required
def dashboard():
    if session["role"] == "admin":
        return redirect(url_for("admin"))
    exams = query(
        """SELECT e.*, (SELECT COUNT(*) FROM questions q WHERE q.exam_id=e.id) AS qcount,
                  r.score, r.total
           FROM exams e LEFT JOIN results r ON r.exam_id=e.id AND r.user_id=%s
           ORDER BY e.id DESC""",
        (session["user_id"],),
    )
    return render_template("dashboard.html", exams=exams)


@app.route("/exam/<int:exam_id>")
@login_required
def take_exam(exam_id):
    exam = query("SELECT * FROM exams WHERE id=%s", (exam_id,), one=True)
    if not exam:
        flash("Exam nahi mila.", "error")
        return redirect(url_for("dashboard"))
    if query("SELECT id FROM results WHERE user_id=%s AND exam_id=%s",
             (session["user_id"], exam_id), one=True):
        flash("Aap ye exam already de chuke ho.", "error")
        return redirect(url_for("dashboard"))
    questions = query("SELECT * FROM questions WHERE exam_id=%s", (exam_id,))
    if not questions:
        flash("Is exam mein abhi questions nahi hain.", "error")
        return redirect(url_for("dashboard"))
    return render_template("exam.html", exam=exam, questions=questions)


@app.route("/exam/<int:exam_id>/submit", methods=["POST"])
@login_required
def submit_exam(exam_id):
    if query("SELECT id FROM results WHERE user_id=%s AND exam_id=%s",
             (session["user_id"], exam_id), one=True):
        return redirect(url_for("dashboard"))
    questions = query("SELECT id, correct FROM questions WHERE exam_id=%s", (exam_id,))
    score = sum(1 for q in questions if request.form.get(f"q{q['id']}") == q["correct"])
    rid = query(
        "INSERT INTO results (user_id,exam_id,score,total) VALUES (%s,%s,%s,%s)",
        (session["user_id"], exam_id, score, len(questions)),
        commit=True,
    )
    return redirect(url_for("result", result_id=rid))


@app.route("/result/<int:result_id>")
@login_required
def result(result_id):
    r = query(
        """SELECT r.*, e.title FROM results r JOIN exams e ON e.id=r.exam_id
           WHERE r.id=%s AND r.user_id=%s""",
        (result_id, session["user_id"]),
        one=True,
    )
    if not r:
        return redirect(url_for("dashboard"))
    r["percent"] = round(r["score"] * 100 / r["total"], 1) if r["total"] else 0
    return render_template("result.html", r=r)


# ---------- Admin ----------
@app.route("/admin")
@admin_required
def admin():
    exams = query(
        """SELECT e.*, (SELECT COUNT(*) FROM questions q WHERE q.exam_id=e.id) AS qcount
           FROM exams e ORDER BY e.id DESC"""
    )
    return render_template("admin.html", exams=exams)


@app.route("/admin/exam/add", methods=["POST"])
@admin_required
def add_exam():
    title = request.form["title"].strip()
    duration = int(request.form.get("duration") or 10)
    if title:
        query("INSERT INTO exams (title,duration_min) VALUES (%s,%s)", (title, duration), commit=True)
        flash("Exam create ho gaya.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/exam/<int:exam_id>/delete", methods=["POST"])
@admin_required
def delete_exam(exam_id):
    query("DELETE FROM exams WHERE id=%s", (exam_id,), commit=True)
    flash("Exam delete ho gaya.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/exam/<int:exam_id>", methods=["GET", "POST"])
@admin_required
def manage_questions(exam_id):
    exam = query("SELECT * FROM exams WHERE id=%s", (exam_id,), one=True)
    if not exam:
        return redirect(url_for("admin"))
    if request.method == "POST":
        f = request.form
        query(
            """INSERT INTO questions (exam_id,question,opt_a,opt_b,opt_c,opt_d,correct)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (exam_id, f["question"], f["opt_a"], f["opt_b"], f["opt_c"], f["opt_d"], f["correct"]),
            commit=True,
        )
        flash("Question add ho gaya.", "success")
        return redirect(url_for("manage_questions", exam_id=exam_id))
    questions = query("SELECT * FROM questions WHERE exam_id=%s", (exam_id,))
    return render_template("admin_exam.html", exam=exam, questions=questions)


@app.route("/admin/question/<int:qid>/delete", methods=["POST"])
@admin_required
def delete_question(qid):
    q = query("SELECT exam_id FROM questions WHERE id=%s", (qid,), one=True)
    query("DELETE FROM questions WHERE id=%s", (qid,), commit=True)
    return redirect(url_for("manage_questions", exam_id=q["exam_id"] if q else 0))


@app.route("/admin/results")
@admin_required
def all_results():
    rows = query(
        """SELECT u.name, u.email, e.title, r.score, r.total, r.taken_at
           FROM results r JOIN users u ON u.id=r.user_id JOIN exams e ON e.id=r.exam_id
           ORDER BY r.taken_at DESC"""
    )
    return render_template("admin_results.html", rows=rows)


if __name__ == "__main__":
    create_default_admin()
    app.run(debug=True)
