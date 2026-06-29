import os

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from db import get_db_connection, refresh_report_status, row_to_dict, to_int
from emergency_resources import get_all_helplines, get_emergency_resources
from location_utils import normalize_phone

victim_bp = Blueprint('victim', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    """Return True if the uploaded filename has an allowed image extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_all_reports(phone=None, name=None):
    """Fetch open victim reports, optionally filtered to one victim."""
    with get_db_connection() as connection:
        rows = connection.execute(
            '''
            SELECT r.id, r.name, r.phone, r.email, r.location, r.problem,
                   r.people_affected, r.medical_emergency, r.children,
                   r.old_people, r.photo_filename, r.help_arrived,
                   r.victim_rescued, r.status, r.completed_at, r.created_at,
                   COALESCE(SUM(CASE WHEN vr.response = 'participate' THEN 1 ELSE 0 END), 0) AS participating_volunteers,
                   COALESCE(SUM(CASE WHEN vr.response = 'participate' AND vr.volunteer_rescued = 1 THEN 1 ELSE 0 END), 0) AS rescued_volunteers
            FROM victim_reports r
            LEFT JOIN volunteer_responses vr ON vr.report_id = r.id
            WHERE r.status != 'complete'
            GROUP BY r.id
            ORDER BY r.created_at DESC, r.id DESC
            '''
        ).fetchall()

    reports = [row_to_dict(row) for row in rows]
    if phone and name:
        target_phone = normalize_phone(phone)
        target_name = name.strip().lower()
        reports = [
            report for report in reports
            if normalize_phone(report['phone']) == target_phone
            and report['name'].strip().lower() == target_name
        ]
    return reports


def get_logged_in_victim():
    """Return the logged-in victim identity from the session."""
    victim = session.get('victim')
    if not victim or not victim.get('phone') or not victim.get('name'):
        return None
    return victim


def victim_owns_report(connection, report_id, victim):
    """Return True when the report belongs to the logged-in victim."""
    report = connection.execute(
        'SELECT name, phone FROM victim_reports WHERE id = ?',
        (report_id,),
    ).fetchone()
    if report is None:
        return False

    return (
        normalize_phone(report['phone']) == normalize_phone(victim['phone'])
        and report['name'].strip().lower() == victim['name'].strip().lower()
    )


def save_report(report):
    """Insert a new victim report into the database and return the new report ID."""
    with get_db_connection() as connection:
        cursor = connection.execute(
            '''
            INSERT INTO victim_reports (
                name, phone, email, location, problem, people_affected,
                medical_emergency, children, old_people, photo_filename
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                report['name'],
                report['phone'],
                report['email'],
                report['location'],
                report['problem'],
                report['people_affected'],
                report['medical_emergency'],
                report['children'],
                report['old_people'],
                report['photo_filename'],
            ),
        )
        return cursor.lastrowid


@victim_bp.route('/victim-log', methods=['GET'])
def victim_log():
    """Render the victim log page with the current list of reports."""
    victim = get_logged_in_victim()
    emergency_resources = session.pop('emergency_resources', None)
    reports = []
    if victim:
        reports = get_all_reports(phone=victim['phone'], name=victim['name'])

    return render_template(
        'victim_log.html',
        reports=reports,
        emergency_resources=emergency_resources,
        helplines=get_all_helplines(),
        victim=victim,
    )


@victim_bp.route('/victim-login', methods=['POST'])
def victim_login():
    """Log a victim in using their name and phone number."""
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()

    if not name or not phone:
        flash('Enter your name and phone number to view your reports.')
        return redirect(url_for('victim.victim_log'))

    session['victim'] = {'name': name, 'phone': phone}
    flash(f'Welcome back, {name}. Showing your reports only.')
    return redirect(url_for('victim.victim_log'))


@victim_bp.route('/victim-logout', methods=['POST'])
def victim_logout():
    """Clear the victim session."""
    session.pop('victim', None)
    flash('You have been logged out.')
    return redirect(url_for('victim.victim_log'))


@victim_bp.route('/api/reports', methods=['GET'])
def api_reports():
    """Return open victim reports as JSON for the logged-in victim."""
    victim = get_logged_in_victim()
    if not victim:
        return jsonify({'ok': False, 'message': 'Login required.'}), 401
    return jsonify(get_all_reports(phone=victim['phone'], name=victim['name']))


@victim_bp.route('/submit_report', methods=['POST'])
@victim_bp.route('/submit-report', methods=['POST'])
def submit_report():
    """Forward report submission requests to the submit_victim handler."""
    return submit_victim()


@victim_bp.route('/submit_victim', methods=['POST'])
@victim_bp.route('/submit-victim', methods=['POST'])
def submit_victim():
    """Process a victim report form submission, validate input, and save the report."""
    victim = get_logged_in_victim()
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    location = request.form.get('location', '').strip()
    problem = request.form.get('problem', '').strip()
    people_affected = to_int(request.form.get('people_affected'))
    medical_emergency = request.form.get('medical_emergency', 'no').strip().lower()
    children = to_int(request.form.get('children'))
    old_people = to_int(request.form.get('old_people'))
    photo = request.files.get('photo')

    if not name or not phone or not location or not problem:
        flash('Name, phone, location and problem are required.')
        return redirect(url_for('victim.victim_log'))

    if victim and (
        victim['name'].strip().lower() != name.lower()
        or victim['phone'].strip() != phone.strip()
    ):
        flash('Report details must match your logged-in name and phone.')
        return redirect(url_for('victim.victim_log'))

    if medical_emergency not in {'yes', 'no'}:
        medical_emergency = 'no'

    photo_filename = None
    if photo and photo.filename:
        if allowed_file(photo.filename):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            photo_filename = secure_filename(photo.filename)
            photo.save(os.path.join(UPLOAD_FOLDER, photo_filename))
        else:
            flash('Photo must be a valid image file.')
            return redirect(url_for('victim.victim_log'))

    report = {
        'name': name,
        'phone': phone,
        'email': email,
        'location': location,
        'problem': problem,
        'people_affected': people_affected,
        'medical_emergency': medical_emergency,
        'children': children,
        'old_people': old_people,
        'photo_filename': photo_filename,
    }
    save_report(report)
    session['victim'] = {'name': name, 'phone': phone}

    emergency_resources = get_emergency_resources(problem, location, medical_emergency)
    session['emergency_resources'] = emergency_resources
    flash('Report submitted. Call the helpline numbers below for immediate help.')

    return redirect(url_for('victim.victim_log'))


@victim_bp.route('/victim-status', methods=['POST'])
def victim_status():
    """Update the status of an existing victim report from the submitted form."""
    victim = get_logged_in_victim()
    if not victim:
        flash('Log in to update your reports.')
        return redirect(url_for('victim.victim_log'))

    report_id = to_int(request.form.get('report_id'))
    help_arrived = request.form.get('help_arrived', 'unknown').strip().lower()
    victim_rescued = 1 if request.form.get('victim_rescued') == 'yes' else 0

    if not report_id or help_arrived not in {'yes', 'no', 'unknown'}:
        flash('Invalid victim status update.')
        return redirect(url_for('victim.victim_log'))

    with get_db_connection() as connection:
        report = connection.execute(
            'SELECT id FROM victim_reports WHERE id = ?',
            (report_id,),
        ).fetchone()
        if report is None:
            flash('Report not found.')
            return redirect(url_for('victim.victim_log'))

        if not victim_owns_report(connection, report_id, victim):
            flash('You can only update your own reports.')
            return redirect(url_for('victim.victim_log'))

        connection.execute(
            '''
            UPDATE victim_reports
            SET help_arrived = ?, victim_rescued = ?
            WHERE id = ?
            ''',
            (help_arrived, victim_rescued, report_id),
        )
        complete = refresh_report_status(connection, report_id)

    flash('Emergency marked complete.' if complete else 'Victim status updated.')
    return redirect(url_for('victim.victim_log'))
