import base64
import email as email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from gmail.gmail_auth import get_gmail_service


def list_emails(max_results: int = 10, query: str = "") -> list[dict]:
    service = get_gmail_service()
    params = {"userId": "me", "maxResults": max_results}
    if query:
        params["q"] = query

    result = service.users().messages().list(**params).execute()
    messages = result.get("messages", [])

    emails = []
    for msg in messages:
        detail = service.users().messages().get(
            userId="me", id=msg["id"], format="metadata",
            metadataHeaders=["Subject", "From", "To", "Date"]
        ).execute()

        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
        emails.append({
            "id": msg["id"],
            "subject": headers.get("Subject", "(no subject)"),
            "from": headers.get("From", ""),
            "to": headers.get("To", ""),
            "date": headers.get("Date", ""),
            "snippet": detail.get("snippet", ""),
        })

    return emails


def read_email(message_id: str) -> dict:
    service = get_gmail_service()
    msg = service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()

    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    body = _extract_body(msg["payload"])

    return {
        "id": message_id,
        "subject": headers.get("Subject", "(no subject)"),
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "date": headers.get("Date", ""),
        "body": body,
        "labels": msg.get("labelIds", []),
    }


def _extract_body(payload: dict) -> str:
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        for part in payload["parts"]:
            if part["mimeType"] == "text/html":
                data = part["body"].get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    else:
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    return ""


def send_email(to: str, subject: str, body: str, cc: str = "", bcc: str = "") -> dict:
    service = get_gmail_service()

    message = MIMEMultipart()
    message["to"] = to
    message["subject"] = subject
    if cc:
        message["cc"] = cc
    if bcc:
        message["bcc"] = bcc

    message.attach(MIMEText(body, "plain"))
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    sent = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()

    return {"status": "sent", "message_id": sent["id"]}


def reply_to_email(message_id: str, body: str) -> dict:
    service = get_gmail_service()

    original = service.users().messages().get(
        userId="me", id=message_id, format="metadata",
        metadataHeaders=["Subject", "From", "Message-ID"]
    ).execute()

    headers = {h["name"]: h["value"] for h in original["payload"]["headers"]}
    subject = headers.get("Subject", "")
    if not subject.lower().startswith("re:"):
        subject = "Re: " + subject

    reply_to = headers.get("From", "")
    original_message_id = headers.get("Message-ID", "")
    thread_id = original.get("threadId", "")

    message = MIMEText(body, "plain")
    message["to"] = reply_to
    message["subject"] = subject
    if original_message_id:
        message["In-Reply-To"] = original_message_id
        message["References"] = original_message_id

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    sent = service.users().messages().send(
        userId="me", body={"raw": raw, "threadId": thread_id}
    ).execute()

    return {"status": "replied", "message_id": sent["id"], "thread_id": thread_id}


def search_emails(query: str, max_results: int = 20) -> list[dict]:
    return list_emails(max_results=max_results, query=query)


def trash_email(message_id: str) -> dict:
    service = get_gmail_service()
    service.users().messages().trash(userId="me", id=message_id).execute()
    return {"status": "trashed", "message_id": message_id}


def mark_as_read(message_id: str) -> dict:
    service = get_gmail_service()
    service.users().messages().modify(
        userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
    ).execute()
    return {"status": "marked_read", "message_id": message_id}


def mark_as_unread(message_id: str) -> dict:
    service = get_gmail_service()
    service.users().messages().modify(
        userId="me", id=message_id, body={"addLabelIds": ["UNREAD"]}
    ).execute()
    return {"status": "marked_unread", "message_id": message_id}


def list_labels() -> list[dict]:
    service = get_gmail_service()
    result = service.users().labels().list(userId="me").execute()
    labels = result.get("labels", [])
    return [{"id": l["id"], "name": l["name"], "type": l.get("type", "")} for l in labels]


def get_email_count(label: str = "INBOX") -> dict:
    service = get_gmail_service()
    result = service.users().labels().get(userId="me", id=label).execute()
    return {
        "label": label,
        "total": result.get("messagesTotal", 0),
        "unread": result.get("messagesUnread", 0),
    }


def forward_email(message_id: str, to: str, note: str = "") -> dict:
    original = read_email(message_id)
    subject = original["subject"]
    if not subject.lower().startswith("fwd:"):
        subject = "Fwd: " + subject

    forward_body = ""
    if note:
        forward_body = note + "\n\n"
    forward_body += (
        "---------- Forwarded message ----------\n"
        f"From: {original['from']}\n"
        f"Date: {original['date']}\n"
        f"Subject: {original['subject']}\n"
        f"To: {original['to']}\n\n"
        f"{original['body']}"
    )

    return send_email(to=to, subject=subject, body=forward_body)


def draft_email(to: str, subject: str, body: str) -> dict:
    service = get_gmail_service()

    message = MIMEText(body, "plain")
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    draft = service.users().drafts().create(
        userId="me", body={"message": {"raw": raw}}
    ).execute()

    return {"status": "draft_saved", "draft_id": draft["id"]}
