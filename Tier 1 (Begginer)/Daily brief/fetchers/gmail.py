"""
Fetches unread emails from the last 24 hours via Gmail API.
Reuses the OAuth pattern from Email Triangle assistant.
"""

from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.readonly",
]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"


def get_google_service(api: str, version: str):
    """Returns an authorized Google API service client, refreshing token as needed."""
    creds = None
    token_path = Path(TOKEN_FILE)
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())
    return build(api, version, credentials=creds)


def fetch_gmail(max_results: int = 15) -> list[dict]:
    service = get_google_service("gmail", "v1")

    result = service.users().messages().list(
        userId="me",
        q="is:unread newer_than:1d",
        maxResults=max_results,
    ).execute()

    messages = result.get("messages", [])
    if not messages:
        return []

    emails = []
    for m in messages:
        msg = service.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
        emails.append({
            "from": headers.get("From", "(unknown)"),
            "subject": headers.get("Subject", "(no subject)"),
            "snippet": msg.get("snippet", ""),
        })

    return emails
