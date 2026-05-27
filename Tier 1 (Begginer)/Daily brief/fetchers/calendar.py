"""
Fetches today's Google Calendar events.
Shares the same OAuth token as the Gmail fetcher.
"""

from datetime import datetime, timezone, timedelta
from fetchers.gmail import get_google_service


def fetch_calendar() -> list[dict]:
    service = get_google_service("calendar", "v3")

    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    result = service.events().list(
        calendarId="primary",
        timeMin=start_of_day.isoformat(),
        timeMax=end_of_day.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = []
    for e in result.get("items", []):
        start = e.get("start", {})
        time_str = start.get("dateTime") or start.get("date", "All day")

        # Format dateTime to a readable local time
        if "T" in time_str:
            dt = datetime.fromisoformat(time_str)
            time_str = dt.strftime("%I:%M %p").lstrip("0")

        events.append({
            "time": time_str,
            "title": e.get("summary", "(no title)"),
            "location": e.get("location", ""),
            "description": (e.get("description") or "")[:200],
        })

    return events
