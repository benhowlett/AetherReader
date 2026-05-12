from flask import Flask, render_template, request, session, jsonify
from models import db, User, Credential
from passkey_utils import server, get_registration_options
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aetherreader.db'
app.config['SECRET_KEY'] = os.urandom(24) # Needed for sessions
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-registration-options', methods=['POST'])
def generate_registration():
    username = request.json.get('username')
    # Check if user exists or create a temp one
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()

    options, state = get_registration_options(user.id, user.username)
    session['registration_state'] = state
    return jsonify(dict(options))

@app.route('/verify-registration', methods=['POST'])
def verify_registration():
    # Here we would verify the 'attestation' sent back by the browser
    # and save the Public Key to the Credential table.
    return jsonify({"status": "success"})

if __name__ == '__main__':
    # On your Mac, use 'ssl_context' because WebAuthn requires HTTPS
    app.run(debug=True, port=5000, ssl_context='adhoc')