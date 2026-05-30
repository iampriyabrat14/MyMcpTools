import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o"


def summarize_email(subject: str, sender: str, snippet: str) -> str:
    prompt = (
        f"Summarize this email in one short sentence (max 15 words).\n"
        f"From: {sender}\n"
        f"Subject: {subject}\n"
        f"Preview: {snippet}"
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=60,
    )
    return response.choices[0].message.content.strip()


def summarize_email_list(emails: list[dict]) -> list[dict]:
    for email in emails:
        email["summary"] = summarize_email(
            subject=email.get("subject", ""),
            sender=email.get("from", ""),
            snippet=email.get("snippet", ""),
        )
    return emails


def summarize_full_email(subject: str, sender: str, body: str) -> str:
    prompt = (
        f"Summarize this email clearly in 2-3 sentences. Focus on what action is needed.\n"
        f"From: {sender}\n"
        f"Subject: {subject}\n"
        f"Body:\n{body[:3000]}"
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()
