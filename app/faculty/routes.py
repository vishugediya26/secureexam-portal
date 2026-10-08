import csv
import io
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.decorators import role_required
from app import db
from app.models import Faculty, FacultyBusySlot
from app.faculty.scheduler import assign_duties_for_exam
from app.models import Exam, DutyAssignment
from flask_login import current_user
from app.audit import log_access

faculty_bp = Blueprint('faculty', __name__)

MAX_CSV_BYTES = 1024 * 1024  # 1 MB
MAX_ROWS = 2000
REQUIRED_COLUMNS = {'faculty_name', 'subject', 'day', 'start_time', 'end_time'}
VALID_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def parse_timetable_csv(raw_bytes):
    """Checks the whole file first. Returns (rows, errors). Nothing is saved here."""
    try:
        text = raw_bytes.decode('utf-8-sig')
    except UnicodeDecodeError:
        return [], ['The file is not valid UTF-8 text. Save it as CSV (UTF-8) and try again.']

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return [], ['The file is empty.']

    headers = {h.strip() for h in reader.fieldnames if h}
    missing = REQUIRED_COLUMNS - headers
    if missing:
        return [], ['Missing columns: ' + ', '.join(sorted(missing))]

    rows = []
    errors = []
    for line_no, row in enumerate(reader, start=2):
        clean = {k.strip(): (v or '').strip() for k, v in row.items() if k}

        name = clean['faculty_name']
        subject = clean['subject']
        raw_day = clean['day']
        day = raw_day.title()

        if not name or len(name) > 120:
            errors.append(f'Line {line_no}: faculty_name is empty or too long')
        if len(subject) > 120:
            errors.append(f'Line {line_no}: subject is too long')
        if day not in VALID_DAYS:
            errors.append(f'Line {line_no}: day "{raw_day}" is not a weekday name')

        start = None
        end = None
        try:
            start = datetime.strptime(clean['start_time'], '%H:%M').time()
        except ValueError:
            errors.append(f'Line {line_no}: start_time must look like 09:30')
        try:
            end = datetime.strptime(clean['end_time'], '%H:%M').time()
        except ValueError:
            errors.append(f'Line {line_no}: end_time must look like 10:30')
        if start and end and end <= start:
            errors.append(f'Line {line_no}: end_time must be after start_time')

        rows.append({'name': name, 'subject': subject, 'day': day, 'start': start, 'end': end})

        if len(rows) > MAX_ROWS:
            return [], [f'Too many rows (limit is {MAX_ROWS}).']

    if not rows:
        return [], ['The file has no data rows.']
    return rows, errors


@faculty_bp.route('/faculty/upload', methods=['GET', 'POST'])
@login_required
@role_required('coordinator')
def upload_timetable():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if not file or not file.filename:
            flash('No file selected')
            return redirect(url_for('faculty.upload_timetable'))

        if not file.filename.lower().endswith('.csv'):
            flash('Only .csv files are allowed')
            return redirect(url_for('faculty.upload_timetable'))

        raw = file.stream.read(MAX_CSV_BYTES + 1)
        if len(raw) > MAX_CSV_BYTES:
            flash('The file is too large (limit is 1 MB)')
            return redirect(url_for('faculty.upload_timetable'))

        rows, errors = parse_timetable_csv(raw)
        if errors:
            shown = errors[:5]
            message = 'Import rejected, nothing was saved. ' + ' | '.join(shown)
            if len(errors) > len(shown):
                message += f' (and {len(errors) - len(shown)} more problems)'
            flash(message)
            return redirect(url_for('faculty.upload_timetable'))

        added = 0
        skipped = 0
        for r in rows:
            faculty = Faculty.query.filter_by(name=r['name']).first()
            if not faculty:
                faculty = Faculty(name=r['name'])
                db.session.add(faculty)
                db.session.flush()

            exists = FacultyBusySlot.query.filter_by(
                faculty_id=faculty.id, day=r['day'],
                start_time=r['start'], end_time=r['end']
            ).first()
            if exists:
                skipped += 1
                continue

            db.session.add(FacultyBusySlot(
                faculty_id=faculty.id,
                subject=r['subject'],
                day=r['day'],
                start_time=r['start'],
                end_time=r['end']
            ))
            added += 1

        db.session.commit()
        flash(f'Imported {added} new timetable entries ({skipped} duplicates skipped)')
        return redirect(url_for('faculty.list_faculty'))

    return render_template('faculty/upload.html')


@faculty_bp.route('/faculty')
@login_required
@role_required('coordinator')
def list_faculty():
    all_faculty = Faculty.query.all()
    return render_template('faculty/list.html', all_faculty=all_faculty)


@faculty_bp.route('/faculty/assign/<int:exam_id>', methods=['POST'])
@login_required
@role_required('coordinator')
def assign_duty(exam_id):
    num = request.form.get('num_invigilators', default=1, type=int)
    num = max(1, min(num, 10))
    assigned = assign_duties_for_exam(exam_id, num_invigilators=num)
    log_access(user_id=current_user.id, username=current_user.username, action='ASSIGN_DUTY')
    if assigned:
        names = ', '.join(f.name for f in assigned)
        if len(assigned) < num:
            flash(f'Assigned {len(assigned)} of {num} requested: {names}. The rest are busy or already assigned.')
        else:
            flash(f'Assigned: {names}')
    else:
        flash('No available faculty found for this exam slot')
    return redirect(url_for('exams.list_exams'))


@faculty_bp.route('/faculty/duty-chart')
@login_required
@role_required('coordinator')
def duty_chart():
    exams = Exam.query.order_by(Exam.scheduled_start).all()
    chart = []
    for exam in exams:
        assignments = DutyAssignment.query.filter_by(exam_id=exam.id).all()
        names = []
        for a in assignments:
            f = db.session.get(Faculty, a.faculty_id)
            if f:
                names.append(f.name)
        chart.append({'exam': exam, 'faculty_names': names})
    return render_template('faculty/duty_chart.html', chart=chart)