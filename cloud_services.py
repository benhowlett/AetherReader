import os
from authlib.integrations.flask_client import OAuth
from flask import url_for

def setup_oauth(app):
    oauth = OAuth(app)
    
    # Google Drive Setup
    oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        access_token_url='https://oauth2.googleapis.com/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        api_base_url='https://www.googleapis.com/drive/v3/',
        client_kwargs={'scope': 'https://www.googleapis.com/auth/drive.readonly'},
    )
    
    # Dropbox Setup
    oauth.register(
        name='dropbox',
        client_id=os.getenv('DROPBOX_APP_KEY'),
        client_secret=os.getenv('DROPBOX_APP_SECRET'),
        access_token_url='https://api.dropboxapi.com/oauth2/token',
        authorize_url='https://www.dropbox.com/oauth2/authorize',
        api_base_url='https://api.dropboxapi.com/2/',
    )
    
    return oauth