from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime
from app import db
from app.models import Exam, Paper
from app.crypto_utils import encrypt_text

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

@exams_bp.route('/exams/<int:exam_id>/upload-paper', methods=['GET', 'POST'])
def upload_paper(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if request.method == 'POST':
        content = request.form['content']
        encrypted = encrypt_text(content)
        paper = Paper(exam_id=exam.id, setter_id=1, encrypted_content=encrypted)
        db.session.add(paper)
        db.session.commit()
        return redirect(url_for('exams.list_papers', exam_id=exam.id))
    return render_template('exams/upload_paper.html', exam=exam)

@exams_bp.route('/exams/<int:exam_id>/papers')
def list_papers(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    papers = Paper.query.filter_by(exam_id=exam.id).all()
    return render_template('exams/papers.html', exam=exam, papers=papers)