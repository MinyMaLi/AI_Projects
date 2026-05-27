"""
Daily AI Briefing Agent
Pulls weather, news, Gmail, and Calendar data, generates an HTML brief with Claude,
emails it to the configured address, and saves a local copy.

Usage: python brief.py
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
LOCATION = os.environ.get("LOCATION", "Prague")
USER_EMAIL = os.environ.get("USER_EMAIL", "lasha@nextstudio.io")
OUTPUTS_DIR = Path("outputs")


def main():
    if not ANTHROPIC_API_KEY:
        sys.exit("ERROR: ANTHROPIC_API_KEY is not set in .env")
    if not TAVILY_API_KEY:
        sys.exit("ERROR: TAVILY_API_KEY is not set in .env")

    today = datetime.now().strftime("%A, %B %d, %Y")
    date_slug = datetime.now().strftime("%Y-%m-%d")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting daily brief for {today}")

    # ── Fetch all data ─────────────────────────────────────────────────────────
    from fetchers.weather import fetch_weather
    from fetchers.news import fetch_news
    from fetchers.gmail import fetch_gmail
    from fetchers.calendar import fetch_calendar

    weather = None
    print("  Fetching weather...", end=" ", flush=True)
    try:
        weather = fetch_weather(LOCATION)
        print(f"{weather['condition']}, {weather['temp_high']}°C / {weather['temp_low']}°C")
    except Exception as e:
        print(f"FAILED ({e})")

    news = []
    print("  Fetching news...", end=" ", flush=True)
    try:
        news = fetch_news(TAVILY_API_KEY)
        print(f"{len(news)} articles")
    except Exception as e:
        print(f"FAILED ({e})")

    emails = []
    print("  Fetching Gmail...", end=" ", flush=True)
    try:
        emails = fetch_gmail()
        print(f"{len(emails)} unread emails")
    except Exception as e:
        print(f"FAILED ({e})")

    events = []
    print("  Fetching Calendar...", end=" ", flush=True)
    try:
        events = fetch_calendar()
        print(f"{len(events)} events today")
    except Exception as e:
        print(f"FAILED ({e})")

    # ── Generate brief with Claude ─────────────────────────────────────────────
    from utils.claude_client import generate_brief

    print("  Generating brief with Claude...", end=" ", flush=True)
    context = {
        "date": today,
        "weather": weather,
        "news": news,
        "emails": emails,
        "events": events,
    }
    html = generate_brief(context, ANTHROPIC_API_KEY)
    print("done")

    # ── Save local copy ────────────────────────────────────────────────────────
    OUTPUTS_DIR.mkdir(exist_ok=True)
    output_path = OUTPUTS_DIR / f"{date_slug}.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"  Saved local copy → {output_path}")

    # ── Send email ─────────────────────────────────────────────────────────────
    from utils.gmail_send import send_brief

    subject = f"Daily Brief — {today}"
    print(f"  Sending email to {USER_EMAIL}...", end=" ", flush=True)
    try:
        msg_id = send_brief(html, USER_EMAIL, subject)
        print(f"sent (id: {msg_id})")
    except Exception as e:
        print(f"FAILED ({e})")
        print("  (Brief saved locally — check outputs/ folder)")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Brief complete.")


if __name__ == "__main__":
    main()
