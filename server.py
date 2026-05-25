from fastmcp import FastMCP
from gmail_tools import (
    list_emails,
    read_email,
    send_email,
    reply_to_email,
    search_emails,
    trash_email,
    mark_as_read,
    mark_as_unread,
    list_labels,
    get_email_count,
    forward_email,
    draft_email,
)

mcp = FastMCP("Gmail MCP Server")


@mcp.tool()
def tool_list_emails(max_results: int = 10, query: str = "") -> list[dict]:
    """
    List emails from your Gmail inbox.
    Use query param for Gmail search syntax e.g. 'is:unread', 'from:boss@company.com', 'subject:invoice'.
    """
    return list_emails(max_results=max_results, query=query)


@mcp.tool()
def tool_read_email(message_id: str) -> dict:
    """
    Read the full content of a single email by its message ID.
    Returns subject, from, to, date, body, and labels.
    """
    return read_email(message_id)


@mcp.tool()
def tool_send_email(to: str, subject: str, body: str, cc: str = "", bcc: str = "") -> dict:
    """
    Send a new email.
    to: recipient email address
    subject: email subject line
    body: plain text email body
    cc: optional comma-separated CC addresses
    bcc: optional comma-separated BCC addresses
    """
    return send_email(to=to, subject=subject, body=body, cc=cc, bcc=bcc)


@mcp.tool()
def tool_reply_to_email(message_id: str, body: str) -> dict:
    """
    Reply to an existing email by its message ID.
    Automatically sets subject as 'Re: ...' and threads the reply.
    """
    return reply_to_email(message_id=message_id, body=body)


@mcp.tool()
def tool_search_emails(query: str, max_results: int = 20) -> list[dict]:
    """
    Search emails using Gmail query syntax.
    Examples:
      - 'is:unread' to get unread emails
      - 'from:hr@company.com' to filter by sender
      - 'subject:interview' to search by subject
      - 'after:2024/01/01 before:2024/12/31' for date range
      - 'has:attachment' for emails with attachments
    """
    return search_emails(query=query, max_results=max_results)


@mcp.tool()
def tool_trash_email(message_id: str) -> dict:
    """
    Move an email to trash by its message ID.
    """
    return trash_email(message_id=message_id)


@mcp.tool()
def tool_mark_as_read(message_id: str) -> dict:
    """
    Mark an email as read by its message ID.
    """
    return mark_as_read(message_id=message_id)


@mcp.tool()
def tool_mark_as_unread(message_id: str) -> dict:
    """
    Mark an email as unread by its message ID.
    """
    return mark_as_unread(message_id=message_id)


@mcp.tool()
def tool_list_labels() -> list[dict]:
    """
    List all Gmail labels (folders) in your account.
    Returns label id, name, and type (system or user).
    """
    return list_labels()


@mcp.tool()
def tool_get_email_count(label: str = "INBOX") -> dict:
    """
    Get the total and unread email count for a label.
    Default label is INBOX. Use tool_list_labels to find other label IDs.
    """
    return get_email_count(label=label)


@mcp.tool()
def tool_forward_email(message_id: str, to: str, note: str = "") -> dict:
    """
    Forward an existing email to another address.
    message_id: ID of the email to forward
    to: recipient email address
    note: optional personal note to prepend before the forwarded content
    """
    return forward_email(message_id=message_id, to=to, note=note)


@mcp.tool()
def tool_draft_email(to: str, subject: str, body: str) -> dict:
    """
    Save an email as a draft without sending it.
    to: recipient email address
    subject: email subject
    body: email body text
    """
    return draft_email(to=to, subject=subject, body=body)


if __name__ == "__main__":
    mcp.run()
