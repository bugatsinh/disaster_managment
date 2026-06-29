from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from db import get_db_connection, ensure_column, to_int

admin_bp = Blueprint('admin', __name__)

# ── Credentials (change these before deploying) ──────────────────
ADMIN_ID       = 'admin2025'
ADMIN_PASSWORD = 'disaster@secure'

PRIORITY_LEVELS = ['immediate', 'high', 'medium', 'low']


def init_admin_columns():
    """Add admin-specific columns to victim_reports if they don't exist yet."""
    with get_db_connection() as conn:
        ensure_column(conn, 'victim_reports', 'priority',     "TEXT NOT NULL DEFAULT 'medium'")
        ensure_column(conn, 'victim_reports', 'admin_notes',  'TEXT')
        ensure_column(conn, 'victim_reports', 'assigned_to',  'TEXT')
        ensure_column(conn, 'victim_reports', 'resolved_at',  'TEXT')


def get_admin():
    """Return admin identity from session or None."""
    return session.get('admin')


def require_admin():
    """Return redirect if not logged in, else None."""
    if not get_admin():
        flash('Admin login required.')
        return redirect(url_for('admin.admin_login_page'))
    return None


def get_all_reports_admin(filters=None):
    """Fetch ALL reports (including completed) with volunteer counts and optional filters."""
    filters = filters or {}
    where_clauses = []
    params = []

    priority = filters.get('priority')
    status   = filters.get('status')
    search   = filters.get('search', '').strip()

    if priority and priority in PRIORITY_LEVELS:
        where_clauses.append('r.priority = ?')
        params.append(priority)
    if status in ('open', 'complete'):
        where_clauses.append('r.status = ?')
        params.append(status)
    if search:
        where_clauses.append('(r.name LIKE ? OR r.location LIKE ? OR r.problem LIKE ?)')
        like = f'%{search}%'
        params += [like, like, like]

    where_sql = ('WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''

    with get_db_connection() as conn:
        rows = conn.execute(f'''
            SELECT r.id, r.name, r.phone, r.email, r.location, r.problem,
                   r.people_affected, r.medical_emergency, r.children, r.old_people,
                   r.help_arrived, r.victim_rescued, r.status, r.created_at,
                   r.completed_at, r.priority, r.admin_notes, r.assigned_to,
                   COALESCE(SUM(CASE WHEN vr.response = "participate" THEN 1 ELSE 0 END), 0) AS volunteers,
                   COALESCE(SUM(CASE WHEN vr.response = "participate" AND vr.volunteer_rescued = 1 THEN 1 ELSE 0 END), 0) AS rescued_volunteers
            FROM victim_reports r
            LEFT JOIN volunteer_responses vr ON vr.report_id = r.id
            {where_sql}
            GROUP BY r.id
            ORDER BY
                CASE r.priority WHEN "immediate" THEN 1 WHEN "high" THEN 2 WHEN "medium" THEN 3 ELSE 4 END,
                r.created_at DESC
        ''', params).fetchall()
    return [dict(row) for row in rows]


def get_stats():
    """Return dashboard stat counts."""
    with get_db_connection() as conn:
        total      = conn.execute('SELECT COUNT(*) FROM victim_reports').fetchone()[0]
        open_count = conn.execute("SELECT COUNT(*) FROM victim_reports WHERE status != 'complete'").fetchone()[0]
        complete   = conn.execute("SELECT COUNT(*) FROM victim_reports WHERE status = 'complete'").fetchone()[0]
        immediate  = conn.execute("SELECT COUNT(*) FROM victim_reports WHERE priority = 'immediate' AND status != 'complete'").fetchone()[0]
        medical    = conn.execute("SELECT COUNT(*) FROM victim_reports WHERE medical_emergency = 'yes' AND status != 'complete'").fetchone()[0]
        volunteers = conn.execute("SELECT COUNT(DISTINCT volunteer_email) FROM volunteer_responses").fetchone()[0]
        people     = conn.execute("SELECT COALESCE(SUM(people_affected), 0) FROM victim_reports").fetchone()[0]
    return dict(total=total, open=open_count, complete=complete,
                immediate=immediate, medical=medical,
                volunteers=volunteers, people=people)


# ── Routes ────────────────────────────────────────────────────────

@admin_bp.route('/admin/login', methods=['GET'])
def admin_login_page():
    if get_admin():
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('admin_login.html')


@admin_bp.route('/admin/login', methods=['POST'])
def admin_login():
    admin_id  = request.form.get('admin_id', '').strip()
    password  = request.form.get('password', '').strip()
    if admin_id == ADMIN_ID and password == ADMIN_PASSWORD:
        session['admin'] = {'id': admin_id}
        flash('Welcome, Admin.')
        return redirect(url_for('admin.admin_dashboard'))
    flash('Invalid admin ID or password.')
    return redirect(url_for('admin.admin_login_page'))


@admin_bp.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin', None)
    flash('Logged out of admin panel.')
    return redirect(url_for('admin.admin_login_page'))


@admin_bp.route('/admin', methods=['GET'])
def admin_dashboard():
    guard = require_admin()
    if guard:
        return guard
    filters = {
        'priority': request.args.get('priority', ''),
        'status':   request.args.get('status', ''),
        'search':   request.args.get('search', ''),
    }
    reports = get_all_reports_admin(filters)
    stats   = get_stats()
    return render_template('admin.html',
                           reports=reports, stats=stats,
                           filters=filters,
                           priority_levels=PRIORITY_LEVELS)


@admin_bp.route('/admin/set-priority', methods=['POST'])
def set_priority():
    guard = require_admin()
    if guard:
        return guard
    report_id = to_int(request.form.get('report_id'))
    priority  = request.form.get('priority', '').strip().lower()
    if not report_id or priority not in PRIORITY_LEVELS:
        flash('Invalid priority update.')
        return redirect(url_for('admin.admin_dashboard'))
    with get_db_connection() as conn:
        conn.execute('UPDATE victim_reports SET priority = ? WHERE id = ?', (priority, report_id))
    flash(f'Priority set to "{priority}" for report #{report_id}.')
    return redirect(url_for('admin.admin_dashboard') + _qs())


@admin_bp.route('/admin/set-notes', methods=['POST'])
def set_notes():
    guard = require_admin()
    if guard:
        return guard
    report_id  = to_int(request.form.get('report_id'))
    notes      = request.form.get('admin_notes', '').strip()
    assigned   = request.form.get('assigned_to', '').strip()
    if not report_id:
        flash('Invalid report.')
        return redirect(url_for('admin.admin_dashboard'))
    with get_db_connection() as conn:
        conn.execute('UPDATE victim_reports SET admin_notes = ?, assigned_to = ? WHERE id = ?',
                     (notes, assigned, report_id))
    flash(f'Notes saved for report #{report_id}.')
    return redirect(url_for('admin.admin_dashboard') + _qs())


@admin_bp.route('/admin/delete', methods=['POST'])
def delete_report():
    guard = require_admin()
    if guard:
        return guard
    report_id = to_int(request.form.get('report_id'))
    if not report_id:
        flash('Invalid report ID.')
        return redirect(url_for('admin.admin_dashboard'))
    with get_db_connection() as conn:
        conn.execute('DELETE FROM volunteer_responses WHERE report_id = ?', (report_id,))
        conn.execute('DELETE FROM victim_reports WHERE id = ?', (report_id,))
    flash(f'Report #{report_id} and all its volunteer responses have been deleted.')
    return redirect(url_for('admin.admin_dashboard') + _qs())


@admin_bp.route('/admin/mark-complete', methods=['POST'])
def mark_complete():
    guard = require_admin()
    if guard:
        return guard
    report_id = to_int(request.form.get('report_id'))
    if not report_id:
        flash('Invalid report ID.')
        return redirect(url_for('admin.admin_dashboard'))
    with get_db_connection() as conn:
        conn.execute("""UPDATE victim_reports
                        SET status = 'complete', completed_at = CURRENT_TIMESTAMP
                        WHERE id = ?""", (report_id,))
    flash(f'Report #{report_id} marked as complete.')
    return redirect(url_for('admin.admin_dashboard') + _qs())


@admin_bp.route('/admin/reopen', methods=['POST'])
def reopen_report():
    guard = require_admin()
    if guard:
        return guard
    report_id = to_int(request.form.get('report_id'))
    if not report_id:
        flash('Invalid report ID.')
        return redirect(url_for('admin.admin_dashboard'))
    with get_db_connection() as conn:
        conn.execute("UPDATE victim_reports SET status = 'open', completed_at = NULL WHERE id = ?",
                     (report_id,))
    flash(f'Report #{report_id} reopened.')
    return redirect(url_for('admin.admin_dashboard') + _qs())


@admin_bp.route('/api/admin/stats')
def api_stats():
    guard = require_admin()
    if guard:
        return jsonify({'ok': False}), 401
    return jsonify(get_stats())


def _qs():
    """Preserve active filter query string on redirects."""
    parts = []
    for k in ('priority', 'status', 'search'):
        v = request.form.get(k) or request.args.get(k, '')
        if v:
            parts.append(f'{k}={v}')
    return ('?' + '&'.join(parts)) if parts else ''
