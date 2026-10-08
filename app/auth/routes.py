from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
import bcrypt
from app import db, limiter
from app.models import User
from app.audit import log_access

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('5 per minute', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            login_user(user)
            log_access(user_id=user.id, username=user.username, action='LOGIN_SUCCESS')
            return redirect(url_for('exams.list_exams'))
        log_access(user_id=(user.id if user else None), username=username, action='LOGIN_FAILED')
        flash('Invalid username or password')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))