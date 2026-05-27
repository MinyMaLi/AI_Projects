"""
Thin wrapper around the Anthropic API.
Takes all fetched data, sends it to Claude, and returns a styled HTML brief.
"""

import anthropic

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a personal morning briefing assistant for Lasha. Your job is to synthesize the provided data into a clean, scannable HTML email brief.

Produce a complete HTML document styled for email clients. Use inline CSS only. Keep the design minimalisstic and professional — white background, dark text, one accent color (#2563EB blue for headings and links).

Structure the brief exactly as follows:
1. Header: "Good morning, Soldier ☀️" + today's date in a large, friendly font
2. Weather section: condition icon (use a relevant emoji), high/low temps in °C, rain chance
3. Top News section: Analyze the tavily output aad provide a concise summary of the top 2 news items from each query. For each item, show the title (as a link), a one-line snippet, and the source domain in parentheses.
4. Your Inbox section: for each email, show sender name (bold), subject, and a one-line summary of the snippet. If there are no unread emails, say so warmly.
5. Today's Calendar section: time-sorted list of events. If no events, say so. Show time + event name + location if available.
6. Footer: a brief one-line motivational thought.

Keep the total reading time under 2 minutes. Be warm but efficient — no filler phrases.

Return ONLY the complete HTML document. No markdown, no explanation, no preamble."""


def generate_brief(context: dict, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)

    user_message = _format_context(context)

    response = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text

def _format_context(ctx: dict) -> str:
    parts = [f"Today's date: {ctx['date']}\n"]

    w = ctx.get("weather", {})
    if w:
        parts.append(
            f"WEATHER — {w['location']}\n"
            f"Condition: {w['condition']}\n"
            f"High: {w['temp_high']}°C, Low: {w['temp_low']}°C\n"
            f"Rain chance: {w['rain_chance']}%\n"
        )

    news = ctx.get("news", [])
    if news:
        parts.append("TOP NEWS")
        for i, item in enumerate(news, 1):
            parts.append(f"{i}. {item['title']}\n   URL: {item['url']}\n   {item['snippet']}")
        parts.append("")

    emails = ctx.get("emails", [])
    if emails:
        parts.append(f"UNREAD EMAILS ({len(emails)} messages)")
        for e in emails:
            parts.append(f"- From: {e['from']}\n  Subject: {e['subject']}\n  Preview: {e['snippet']}")
        parts.append("")
    else:
        parts.append("UNREAD EMAILS: None\n")

    events = ctx.get("events", [])
    if events:
        parts.append("TODAY'S CALENDAR")
        for ev in events:
            loc = f" @ {ev['location']}" if ev["location"] else ""
            parts.append(f"- {ev['time']}: {ev['title']}{loc}")
        parts.append("")
    else:
        parts.append("TODAY'S CALENDAR: No events scheduled\n")

    return "\n".join(parts)
