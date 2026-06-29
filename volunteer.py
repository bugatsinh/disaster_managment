from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for, flash

from db import get_db_connection, refresh_report_status, to_int
from location_utils import sort_by_nearest

volunteer_bp = Blueprint('volunteer', __name__)


def get_logged_in_volunteer():
    """Return the logged-in volunteer identity from the session."""
    volunteer = session.get('volunteer')
    if not volunteer or not volunteer.get('name') or not volunteer.get('email') or not volunteer.get('location'):
        return None
    return volunteer


def get_volunteer_emergencies(volunteer_location=None):
    """Fetch emergency summaries, sorted nearest to farthest from the volunteer."""
    with get_db_connection() as connection:
        rows = connection.execute(
            '''
            SELECT r.id, r.location, r.problem, r.people_affected, r.children,
                   r.old_people, r.help_arrived, r.victim_rescued, r.status,
                   r.medical_emergency,
                   COALESCE(SUM(CASE WHEN vr.response = 'participate' THEN 1 ELSE 0 END), 0) AS participating_volunteers,
                   COALESCE(SUM(CASE WHEN vr.response = 'participate' AND vr.volunteer_rescued = 1 THEN 1 ELSE 0 END), 0) AS rescued_volunteers
            FROM victim_reports r
            LEFT JOIN volunteer_responses vr ON vr.report_id = r.id
            WHERE r.status != 'complete'
            GROUP BY r.id
            ORDER BY r.created_at DESC, r.id DESC
            '''
        ).fetchall()

    emergencies = [
        {
            'id': row['id'],
            'type': 'Medical Emergency' if row['medical_emergency'] == 'yes' else 'General Emergency',
            'medical_emergency': row['medical_emergency'],
            'location': row['location'] or 'Location not provided',
            'people_affected': row['people_affected'],
            'children': row['children'],
            'elderly': row['old_people'],
            'help_arrived': row['help_arrived'],
            'victim_rescued': bool(row['victim_rescued']),
            'participating_volunteers': row['participating_volunteers'],
            'rescued_volunteers': row['rescued_volunteers'],
            'status': row['status'],
            'details': row['problem'] or 'No problem description provided.',
        }
        for row in rows
    ]

    if volunteer_location:
        return sort_by_nearest(volunteer_location, emergencies)

    return emergencies


@volunteer_bp.route('/volunteer', methods=['GET'])
def volunteer():
    """Render the volunteer page showing available emergencies."""
    logged_in_volunteer = get_logged_in_volunteer()
    emergencies = []
    if logged_in_volunteer:
        emergencies = get_volunteer_emergencies(logged_in_volunteer['location'])

    return render_template(
        'volunteer.html',
        emergencies=emergencies,
        volunteer=logged_in_volunteer,
    )


@volunteer_bp.route('/volunteer-login', methods=['POST'])
def volunteer_login():
    """Log a volunteer in and prepare nearest-first emergency sorting."""
    name = request.form.get('volunteer_name', '').strip()
    email = request.form.get('volunteer_email', '').strip()
    location = request.form.get('volunteer_location', '').strip()

    if not name or not email or not location:
        flash('Enter your name, email, and location to view nearby emergencies.')
        return redirect(url_for('volunteer.volunteer'))

    session['volunteer'] = {
        'name': name,
        'email': email,
        'location': location,
    }
    flash(f'Welcome, {name}. Emergencies are sorted nearest to farthest from {location}.')
    return redirect(url_for('volunteer.volunteer'))


@volunteer_bp.route('/volunteer-logout', methods=['POST'])
def volunteer_logout():
    """Clear the volunteer session."""
    session.pop('volunteer', None)
    flash('You have been logged out.')
    return redirect(url_for('volunteer.volunteer'))


@volunteer_bp.route('/api/emergencies', methods=['GET'])
def api_emergencies():
    """Return emergency summaries sorted by distance for the logged-in volunteer."""
    logged_in_volunteer = get_logged_in_volunteer()
    if not logged_in_volunteer:
        return jsonify({'ok': False, 'message': 'Login required.'}), 401

    return jsonify(get_volunteer_emergencies(logged_in_volunteer['location']))


@volunteer_bp.route('/volunteer-response', methods=['POST'])
def volunteer_response():
    """Handle volunteer responses, record participation, and refresh report status."""
    logged_in_volunteer = get_logged_in_volunteer()
    report_id = to_int(request.form.get('report_id'))
    volunteer_name = request.form.get('volunteer_name', '').strip()
    volunteer_email = request.form.get('volunteer_email', '').strip()
    response = request.form.get('response', '').strip().lower()
    volunteer_rescued = 1 if request.form.get('volunteer_rescued') == 'yes' else 0

    if logged_in_volunteer:
        volunteer_name = logged_in_volunteer['name']
        volunteer_email = logged_in_volunteer['email']

    if not report_id or not volunteer_name or not volunteer_email or response not in {'participate', 'decline'}:
        return jsonify({'ok': False, 'message': 'Missing or invalid volunteer response.'}), 400

    with get_db_connection() as connection:
        report = connection.execute(
            'SELECT id, status FROM victim_reports WHERE id = ?',
            (report_id,),
        ).fetchone()
        if report is None:
            return jsonify({'ok': False, 'message': 'Report not found.'}), 404
        if report['status'] == 'complete':
            return jsonify({'ok': False, 'message': 'This emergency is already complete.'}), 400

        connection.execute(
            '''
            INSERT INTO volunteer_responses (
                report_id, volunteer_name, volunteer_email, response, volunteer_rescued
            )
            VALUES (?, ?, ?, ?, ?)
            ''',
            (report_id, volunteer_name, volunteer_email, response, volunteer_rescued),
        )
        complete = refresh_report_status(connection, report_id)

    message = (
        'You have chosen to participate in this emergency. Help is on the way.'
        if response == 'participate'
        else 'You have declined this request. Another volunteer may be notified.'
    )
    if complete:
        message = 'Both sides marked rescued. This emergency is now complete.'
    return jsonify({'ok': True, 'message': message, 'complete': complete})
