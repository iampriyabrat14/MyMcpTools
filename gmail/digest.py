import os
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from gmail.gmail_tools import list_emails, send_email
from gmail.summarizer import summarize_email

load_dotenv()

DIGEST_TO = os.getenv("DIGEST_EMAIL", os.getenv("GMAIL_USER", ""))
DIGEST_HOUR = int(os.getenv("DIGEST_HOUR", "8"))
DIGEST_MINUTE = int(os.getenv("DIGEST_MINUTE", "0"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_digest_body(emails: list[dict]) -> str:
    if not emails:
        return "No unread emails today."

    lines = [
        f"Daily Email Digest — {datetime.now().strftime('%A, %d %B %Y')}",
        f"You have {len(emails)} unread email(s).\n",
        "-" * 50,
    ]

    for i, email in enumerate(emails, 1):
        summary = summarize_email(
            subject=email.get("subject", ""),
            sender=email.get("from", ""),
            snippet=email.get("snippet", ""),
        )
        lines.append(f"\n{i}. {email.get('subject', '(no subject)')}")
        lines.append(f"   From: {email.get('from', '')}")
        lines.append(f"   Date: {email.get('date', '')}")
        lines.append(f"   Summary: {summary}")
        lines.append(f"   ID: {email.get('id', '')}")

    lines.append("\n" + "-" * 50)
    lines.append("Reply to any email using its ID via your Gmail MCP chat.")
    return "\n".join(lines)


def send_digest():
    logger.info("Running daily email digest job...")
    try:
        emails = list_emails(max_results=20, query="is:unread")
        body = build_digest_body(emails)
        result = send_email(
            to=DIGEST_TO,
            subject=f"Daily Email Digest — {datetime.now().strftime('%d %b %Y')}",
            body=body,
        )
        logger.info(f"Digest sent: {result}")
    except Exception as e:
        logger.error(f"Digest failed: {e}")


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        send_digest,
        trigger=CronTrigger(hour=DIGEST_HOUR, minute=DIGEST_MINUTE),
        id="daily_digest",
        name="Daily Email Digest",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Digest scheduler started — runs daily at {DIGEST_HOUR:02d}:{DIGEST_MINUTE:02d}")
    return scheduler


if __name__ == "__main__":
    scheduler = start_scheduler()
    print(f"Scheduler running. Digest will be sent at {DIGEST_HOUR:02d}:{DIGEST_MINUTE:02d} every day.")
    print("Press Ctrl+C to stop.")
    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.shutdown()
        print("Scheduler stopped.")
