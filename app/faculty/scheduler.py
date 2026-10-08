from app import db
from app.models import Exam
from app.models import Faculty, FacultyBusySlot, DutyAssignment

def is_faculty_free(faculty, exam):
    exam_day = exam.scheduled_start.strftime('%A')
    exam_start = exam.scheduled_start.time()
    exam_end_minutes = exam.scheduled_start.hour * 60 + exam.scheduled_start.minute + exam.duration_minutes
    exam_end_hour = exam_end_minutes // 60
    exam_end_min = exam_end_minutes % 60
    exam_end = exam_start.replace(hour=exam_end_hour % 24, minute=exam_end_min)

    busy_slots = FacultyBusySlot.query.filter_by(faculty_id=faculty.id, day=exam_day).all()
    for slot in busy_slots:
        overlaps = slot.start_time < exam_end and exam_start < slot.end_time
        if overlaps:
            return False
    return True

def assign_duties_for_exam(exam_id, num_invigilators=1):
    exam = Exam.query.get_or_404(exam_id)

    existing = DutyAssignment.query.filter_by(exam_id=exam.id).all()
    already_assigned_ids = [d.faculty_id for d in existing]

    all_faculty = Faculty.query.order_by(Faculty.duty_count.asc()).all()

    assigned = []
    for faculty in all_faculty:
        if len(assigned) >= num_invigilators:
            break
        if faculty.id in already_assigned_ids:
            continue
        if is_faculty_free(faculty, exam):
            assignment = DutyAssignment(faculty_id=faculty.id, exam_id=exam.id)
            db.session.add(assignment)
            faculty.duty_count += 1
            assigned.append(faculty)

    db.session.commit()
    return assigned