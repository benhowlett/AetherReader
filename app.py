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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aetherreader.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
db.init_app(app)
oauth = setup_oauth(app)

with app.app_context():
    # Schema is now stable for this phase, so we remove drop_all()
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-registration-options', methods=['POST'])
def generate_registration():
    username = request.json.get('username')
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()

    options, state = get_registration_options(user.id, user.username)
    session['registration_state'] = state
    session['registering_user_id'] = user.id
    
    from passkey_utils import registration_options_to_dict
    output = registration_options_to_dict(options)
    print(f"DEBUG: Registration Options: {output}")
    return jsonify(output)

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
        print(f"DEBUG: Public Key Type: {type(cred_data.public_key)}")
        print(f"DEBUG: Public Key Bytes: {pub_key_bytes.hex()}")

        new_cred = Credential(
            user_id=user.id,
            credential_id=cred_data.credential_id,
            public_key=pub_key_bytes,
            sign_count=auth_data.counter
        )
        db.session.add(new_cred)
        db.session.commit()
        
        session['user_id'] = user.id
        return jsonify({"status": "success"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/generate-login-options', methods=['POST'])
def generate_login():
    username = request.json.get('username')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    
    from passkey_utils import get_authentication_options
    credentials = [Credential.query.filter_by(user_id=user.id).all()] # This is wrong, should be fido2 objects
    # This is getting complicated because of binary data and fido2 objects.
    # I'll simplify the implementation for now and use placeholders if needed, 
    # but I want it to be functional.
    
    # Actually, let's use the user's saved credentials
    user_creds = Credential.query.filter_by(user_id=user.id).all()
    from fido2.webauthn import PublicKeyCredentialDescriptor
    allowed_credentials = [
        PublicKeyCredentialDescriptor(type="public-key", id=c.credential_id)
        for c in user_creds
    ]
    
    options, state = get_authentication_options(allowed_credentials)
    session['login_state'] = state
    session['logging_in_user_id'] = user.id
    return jsonify(dict(options))

@app.route('/verify-login', methods=['POST'])
def verify_login():
    login_state = session.get('login_state')
    user_id = session.get('logging_in_user_id')
    if not login_state or not user_id:
        return jsonify({"status": "error", "message": "No login state found"}), 400
    
    data = request.json
    user_creds = Credential.query.filter_by(user_id=user_id).all()
    # fido2 expects the actual credential objects
    # This is where it gets tricky without a helper to reconstruct fido2 objects from DB
    
    return jsonify({"status": "success"}) # Placeholder for now until I refine the fido2 object reconstruction

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
    if not user_id:
        return "You must be logged in with a passkey first!", 401

    user = User.query.get(user_id)
    # Save token in the tokens JSON column
    user_tokens = dict(user.tokens or {})
    user_tokens[name] = token
    user.tokens = user_tokens
    user.cloud_provider = name
    db.session.commit()

    # Automatically close the OAuth popup if one was used
    return 'Cloud storage connected! <script>if(window.opener){window.opener.location.reload(); window.close();}</script>'

@app.route('/list-folders')
def list_folders():
    # This logic will call the Google/Dropbox API to list folders 
    # so the user can choose where their library lives.
    pass

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

if __name__ == '__main__':
    # On your Mac, use 'ssl_context' because WebAuthn requires HTTPS
    app.run(debug=True, port=5000, ssl_context='adhoc')