"""
One-time Google OAuth setup.
Run this once to authorize Gmail (read + send) and Google Calendar access.
A token.json file will be created in this directory and reused on future runs.

Usage:
    python setup_auth.py
"""

from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.readonly",
]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"


def main():
    token_path = Path(TOKEN_FILE)
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if creds and creds.valid:
        print("Token is already valid — no action needed.")
        return

    if creds and creds.expired and creds.refresh_token:
        print("Refreshing expired token...")
        creds.refresh(Request())
    else:
        if not Path(CREDENTIALS_FILE).exists():
            print(f"ERROR: {CREDENTIALS_FILE!r} not found.")
            print("Download it from Google Cloud Console → APIs & Services → Credentials.")
            return
        print("Opening browser for Google authorization...")
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)

    token_path.write_text(creds.to_json())
    print(f"Authorization successful. Token saved to {TOKEN_FILE}")


if __name__ == "__main__":
    main()
