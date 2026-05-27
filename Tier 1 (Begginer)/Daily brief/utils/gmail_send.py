"""
Sends the HTML brief as an email via Gmail API.
Shares the same OAuth token as the other Google fetchers.
"""

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fetchers.gmail import get_google_service


def send_brief(html: str, to: str, subject: str) -> str:
    service = get_google_service("gmail", "v1")

    msg = MIMEMultipart("alternative")
    msg["To"] = to
    msg["Subject"] = subject

    # Plain-text fallback for email clients that don't render HTML
    plain = "Your daily brief is ready. Please view this email in an HTML-capable client."
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    result = service.users().messages().send(
        userId="me",
        body={"raw": raw},
    ).execute()

    return result["id"]
