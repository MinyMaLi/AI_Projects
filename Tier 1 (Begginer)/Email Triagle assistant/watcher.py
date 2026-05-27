"""
Email Triangle Watcher — polls Gmail history every 45 seconds and runs the
pipeline on each new inbox message.
"""

import json
import logging
import logging.handlers
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Resolve paths relative to this script's directory so pythonw.exe can be
# launched from anywhere.
SCRIPT_DIR = Path(__file__).parent.resolve()
os.chdir(SCRIPT_DIR)

import pipeline  # noqa: E402 — import after chdir so pipeline's relative paths work
from googleapiclient.errors import HttpError  # noqa: E402

STATE_FILE = SCRIPT_DIR / "state.json"
PID_FILE = SCRIPT_DIR / "watcher.pid"
LOG_FILE = SCRIPT_DIR / "watcher.log"
POLL_INTERVAL = 45  # seconds
MAX_PROCESSED_IDS = 500

# ── Logging ───────────────────────────────────────────────────────────────────

log = logging.getLogger("watcher")
log.setLevel(logging.INFO)

_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
)
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
log.addHandler(_handler)

# Also echo to stdout so `python watcher.py` shows output in a console.
_stdout = logging.StreamHandler(sys.stdout)
_stdout.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
log.addHandler(_stdout)

# ── State ─────────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    tmp = STATE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(STATE_FILE)


# ── Gmail helpers ─────────────────────────────────────────────────────────────

def bootstrap_history_id(service) -> str:
    profile = service.users().getProfile(userId="me").execute()
    return str(profile["historyId"])


def get_new_message_ids(service, last_history_id: str) -> tuple:
    """Return (list_of_new_inbox_msg_ids, updated_history_id)."""
    new_ids = []
    new_history_id = last_history_id
    page_token = None
    first_page = True

    while True:
        kwargs = {
            "userId": "me",
            "startHistoryId": last_history_id,
            "historyTypes": ["messageAdded"],
        }
        if page_token:
            kwargs["pageToken"] = page_token

        result = service.users().history().list(**kwargs).execute()

        # The historyId on the first page is the new baseline.
        if first_page:
            new_history_id = str(result.get("historyId", last_history_id))
            first_page = False

        for record in result.get("history", []):
            for added in record.get("messagesAdded", []):
                msg = added.get("message", {})
                if "INBOX" in msg.get("labelIds", []):
                    new_ids.append(msg["id"])

        page_token = result.get("nextPageToken")
        if not page_token:
            break

    # Deduplicate while preserving order.
    seen = set()
    unique_ids = []
    for mid in new_ids:
        if mid not in seen:
            seen.add(mid)
            unique_ids.append(mid)

    return unique_ids, new_history_id


# ── Lockfile ──────────────────────────────────────────────────────────────────

def acquire_lock() -> bool:
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            # Check if that PID is still alive (Windows-safe).
            import ctypes
            handle = ctypes.windll.kernel32.OpenProcess(0x0400, False, old_pid)
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                log.error(
                    f"Another watcher is already running (PID {old_pid}). "
                    "Stop it first with stop_watcher.bat."
                )
                return False
        except Exception:
            pass  # stale PID file — safe to overwrite
    PID_FILE.write_text(str(os.getpid()))
    return True


def release_lock() -> None:
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass


# ── Main loop ─────────────────────────────────────────────────────────────────

def run_watcher() -> None:
    if not acquire_lock():
        sys.exit(1)

    try:
        log.info("=== Email Triangle Watcher starting ===")
        service = pipeline.get_gmail_service()

        state = load_state()
        if not state.get("last_history_id"):
            history_id = bootstrap_history_id(service)
            state = {
                "last_history_id": history_id,
                "processed_message_ids": [],
                "watcher_started_at": _now_iso(),
                "last_poll_at": None,
                "total_processed": 0,
            }
            save_state(state)
            log.info(f"Bootstrapped at historyId={history_id}. Watching for new emails from now.")
        else:
            log.info(
                f"Resuming from historyId={state['last_history_id']}, "
                f"total processed so far: {state.get('total_processed', 0)}"
            )

        while True:
            try:
                state = load_state()
                new_ids, new_history_id = get_new_message_ids(
                    service, state["last_history_id"]
                )

                processed_set = set(state.get("processed_message_ids", []))
                to_process = [mid for mid in new_ids if mid not in processed_set]

                for msg_id in to_process:
                    log.info(f"New email detected: {msg_id} — processing...")
                    try:
                        email_data = pipeline.get_email_by_id(service, msg_id)
                        log.info(f"  Subject: {email_data['subject']}")
                        log.info(f"  From:    {email_data['sender']}")
                        reply = pipeline.process_email(service, email_data)
                        if reply.startswith("[SKIP:"):
                            log.info(f"Skipped: {reply}")
                        else:
                            log.info("Gmail draft saved.")
                        processed_set.add(msg_id)
                        state["total_processed"] = state.get("total_processed", 0) + 1
                    except Exception as exc:
                        log.error(f"  Failed to process {msg_id}: {exc}", exc_info=True)

                # Cap the deduplication cache.
                ids_list = list(processed_set)[-MAX_PROCESSED_IDS:]

                state["last_history_id"] = new_history_id
                state["processed_message_ids"] = ids_list
                state["last_poll_at"] = _now_iso()
                save_state(state)

            except HttpError as exc:
                if exc.resp.status == 404:
                    log.warning("historyId expired (too old). Re-bootstrapping from now...")
                    new_id = bootstrap_history_id(service)
                    state = load_state()
                    state["last_history_id"] = new_id
                    state["last_poll_at"] = _now_iso()
                    save_state(state)
                else:
                    log.error(f"Gmail API error: {exc}")
            except Exception as exc:
                log.error(f"Unexpected error in poll loop: {exc}", exc_info=True)

            log.info(f"Polling again in {POLL_INTERVAL}s...")
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        log.info("Watcher stopped by user.")
    finally:
        release_lock()


if __name__ == "__main__":
    run_watcher()
