from flask import Flask, redirect, url_for

from db import init_db
from victim import victim_bp
from volunteer import volunteer_bp

app = Flask(__name__)
app.secret_key = 'change-this-secret-key'

app.register_blueprint(victim_bp)
app.register_blueprint(volunteer_bp)

init_db()


@app.route('/', methods=['GET'])
def index():
    """Redirect the root URL to the victim log display page."""
    return redirect(url_for('victim.victim_log'))


if __name__ == '__main__':
    app.run(debug=True)
