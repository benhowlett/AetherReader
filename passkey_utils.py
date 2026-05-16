import os
from fido2.server import Fido2Server
from fido2.webauthn import PublicKeyCredentialRpEntity
from fido2.utils import websafe_encode, websafe_decode

# Configuration for your domain
rp = PublicKeyCredentialRpEntity(id=os.getenv('RP_ID', 'localhost'), name="AetherReader")
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

def registration_options_to_dict(options):
    """Manually serializes registration options to a JSON-friendly dict"""
    pk = options.public_key
    return {
        "challenge": websafe_encode(pk.challenge),
        "rp": {"name": pk.rp.name, "id": pk.rp.id},
        "user": {
            "id": websafe_encode(pk.user.id),
            "name": pk.user.name,
            "displayName": pk.user.display_name
        },
        "pubKeyCredParams": [{"type": p.type, "alg": p.alg} for p in pk.pub_key_cred_params],
        "timeout": pk.timeout,
        "excludeCredentials": [
            {"type": c.type, "id": websafe_encode(c.id)} for c in pk.exclude_credentials
        ] if pk.exclude_credentials else [],
        "authenticatorSelection": {
            "authenticatorAttachment": pk.authenticator_selection.authenticator_attachment,
            "requireResidentKey": pk.authenticator_selection.require_resident_key,
            "userVerification": pk.authenticator_selection.user_verification
        } if pk.authenticator_selection else {},
        "attestation": pk.attestation
    }

def get_authentication_options(credentials):
    """Generates the challenge for an existing user to log in"""
    auth_data, state = server.authenticate_begin(credentials)
    return auth_data, state

def verify_registration_response(state, response):
    """Verifies the attestation from the browser and returns the credential"""
    return server.register_complete(state, response)

def verify_authentication_response(state, credentials, response):
    """Verifies the assertion from the browser and returns the credential"""
    return server.authenticate_complete(state, credentials, response)
