# Personal Assistant (Life Organizer)

A personal organizer and planner for managing projects alongside emails, texts, calls, and voicemails — all in one place.

## What it does

- **Projects** — Sync from Harvest (your source of truth) or add local-only projects
- **Emails** — Sync work Outlook and personal Gmail inboxes, or log manually
- **Texts** — Track text message conversations
- **Calls** — Quick call notepad for architects/contractors, filed to the right Harvest project
- **Voicemails** — Record voicemails with transcripts and listened/unlistened status
- **Start My Day** — AI brief for today, this week, and this month with a daily checklist, evening wrap-up, and weekly review
- **Needs attention** — prioritized queue on your morning dashboard
- **Project timelines** — chronological view of all comms per project, plus contact roll-up
- **Smart linking** — Alex suggests which project emails, texts, and voicemails belong to
- **Alex actions** — assistant can link items, mark read, and trigger syncs from chat
- **Follow-up reminders** — set when saving call notes; surfaces on Start My Day when due
- **AI Secretary** — Smart assistant that summarizes, prioritizes, and drafts replies using your live data

## Architecture

```
├── backend/          # Python FastAPI REST API
│   └── app/
│       ├── models.py     # SQLAlchemy data models
│       ├── schemas.py    # Pydantic request/response schemas
│       └── routers/      # API endpoints per resource
└── frontend/         # React + Vite + TypeScript UI
    └── src/
        ├── pages/        # Dashboard, Projects, Emails, etc.
        └── api/          # API client
```

**Stack:** FastAPI · SQLAlchemy · SQLite · React · Vite · TypeScript

## Getting started

### Prerequisites

- Python 3.11+
- Node.js 18+

### Quick start

```bash
./start.sh
```

Or manually:

### 1. Configure Harvest (recommended)

Projects are synced from [Harvest](https://www.getharvest.com/), where you already track them.

1. Go to [Harvest Developers](https://id.getharvest.com/developers) and create a **Personal Access Token**
2. Copy your **Access Token** and **Account ID**
3. Create `backend/.env` from the example:

```bash
cd backend
cp .env.example .env
# Edit .env with your credentials
```

```env
HARVEST_ACCESS_TOKEN=your_token_here
HARVEST_ACCOUNT_ID=your_account_id_here
HARVEST_USER_AGENT=Personal Assistant (you@example.com)
```

### 2. Start the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, go to **Integrations**, and sync from Harvest, Outlook, Gmail, and Grasshopper.

## Email setup (Outlook + Gmail)

| Account | Provider | IMAP host | Env prefix |
|---------|----------|-----------|------------|
| Company (work) | Outlook / Microsoft 365 | `outlook.office365.com` | `WORK_EMAIL_IMAP_*` |
| Personal | Gmail | `imap.gmail.com` | `PERSONAL_EMAIL_IMAP_*` |

Both require an **app password** if you use MFA:

- **Outlook:** Microsoft account → Security → App passwords (or create via Microsoft 365 admin)
- **Gmail:** Google Account → Security → 2-Step Verification → App passwords. Also enable IMAP under Gmail settings.

```env
# Work — company Outlook
WORK_EMAIL_IMAP_HOST=outlook.office365.com
WORK_EMAIL_IMAP_USER=you@yourcompany.com
WORK_EMAIL_IMAP_PASSWORD=your_app_password

# Personal — Gmail
PERSONAL_EMAIL_IMAP_HOST=imap.gmail.com
PERSONAL_EMAIL_IMAP_USER=you@gmail.com
PERSONAL_EMAIL_IMAP_PASSWORD=your_app_password
```

Go to **Integrations** → **Sync All Email**. Work emails show an **Outlook** badge; personal show **Gmail**.

Grasshopper voicemails use your **work Outlook inbox** automatically — point Grasshopper notifications at your company address.

## Harvest sync

- Projects are pulled from the Harvest API and stored locally for linking communications
- Active/archived status follows Harvest (`is_active`)
- Client name, project code, and notes are imported into the project description
- Re-sync updates existing projects and archives any that were removed from Harvest
- Harvest-synced projects cannot be deleted locally — manage them in Harvest

## Grasshopper sync

Grasshopper does not offer a public API, so Personal Assistant connects through the channels Grasshopper does support:

1. **Voicemail email (IMAP)** — Grasshopper sends voicemail MP3s and transcriptions to your email. Point those notifications at an IMAP inbox, add the credentials to `.env`, and sync from the **Integrations** page.
2. **Webhook (optional)** — For texts or other events, use Zapier or a custom script to `POST` JSON to `/api/grasshopper/webhook` with your `GRASSHOPPER_WEBHOOK_SECRET`.

### Grasshopper setup

1. In Grasshopper: **Settings → Notifications** — add the email address you use for IMAP (e.g. a Gmail inbox with an app password).
2. Enable **voicemail-to-email** and **voicemail transcription**.
3. Add to `backend/.env`:

```env
GRASSHOPPER_IMAP_HOST=imap.gmail.com
GRASSHOPPER_IMAP_USER=you@example.com
GRASSHOPPER_IMAP_PASSWORD=your_app_password
GRASSHOPPER_IMAP_FOLDER=INBOX
GRASSHOPPER_WEBHOOK_SECRET=optional_secret_for_custom_automations
```

4. Go to **Integrations** → **Sync from Inbox**

Imported voicemails include transcripts and audio attachments. Duplicate emails are skipped automatically.

## AI Secretary (Alex)

The built-in AI assistant acts like a smart secretary. It reads a live snapshot of your projects and communications to:

- Give morning briefings and daily priorities
- Summarize unread emails, texts, and voicemails
- Draft follow-up emails and text replies
- Suggest which Harvest project to focus on

Add to `backend/.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
ASSISTANT_MODEL=gpt-4o-mini
ASSISTANT_NAME=Alex
```

Works with any OpenAI-compatible API (`OPENAI_BASE_URL`). Open the **Assistant** page to chat.

## Start My Day

Your home screen (`Start My Day`) generates a personalized brief:

- **Today** — what needs attention right now
- **This week** — items to keep on your radar
- **This month** — bigger-picture goals
- **Checklist** — 6–10 actionable tasks you can check off (add your own too)

Click **Start my day** each morning. Refresh anytime if you've synced new emails or projects.

## API endpoints

| Resource    | Endpoints                          |
|-------------|------------------------------------|
| Harvest     | `GET /api/harvest/status`, `POST /api/harvest/sync` |
| Grasshopper | `GET /api/grasshopper/status`, `POST /api/grasshopper/sync`, `POST /api/grasshopper/webhook` |
| Mailboxes   | `GET /api/mailboxes/status`, `POST /api/mailboxes/sync` |
| Assistant   | `GET /api/assistant/status`, `POST /api/assistant/chat`, `POST /api/assistant/briefing` |
| Day start   | `GET /api/day-start`, `POST /api/day-start/generate`, wrap-up & weekly review |
| Projects    | `GET/POST /api/projects`, timeline & contacts |
| Emails      | `GET/POST /api/emails`             |
| Texts       | `GET/POST /api/texts`              |
| Calls       | `GET/POST /api/calls`              |
| Voicemails  | `GET/POST /api/voicemails`         |
| Linking     | `GET /api/linking/suggest`, `POST /api/linking/apply` |
| Attention   | `GET /api/attention`               |
| Dashboard   | `GET /api/dashboard/stats`         |

All resources support `GET /:id`, `PATCH /:id`, and `DELETE /:id` where applicable.
