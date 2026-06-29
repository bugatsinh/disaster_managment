import os
import sqlite3

BASE_DIR = os.path.dirname(__file__)
DATABASE = os.path.join(BASE_DIR, 'emergency_reports.db')


def get_db_connection():
    """Open a SQLite connection and configure row factory for dict-like access."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_column(connection, table, column, definition):
    """Add a missing column to a table when it does not already exist."""
    columns = connection.execute(f'PRAGMA table_info({table})').fetchall()
    if column not in {item['name'] for item in columns}:
        connection.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')


def init_db():
    """Create required database tables and ensure all expected columns exist."""
    with get_db_connection() as connection:
        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS victim_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                location TEXT NOT NULL,
                problem TEXT NOT NULL,
                people_affected INTEGER NOT NULL DEFAULT 0,
                medical_emergency TEXT NOT NULL DEFAULT 'no',
                children INTEGER NOT NULL DEFAULT 0,
                old_people INTEGER NOT NULL DEFAULT 0,
                photo_filename TEXT,
                help_arrived TEXT NOT NULL DEFAULT 'unknown',
                victim_rescued INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'open',
                completed_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )
        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS volunteer_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                volunteer_name TEXT NOT NULL,
                volunteer_email TEXT NOT NULL,
                response TEXT NOT NULL,
                volunteer_rescued INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (report_id) REFERENCES victim_reports (id)
            )
            '''
        )
        ensure_column(connection, 'victim_reports', 'help_arrived', "TEXT NOT NULL DEFAULT 'unknown'")
        ensure_column(connection, 'victim_reports', 'victim_rescued', 'INTEGER NOT NULL DEFAULT 0')
        ensure_column(connection, 'victim_reports', 'status', "TEXT NOT NULL DEFAULT 'open'")
        ensure_column(connection, 'victim_reports', 'completed_at', 'TEXT')
        ensure_column(connection, 'volunteer_responses', 'volunteer_rescued', 'INTEGER NOT NULL DEFAULT 0')


def to_int(value, default=0):
    """Convert a value to a non-negative integer, returning a default if conversion fails."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(number, 0)


def row_to_dict(row):
    """Convert a database row into a dictionary and add human-readable labels."""
    report = dict(row)
    if 'medical_emergency' in report:
        report['medical_emergency_label'] = report['medical_emergency'].capitalize()
    if 'help_arrived' in report:
        report['help_arrived_label'] = {
            'yes': 'Arrived',
            'no': 'Not arrived',
            'unknown': 'Not updated',
        }.get(report['help_arrived'], 'Not updated')
    if 'status' in report:
        report['status_label'] = 'Complete' if report['status'] == 'complete' else 'Open'
    if 'victim_rescued' in report:
        report['victim_rescued_label'] = 'Yes' if report['victim_rescued'] else 'No'
    return report


def refresh_report_status(connection, report_id):
    """Refresh a report's completion status and remove it when completed."""
    report = connection.execute(
        'SELECT victim_rescued FROM victim_reports WHERE id = ?',
        (report_id,),
    ).fetchone()
    if report is None:
        return None

    rescued_volunteers = connection.execute(
        '''
        SELECT COUNT(*) AS total
        FROM volunteer_responses
        WHERE report_id = ? AND response = 'participate' AND volunteer_rescued = 1
        ''',
        (report_id,),
    ).fetchone()['total']
    is_complete = bool(report['victim_rescued']) and rescued_volunteers > 0
    if is_complete:
        connection.execute(
            'DELETE FROM volunteer_responses WHERE report_id = ?',
            (report_id,),
        )
        connection.execute(
            'DELETE FROM victim_reports WHERE id = ?',
            (report_id,),
        )
    else:
        connection.execute(
            '''
            UPDATE victim_reports
            SET status = 'open'
            WHERE id = ?
            ''',
            (report_id,),
        )
    return is_complete
