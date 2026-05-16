import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, session, jsonify, Response, stream_with_context, url_for
from models import db, User, Credential
from passkey_utils import server, get_registration_options
import json, requests
from cloud_services import setup_oauth
from cloud_bridge import CloudBridge

app = Flask(__name__)
# Use absolute path for SQLite to avoid issues with Gunicorn workers
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aetherreader.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Production Session Security
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_PERMANENT=True,
    PERMANENT_SESSION_LIFETIME=2592000, # 30 days
)

db.init_app(app)
oauth = setup_oauth(app)

with app.app_context():
    print(f"DEBUG: App started. Database path: {db_path}")
    db.create_all()
    user_count = User.query.count()
    cred_count = Credential.query.count()
    print(f"DEBUG: Current DB state: {user_count} users, {cred_count} credentials")

@app.route('/api/db-status')
def db_status():
    users = User.query.all()
    creds = Credential.query.all()
    return jsonify({
        "db_path": db_path,
        "users": [{"id": u.id, "username": u.username, "creds": len(u.credentials), "provider": u.cloud_provider} for u in users],
        "total_creds": len(creds)
    })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/auth-options', methods=['POST'])
def auth_options():
    username = request.json.get('username', '').lower().strip()
    if not username:
        return jsonify({"status": "error", "message": "Username required"}), 400
        
    print(f"DEBUG: Auth options requested for username: {username}")
    user = User.query.filter_by(username=username).first()
    
    if not user:
        print(f"DEBUG: User '{username}' not found. Creating new user.")
        user = User(username=username)
        db.session.add(user)
        db.session.commit()
    
    # Check if they have credentials (using the relationship)
    if not user.credentials:
        print(f"DEBUG: User '{username}' has no credentials. Registration required.")
        options, state = get_registration_options(user.id, user.username)
        session['registration_state'] = state
        session['registering_user_id'] = user.id
        from passkey_utils import registration_options_to_dict
        return jsonify({"type": "registration", "options": registration_options_to_dict(options)})

    print(f"DEBUG: User '{username}' found. ID: {user.id}. Credentials: {len(user.credentials)}")
    # Return login options
    from fido2.webauthn import PublicKeyCredentialDescriptor
    allowed_credentials = [
        PublicKeyCredentialDescriptor(type="public-key", id=c.credential_id)
        for c in user.credentials
    ]
    
    from passkey_utils import get_authentication_options, authentication_options_to_dict
    options, state = get_authentication_options(allowed_credentials)
    session['login_state'] = state
    session['logging_in_user_id'] = user.id
    return jsonify({"type": "login", "options": authentication_options_to_dict(options)})

@app.route('/verify-registration', methods=['POST'])
def verify_registration():
    registration_state = session.get('registration_state')
    user_id = session.get('registering_user_id')
    if not registration_state or not user_id:
        return jsonify({"status": "error", "message": "No registration state found"}), 400
    
    # The browser sends back the attestation
    data = request.json
    try:
        from passkey_utils import verify_registration_response
        auth_data = verify_registration_response(registration_state, data)
        
        cred_data = auth_data.credential_data
        user = User.query.get(user_id)
        
        from fido2 import cbor
        pub_key_bytes = cbor.encode(cred_data.public_key)

        new_cred = Credential(
            user_id=user.id,
            credential_id=cred_data.credential_id,
            public_key=pub_key_bytes,
            sign_count=auth_data.counter
        )
        db.session.add(new_cred)
        db.session.commit()
        
        session.permanent = True
        session['user_id'] = user.id
        return jsonify({"status": "success"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/verify-login', methods=['POST'])
def verify_login():
    login_state = session.get('login_state')
    user_id = session.get('logging_in_user_id')
    if not login_state or not user_id:
        return jsonify({"status": "error", "message": "No login state found"}), 400
    
    data = request.json
    user = User.query.get(user_id)
    
    from fido2.webauthn import AttestedCredentialData
    from fido2 import cbor
    
    # Reconstruct fido2 credential objects
    credentials = []
    for c in user.credentials:
        try:
            # Reconstruct from the CBOR-encoded public key we saved
            pub_key = cbor.decode(c.public_key)
            cred = AttestedCredentialData.create(
                aaguid=b'\x00'*16, # We didn't save AAGUID, standard for many passkeys
                credential_id=c.credential_id,
                public_key=pub_key
            )
            credentials.append(cred)
        except Exception as e:
            print(f"Error reconstructing credential {c.id}: {e}")

    try:
        from passkey_utils import verify_authentication_response
        verify_authentication_response(login_state, credentials, data)
        session.permanent = True
        session['user_id'] = user_id
        return jsonify({"status": "success"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/user-status')
def user_status():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"isLoggedIn": False})
    
    user = User.query.get(user_id)
    return jsonify({
        "isLoggedIn": True,
        "username": user.username,
        "isConnected": bool(user.cloud_provider),
        "provider": user.cloud_provider
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
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
    
    user_id = session.get('user_id')
    print(f"DEBUG: Authorize called for {name}. user_id from session: {user_id}")
    if not user_id:
        print("DEBUG: Session user_id is missing in authorize!")
        return "Login session lost. Please close this window and log in again before connecting.", 401

    user = User.query.get(user_id)
    if not user:
        return "User not found", 404
        
    # Save token
    from sqlalchemy.orm.attributes import flag_modified
    user_tokens = dict(user.tokens or {})
    user_tokens[name] = token
    user.tokens = user_tokens
    flag_modified(user, 'tokens') # Ensure SQLAlchemy sees the change
    
    user.cloud_provider = name
    db.session.commit()
    print(f"DEBUG: Cloud {name} connected and SAVED for user {user.username}")

    # Automatically close the OAuth popup if one was used
    return 'Cloud storage connected! <script>if(window.opener){window.opener.location.reload(); window.close();}</script>'

@app.route('/api/set-library', methods=['POST'])
def set_library():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    data = request.json
    folder_id = data.get('folder_id')
    
    user = User.query.get(user_id)
    user.cloud_folder_id = folder_id
    db.session.commit()
    
    return jsonify({"status": "success"})

@app.route('/list-folders')
def list_folders():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    user = User.query.get(user_id)
    provider = user.cloud_provider
    if not provider or not user.tokens or provider not in user.tokens:
        return jsonify([])

    token_obj = user.tokens[provider]
    access_token = token_obj.get('access_token')
    instance_url = os.getenv('NEXTCLOUD_INSTANCE_URL') if provider == 'nextcloud' else None
    
    bridge = CloudBridge(access_token, provider, instance_url)
    path = request.args.get('path', '/')
    # For initial selection, we often want to list folders specifically
    items = bridge.list_folders(path)
    return jsonify(items)

@app.route('/api/browse')
def browse_cloud():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    user = User.query.get(user_id)
    provider = user.cloud_provider
    if not provider or not user.tokens or provider not in user.tokens:
        return jsonify({"status": "error", "message": "No cloud storage connected"}), 400
    
    token_obj = user.tokens[provider]
    access_token = token_obj.get('access_token')
    instance_url = os.getenv('NEXTCLOUD_INSTANCE_URL') if provider == 'nextcloud' else None
    
    bridge = CloudBridge(access_token, provider, instance_url)
    path = request.args.get('path', '/')
    files = bridge.list_folders(path)
    
    return jsonify(files)

@app.route('/api/proxy-book')
def proxy_book():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    user = User.query.get(user_id)
    provider = user.cloud_provider
    token_obj = user.tokens.get(provider) if user.tokens else None
    
    if not token_obj:
        return jsonify({"status": "error", "message": "No cloud token found"}), 400
    
    access_token = token_obj.get('access_token')
    file_path = request.args.get('path')
    
    bridge = CloudBridge(access_token, provider, os.getenv('NEXTCLOUD_INSTANCE_URL'))
    external_response = bridge.get_book_content(file_path)
    
    return Response(
        stream_with_context(external_response.iter_content(chunk_size=4096)),
        content_type=external_response.headers.get('Content-Type')
    )

if __name__ == '__main__':
    # On your Mac, use 'ssl_context' because WebAuthn requires HTTPS
    app.run(debug=True, port=5000, ssl_context='adhoc')
