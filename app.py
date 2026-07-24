from flask import Flask, render_template, request, redirect, session
from db import Base, engine, SessionLocal
import models
import PyPDF2
import docx
import json

# Import your AI function
from ai import analyse_resume, evaluate_answer

app = Flask(__name__)
app.secret_key = "secret123"

import re
@app.template_filter('extract_name')
def extract_name_filter(text):
    if not text:
        return "Resume"
    # Get the first line
    first_line = text.strip().split('\n')[0]
    # Remove email patterns
    first_line = re.sub(r'\S+@\S+', '', first_line)
    # Split by bullets, vertical pipes or hyphens
    first_line = first_line.split('•')[0].split('|')[0].split('-')[0]
    # Remove phone number sequences (digits with spaces/hyphens)
    first_line = re.sub(r'[\d\s\-]{8,}', '', first_line)
    return first_line.strip() or "Resume"

# Create tables
Base.metadata.create_all(bind=engine)

# -------------------- HOME --------------------
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")
# -------------------- SIGNUP --------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    db = SessionLocal()
    try:
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            existing_user = db.query(models.User).filter_by(email=email).first()
            if existing_user:
                return "User already exists."
            user = models.User(
                email=email,
                password=password
            )
            db.add(user)
            db.commit()
            return redirect("/login")
        return render_template("signup.html")
    finally:
        db.close()
# -------------------- LOGIN --------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    db = SessionLocal()
    try:
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            user = db.query(models.User).filter_by(
                email=email,
                password=password
            ).first()
            if user:
                session["user"] = user.email
                return redirect("/dashboard")
            return "Invalid Credentials."
        return render_template("login.html")
    finally:
        db.close()

# -------------------- FORGET PASSWORD --------------------
@app.route("/forget", methods=["GET", "POST"])
def forget():
    db = SessionLocal()
    try:
        if request.method == "POST":
            email = request.form.get("email")
            new_password = request.form.get("password")
            user = db.query(models.User).filter_by(email=email).first()
            if user:
                user.password = new_password
                db.commit()
                return redirect("/login")
            return "User not found."
        return render_template("forget.html")
    finally:
        db.close()

# -------------------- DASHBOARD --------------------

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")
    result = None
    if request.method == "POST":
        user_goal = request.form.get("role")
        resume_text = request.form.get("resume")
        file = request.files.get("file")
        # -------- PDF / DOCX Upload --------

        if file and file.filename != "":
            filename = file.filename.lower()
            if filename.endswith(".pdf"):
                try:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""
                    resume_text = text
                except Exception as e:
                    result = {
                        "error": f"PDF Error: {str(e)}"
                    }
            elif filename.endswith(".docx"):
                try:
                    document = docx.Document(file)
                    text = ""
                    for para in document.paragraphs:
                        text += para.text + "\n"
                    resume_text = text
                except Exception as e:
                    result = {
                        "error": f"DOCX Error: {str(e)}"
                    }
            else:
                result = {
                    "error": "Only PDF and DOCX files are supported."
                }
        # -------- AI Analysis --------

        if resume_text and user_goal and result is None:
            try:
                result = analyse_resume(
                    resume_text,
                    user_goal
                )
                db = SessionLocal()
                try:
                    user = db.query(models.User).filter_by(
                        email=session["user"]
                    ).first()
                    report = models.Report(
                        user_id=user.id,
                        resume_text=resume_text,
                        results=json.dumps(result)
                    )
                    db.add(report)
                    db.commit()
                finally:
                    db.close()
            except Exception as e:
                result = {
                    "error": f"AI Error: {str(e)}"
                }
    return render_template(
        "dashboard.html",
        user=session["user"],
        result=result
    )
# -------------------- HISTORY --------------------

@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")
    db = SessionLocal()
    try:
        user = db.query(models.User).filter_by(
            email=session["user"]
        ).first()
        reports = db.query(models.Report).filter_by(
            user_id=user.id
        ).all()
        parsed_reports = []
        for report in reports:
            try:
                parsed_result = json.loads(report.results)
            except:
                parsed_result = {}
            parsed_reports.append({
                "resume": report.resume_text,
                "result": parsed_result
            })
        return render_template(
            "history.html",
            reports=parsed_reports
        )

    finally:
        db.close()

# -------------------- LOGOUT --------------------

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# -------------------- MOCK INTERVIEW API --------------------
@app.route("/api/interview-feedback", methods=["POST"])
def interview_feedback():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    data = request.json or {}
    question = data.get("question")
    answer = data.get("answer")
    if not question or not answer:
        return {"error": "Missing question or answer"}, 400
    
    feedback = evaluate_answer(question, answer)
    return feedback

# -------------------- RUN APP --------------------
if __name__ == "__main__":
    app.run(debug=True, port=8000)
