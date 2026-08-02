from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime
from app import db
from app.models import Exam

exams_bp = Blueprint('exams', __name__)

@exams_bp.route('/exams')
def list_exams():
    exams = Exam.query.all()
    return render_template('exams/list.html', exams=exams)

@exams_bp.route('/exams/new', methods=['GET', 'POST'])
def new_exam():
    if request.method == 'POST':
        subject = request.form['subject']
        scheduled_start = datetime.strptime(request.form['scheduled_start'], '%Y-%m-%dT%H:%M')
        duration_minutes = int(request.form['duration_minutes'])
        exam = Exam(subject=subject, scheduled_start=scheduled_start, duration_minutes=duration_minutes)
        db.session.add(exam)
        db.session.commit()
        return redirect(url_for('exams.list_exams'))
    return render_template('exams/new.html')