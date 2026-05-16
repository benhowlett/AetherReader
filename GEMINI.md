# AetherReader

A web-based ereader that connects to various cloud storage solutions, allowing users to read their books on any device with a web browser.

## Core Goals
- Allow creation of user accounts using **passkeys** (no password storage).
- Minimal personal data storage (name only).
- Connect to cloud storage: **Google Drive, Dropbox, Nextcloud**.
- Support common ebook formats: **EPUB, MOBI, PDF, etc.**
- Sync reading progress across multiple devices.
- Native **dark mode** support with toggle.

## Technical Stack
- **Backend:** Python with Flask.
- **Frontend:** Well-known, easy-to-maintain framework (to be selected/confirmed).
- **Hosting:** Linode VPS (aetherreader.com).
- **Repository:** [https://github.com/benhowlett/AetherReader.git](https://github.com/benhowlett/AetherReader.git)

## Development Conventions
- **Maintainability:** Code must be clear and easy to follow for self-maintenance by the user.
- **Security:** Prioritize passkeys for authentication. Do not store sensitive personal information.
- **Architectural Clarity:** Keep backend and frontend logic decoupled and well-documented.

## Project Structure
- `app.py`: Main Flask application entry point.
- `models.py`: Database models (minimal user info).
- `cloud_services.py`: Integration logic for Google Drive, Dropbox, and Nextcloud.
- `passkey_utils.py`: Utilities for passkey authentication.
- `templates/`: HTML templates for the frontend.
