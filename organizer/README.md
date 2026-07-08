# Life Organizer

A personal organizer and planner for managing projects alongside emails, texts, calls, and voicemails — all in one place.

This is a **standalone application** living in the `organizer/` directory, separate from the GitHub Pages site at the repo root.

## What it does

- **Projects** — Sync from Harvest (your source of truth) or add local-only projects
- **Emails** — Log inbound/outbound emails, mark read/unread, star important ones
- **Texts** — Track text message conversations
- **Calls** — Log phone calls with duration and notes
- **Voicemails** — Record voicemails with transcripts and listened/unlistened status
- **Dashboard** — Unified overview of active projects and unread communications

## Architecture

```
organizer/
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

### 1. Configure Harvest (recommended)

Projects are synced from [Harvest](https://www.getharvest.com/), where you already track them.

1. Go to [Harvest Developers](https://id.getharvest.com/developers) and create a **Personal Access Token**
2. Copy your **Access Token** and **Account ID**
3. Create `organizer/backend/.env` from the example:

```bash
cd organizer/backend
cp .env.example .env
# Edit .env with your credentials
```

```env
HARVEST_ACCESS_TOKEN=your_token_here
HARVEST_ACCOUNT_ID=your_account_id_here
HARVEST_USER_AGENT=Life Organizer (you@example.com)
```

### 2. Start the backend

```bash
cd organizer/backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 3. Start the frontend

```bash
cd organizer/frontend
npm install
npm run dev
```

Open http://localhost:5173

Open http://localhost:5173, go to **Projects**, and click **Sync from Harvest**.

## Harvest sync

- Projects are pulled from the Harvest API and stored locally for linking communications
- Active/archived status follows Harvest (`is_active`)
- Client name, project code, and notes are imported into the project description
- Re-sync updates existing projects and archives any that were removed from Harvest
- Harvest-synced projects cannot be deleted locally — manage them in Harvest

## Roadmap

Future enhancements you may want to add:

- [x] Harvest project sync
- [ ] Link communications to projects from the UI
- [ ] Gmail / IMAP email sync
- [ ] Phone/SMS integration (Twilio, Android SMS backup)
- [ ] Calendar and task planning
- [ ] Search across all communications
- [ ] Desktop app (Electron or Tauri)
- [ ] Authentication and multi-user support

## API endpoints

| Resource    | Endpoints                          |
|-------------|------------------------------------|
| Harvest     | `GET /api/harvest/status`, `POST /api/harvest/sync` |
| Projects    | `GET/POST /api/projects`           |
| Emails      | `GET/POST /api/emails`             |
| Texts       | `GET/POST /api/texts`              |
| Calls       | `GET/POST /api/calls`              |
| Voicemails  | `GET/POST /api/voicemails`         |
| Dashboard   | `GET /api/dashboard/stats`         |

All resources support `GET /:id`, `PATCH /:id`, and `DELETE /:id`.
