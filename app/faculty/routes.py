import csv
import io
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.decorators import role_required
from app import db
from app.models import Faculty, FacultyBusySlot

faculty_bp = Blueprint('faculty', __name__)

@faculty_bp.route('/faculty/upload', methods=['GET', 'POST'])
@login_required
@role_required('coordinator')
def upload_timetable():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if not file:
            flash('No file selected')
            return redirect(url_for('faculty.upload_timetable'))

        stream = io.StringIO(file.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)

        count = 0
        for row in reader:
            faculty_name = row['faculty_name'].strip()
            subject = row['subject'].strip()
            day = row['day'].strip()
            start_time = datetime.strptime(row['start_time'].strip(), '%H:%M').time()
            end_time = datetime.strptime(row['end_time'].strip(), '%H:%M').time()

            faculty = Faculty.query.filter_by(name=faculty_name).first()
            if not faculty:
                faculty = Faculty(name=faculty_name)
                db.session.add(faculty)
                db.session.commit()

            slot = FacultyBusySlot(
                faculty_id=faculty.id,
                subject=subject,
                day=day,
                start_time=start_time,
                end_time=end_time
            )
            db.session.add(slot)
            count += 1

        db.session.commit()
        flash(f'Successfully imported {count} timetable entries')
        return redirect(url_for('faculty.list_faculty'))

    return render_template('faculty/upload.html')

@faculty_bp.route('/faculty')
@login_required
@role_required('coordinator')
def list_faculty():
    all_faculty = Faculty.query.all()
    return render_template('faculty/list.html', all_faculty=all_faculty)