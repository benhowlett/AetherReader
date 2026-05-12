import os
from fido2.server import Fido2Server
from fido2.webauthn import PublicKeyCredentialRpEntity

# Configuration for your domain
rp = PublicKeyCredentialRpEntity(id="aetherreader.com", name="AetherReader")
server = Fido2Server(rp)

def get_registration_options(user_id, username):
    """Generates the options needed for the browser to create a new Passkey"""
    registration_data, state = server.register_begin({
        'id': str(user_id).encode(),
        'name': username,
        'displayName': username,
    })
    # 'state' must be stored in the session temporarily to verify the response
    return registration_data, state

def get_authentication_options(credentials):
    """Generates the challenge for an existing user to log in"""
    auth_data, state = server.authenticate_begin(credentials)
    return auth_data, state