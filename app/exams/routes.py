from flask import Blueprint, render_template, request, redirect, url_for, abort
from datetime import datetime, timedelta
from app import db
from flask_login import login_required, current_user
from app.decorators import role_required
from app.crypto_utils import encrypt_text, decrypt_text
from app.models import Exam, Paper
from app.audit import log_access
from app.models import AuditLog

exams_bp = Blueprint('exams', __name__)

# Invigilators can open a paper from this many minutes before the exam starts
UNLOCK_MINUTES_BEFORE = 30


@exams_bp.route('/exams')
@login_required
def list_exams():
    exams = Exam.query.all()
    return render_template('exams/list.html', exams=exams)


@exams_bp.route('/exams/new', methods=['GET', 'POST'])
@login_required
@role_required('coordinator')
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
@login_required
@role_required('setter')
def upload_paper(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if request.method == 'POST':
        content = request.form['content']
        encrypted = encrypt_text(content)
        paper = Paper(exam_id=exam.id, setter_id=current_user.id, encrypted_content=encrypted)
        db.session.add(paper)
        db.session.commit()
        log_access(user_id=current_user.id, action='UPLOAD_PAPER', paper_id=paper.id)
        return redirect(url_for('exams.list_papers', exam_id=exam.id))
    return render_template('exams/upload_paper.html', exam=exam)


@exams_bp.route('/exams/<int:exam_id>/papers')
@login_required
def list_papers(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    papers = Paper.query.filter_by(exam_id=exam.id).all()
    return render_template('exams/papers.html', exam=exam, papers=papers)


@exams_bp.route('/exams/<int:exam_id>/papers/<int:paper_id>/view')
@login_required
def view_paper(exam_id, paper_id):
    exam = Exam.query.get_or_404(exam_id)
    paper = Paper.query.get_or_404(paper_id)

    # The paper must belong to the exam in the URL (stops mixing IDs to dodge the time-lock)
    if paper.exam_id != exam.id:
        abort(404)

    is_owner = (paper.setter_id == current_user.id)
    is_coordinator = (current_user.role == 'coordinator')
    is_invigilator = (current_user.role == 'invigilator')

    if not (is_owner or is_coordinator):
        # Anyone else must be an invigilator, and only inside the time window
        if not is_invigilator:
            log_access(user_id=current_user.id, action='ACCESS_DENIED', paper_id=paper.id)
            abort(403)

        window_open = exam.scheduled_start - timedelta(minutes=UNLOCK_MINUTES_BEFORE)
        window_close = exam.scheduled_start + timedelta(minutes=exam.duration_minutes)
        now = datetime.now()

        if now < window_open:
            log_access(user_id=current_user.id, action='ACCESS_DENIED_TOO_EARLY', paper_id=paper.id)
            abort(403, description=f'This paper is locked. It opens at {window_open:%d %b %Y %H:%M}.')
        if now > window_close:
            log_access(user_id=current_user.id, action='ACCESS_DENIED_EXAM_ENDED', paper_id=paper.id)
            abort(403, description='The exam window has closed.')

    decrypted_content = decrypt_text(paper.encrypted_content)
    log_access(user_id=current_user.id, action='VIEW_PAPER', paper_id=paper.id)
    return render_template('exams/view_paper.html', exam=exam, paper=paper, decrypted_content=decrypted_content)


@exams_bp.route('/audit-log')
@login_required
@role_required('coordinator')
def audit_log():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return render_template('audit_log.html', logs=logs)