# Gmail MCP Server

A fully functional Gmail MCP server built with FastMCP and the Gmail API.
Connect it to Claude Desktop and chat your way through your inbox.

## Tools available

| Tool | What it does |
|------|-------------|
| tool_list_emails | List inbox emails with optional query filter |
| tool_read_email | Read full email body by message ID |
| tool_send_email | Send a new email |
| tool_reply_to_email | Reply to an email, auto-threaded |
| tool_search_emails | Search using Gmail query syntax |
| tool_trash_email | Move email to trash |
| tool_mark_as_read | Mark email as read |
| tool_mark_as_unread | Mark email as unread |
| tool_list_labels | List all Gmail labels/folders |
| tool_get_email_count | Get total and unread count for a label |
| tool_forward_email | Forward an email to another address |
| tool_draft_email | Save an email as draft |

---

## Step 1 — Google Cloud Setup

1. Go to https://console.cloud.google.com
2. Create a new project (or use an existing one)
3. Go to **APIs & Services > Enable APIs** and enable **Gmail API**
4. Go to **APIs & Services > OAuth consent screen**
   - Choose **External**, fill in app name and your email
   - Add scopes: `gmail.readonly`, `gmail.send`, `gmail.modify`, `gmail.compose`
   - Add your Gmail as a test user
5. Go to **APIs & Services > Credentials**
   - Click **Create Credentials > OAuth 2.0 Client ID**
   - Application type: **Desktop app**
   - Download the JSON file, rename it to `credentials.json`
   - Put `credentials.json` inside this `MCP/` folder

---

## Step 2 — Python Setup

```bash
cd "d:\InterView\All Code Hub\MCP"
pip install -r requirements.txt
```

---

## Step 3 — First-time Auth

Run once to generate `token.json`:

```bash
python server.py
```

A browser window will open for Google login. After you approve, `token.json` is saved.
You only do this once; after that the token auto-refreshes.

---

## Step 4 — Connect to Claude Desktop

Open your Claude Desktop config file:

- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Add this block inside `"mcpServers"`:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "python",
      "args": ["d:\\InterView\\All Code Hub\\MCP\\server.py"],
      "env": {
        "GOOGLE_CREDENTIALS_FILE": "d:\\InterView\\All Code Hub\\MCP\\credentials.json",
        "GOOGLE_TOKEN_FILE": "d:\\InterView\\All Code Hub\\MCP\\token.json"
      }
    }
  }
}
```

Restart Claude Desktop. You will see a hammer icon indicating MCP tools are loaded.

---

## Usage examples in Claude chat

Once connected, just talk naturally:

- "Show me my last 10 emails"
- "Read the email with id 18f3a..."
- "Search for unread emails from HR"
- "Send an email to boss@company.com with subject Meeting and say I'll be there at 10am"
- "Reply to message 18f3a... and say thanks I'll review it"
- "How many unread emails do I have?"
- "Trash email 18f3a..."
- "Forward email 18f3a... to colleague@gmail.com"
- "Draft an email to recruiter@company.com about following up on my application"
