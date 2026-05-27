# MyMcpTools — Gmail MCP Server

A fully functional Gmail MCP server built with FastMCP and the Gmail API.
Chat with your inbox using OpenAI GPT-4o via a Streamlit UI, terminal chat, or Claude Desktop.

## Features

- 12 Gmail tools — read, send, reply, search, forward, draft, trash, label
- Streamlit chat UI with tool call logs and quick action buttons
- Automatic email summarization — every listed email gets a one-line AI summary
- Daily email digest — scheduled email every morning with all unread emails summarized
- Terminal chat fallback via `chat.py`
- Claude Desktop integration via MCP config

---

## Project Structure

| File | Purpose |
|------|---------|
| `server.py` | FastMCP server — registers all 12 Gmail tools |
| `gmail_tools.py` | Pure functions for every Gmail operation |
| `gmail_auth.py` | OAuth2 login and token refresh |
| `app.py` | Streamlit chat UI |
| `chat.py` | Terminal chat using OpenAI |
| `summarizer.py` | One-line and full email summarization via GPT-4o |
| `digest.py` | APScheduler daily email digest |
| `requirements.txt` | All dependencies |
| `.env.example` | Environment variable template |

---

## Gmail Tools

| Tool | What it does |
|------|-------------|
| `tool_list_emails` | List inbox emails with optional query filter |
| `tool_read_email` | Read full email body by message ID |
| `tool_send_email` | Send a new email |
| `tool_reply_to_email` | Reply to an email, auto-threaded |
| `tool_search_emails` | Search using Gmail query syntax |
| `tool_trash_email` | Move email to trash |
| `tool_mark_as_read` | Mark email as read |
| `tool_mark_as_unread` | Mark email as unread |
| `tool_list_labels` | List all Gmail labels/folders |
| `tool_get_email_count` | Get total and unread count for a label |
| `tool_forward_email` | Forward an email to another address |
| `tool_draft_email` | Save an email as draft |

---

## Step 1 — Google Cloud Setup

1. Go to https://console.cloud.google.com
2. Create a new project or use an existing one
3. Go to **APIs & Services > Enable APIs** and enable **Gmail API**
4. Go to **APIs & Services > OAuth consent screen**
   - Choose **External**, fill in app name and your email
   - Add scopes: `gmail.readonly`, `gmail.send`, `gmail.modify`, `gmail.compose`
   - Add your Gmail as a test user
5. Go to **APIs & Services > Credentials**
   - Click **Create Credentials > OAuth 2.0 Client ID**
   - Application type: **Desktop app**
   - Download the JSON file, rename it to `credentials.json`
   - Place `credentials.json` inside this project folder

---

## Step 2 — Python Setup

```bash
python -m venv venv

# Windows
venv\Scripts\pip install -r requirements.txt
```

---

## Step 3 — Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```env
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json
GMAIL_USER=your@gmail.com
OPENAI_API_KEY=sk-...
DIGEST_EMAIL=your@gmail.com
DIGEST_HOUR=8
DIGEST_MINUTE=0
```

---

## Step 4 — First-time Google Auth

Run once to generate `token.json`:

```bash
venv\Scripts\python server.py
```

A browser window opens for Google login. After approval, `token.json` is saved and auto-refreshes forever.

---

## Usage

### Option A — Streamlit UI (recommended)

```bash
venv\Scripts\streamlit run app.py
```

Opens a chat UI in your browser with:
- Message history
- Collapsible tool call and result logs
- Quick action buttons — Show Unread, Last 10 Emails, Send Digest Now
- Auto-summarized email lists
- Daily digest scheduler running in the background

### Option B — Terminal Chat

```bash
venv\Scripts\python chat.py
```

### Option C — Claude Desktop

Open `%APPDATA%\Claude\claude_desktop_config.json` and add:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "C:\\path\\to\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\server.py"],
      "env": {
        "GOOGLE_CREDENTIALS_FILE": "C:\\path\\to\\credentials.json",
        "GOOGLE_TOKEN_FILE": "C:\\path\\to\\token.json"
      }
    }
  }
}
```

Restart Claude Desktop. A hammer icon confirms the MCP tools are loaded.

### Option D — Digest Only (no UI)

Run the scheduler standalone:

```bash
venv\Scripts\python digest.py
```

Sends a daily digest email at the time set in `.env`. Default is 8:00 AM.

---

## Example Chat Prompts

- "Show my unread emails"
- "Read the email with id 18f3a..."
- "Search for emails from HR about interview"
- "Send an email to boss@company.com saying I will be late today"
- "Reply to message 18f3a... and say thanks, I will review it"
- "How many unread emails do I have?"
- "Trash email 18f3a..."
- "Forward email 18f3a... to colleague@gmail.com"
- "Draft a follow-up email to recruiter@company.com"
- "Send me my digest now"

---

## Security

- `credentials.json` and `token.json` are in `.gitignore` and will never be pushed
- `venv/` and `.env` are also excluded
- Never share your `credentials.json` or `token.json` files
