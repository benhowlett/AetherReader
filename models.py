from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # Store the ID of the folder the user selected in their cloud storage
    cloud_folder_id = db.Column(db.String(255), nullable=True)
    # Store provider name (google, dropbox, nextcloud)
    cloud_provider = db.Column(db.String(50), nullable=True)
    # Store OAuth tokens as JSON: { "google": { "access_token": "...", ... } }
    tokens = db.Column(db.JSON, default={})
    # Reading progress: stores { "book_id": "current_location" } as JSON
    progress = db.Column(db.JSON, default={})

class Credential(db.Model):
    """ Stores the public key for Passkeys """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    credential_id = db.Column(db.LargeBinary, unique=True)
    public_key = db.Column(db.LargeBinary)
    sign_count = db.Column(db.Integer, default=0)