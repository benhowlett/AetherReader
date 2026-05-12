from flask import Flask, render_template, request, session, jsonify
from models import db, User, Credential
from passkey_utils import server, get_registration_options
import json
from cloud_services import setup_oauth

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aetherreader.db'
app.config['SECRET_KEY'] = os.urandom(24) # Needed for sessions
db.init_app(app)
oauth = setup_oauth(app)

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

@app.route('/login/<name>')
def cloud_login(name):
    client = oauth.create_client(name)
    redirect_uri = url_for('authorize', name=name, _external=True)
    return client.authorize_redirect(redirect_uri)

@app.route('/authorize/<name>')
def authorize(name):
    client = oauth.create_client(name)
    token = client.authorize_access_token()
    # Save this token in the SQLite database associated with the user
    # For now, we'll store it in the session to test
    session['cloud_token'] = token
    return 'Cloud storage connected! You can now select your book folder.'

@app.route('/list-folders')
def list_folders():
    # This logic will call the Google/Dropbox API to list folders 
    # so the user can choose where their library lives.
    pass

@app.route('/api/browse')
def browse_cloud():
    # In a real app, you'd get the token/provider from the DB based on the logged-in user
    token = session.get('cloud_token')
    provider = session.get('cloud_provider') 
    instance_url = os.getenv('NEXTCLOUD_INSTANCE_URL') if provider == 'nextcloud' else None
    
    bridge = CloudBridge(token, provider, instance_url)
    path = request.args.get('path', '/')
    files = bridge.list_folders(path)
    
    return jsonify(files)

if __name__ == '__main__':
    # On your Mac, use 'ssl_context' because WebAuthn requires HTTPS
    app.run(debug=True, port=5000, ssl_context='adhoc')