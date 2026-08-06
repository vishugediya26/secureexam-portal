from flask import request
from datetime import datetime
from app import db
from app.models import AuditLog

def log_access(user_id, action, paper_id=None):
    entry = AuditLog(
        user_id=user_id,
        action=action,
        paper_id=paper_id,
        ip_address=request.remote_addr,
        timestamp=datetime.utcnow()
    )
    db.session.add(entry)
    db.session.commit()