# LinkedIn AutoPoster

AI-powered LinkedIn post scheduling and publishing tool. Create posts manually or generate them with AI, schedule them in a drag-and-drop queue, and let the cron job publish them automatically.

## Features

- **AI Post Generation** — Generate LinkedIn posts using OpenAI (GPT-4o) or Anthropic (Claude) with configurable tone and post type
- **Post Queue** — Drag-and-drop reorderable queue with draft and scheduled posts
- **Scheduled Publishing** — Configure posting schedules per day with time slots and daily caps
- **Image Support** — Upload images to publish alongside your posts
- **LinkedIn OAuth 2.0** — Secure connection with encrypted token storage and automatic refresh
- **Auto-Publishing** — Cron job checks every 5 minutes and publishes due posts
- **Publishing History** — View all published and failed posts with error details

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│   MongoDB    │
│  React/Nginx │     │   FastAPI    │     │   mongo:7.0  │
│  port 3010   │     │  port 8010   │     │  port 27018  │
└──────────────┘     └──────────────┘     └──────────────┘
                     ┌──────────────┐            │
                     │   Cron Job   │────────────┘
                     │  */5 * * * * │
                     └──────┬───────┘
                            │
                     ┌──────▼───────┐
                     │ LinkedIn API │
                     └──────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- LinkedIn Developer App ([create one here](https://www.linkedin.com/developers/apps))
- OpenAI or Anthropic API key (for AI generation)

### 1. Clone and configure

```bash
git clone https://github.com/anthropics/linked-poster.git
cd linked-poster
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Required
ADMIN_PASSWORD=your-secure-password
SESSION_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
LINKEDIN_CLIENT_ID=your-client-id
LINKEDIN_CLIENT_SECRET=your-client-secret
FERNET_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# AI provider (pick one)
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
# or
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

### 2. Set LinkedIn OAuth redirect URI

In your [LinkedIn Developer App](https://www.linkedin.com/developers/apps) settings, add this redirect URI:

```
http://localhost:8010/api/auth/linkedin/callback
```

### 3. Start

```bash
docker compose up -d --build
```

Open **http://localhost:3010** and log in with your `ADMIN_PASSWORD`.

### 4. Connect LinkedIn

Go to **Connect LinkedIn** in the navbar and authorize the app. Once connected, you can create and schedule posts.

## Usage

### Manual Posts

1. Click **Create Post** — write content, optionally upload an image
2. Set status to **Draft** (save for later) or **Scheduled** (pick a date/time)
3. Manage posts in the **Queue** — drag to reorder, publish immediately, or delete

### AI-Generated Posts

1. Go to **AI Generate** — enter a topic, pick a tone and post type
2. Get 3 variants — refine any with the **Improve** button
3. Click **Add to Queue** to save as a draft

### Scheduling

1. Go to **Schedule** — set your timezone and daily post cap
2. Enable specific days and add time slots (e.g., Mon 9:00, Wed 14:30)
3. Draft posts auto-fill available slots in queue order

### Auto-Publishing

The cron job runs every 5 minutes. It picks up scheduled posts that are due, publishes them to LinkedIn, and marks them as published or failed.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ADMIN_PASSWORD` | Yes | Password for admin login |
| `SESSION_SECRET` | Yes | Secret for signing session cookies |
| `LINKEDIN_CLIENT_ID` | Yes | LinkedIn OAuth app client ID |
| `LINKEDIN_CLIENT_SECRET` | Yes | LinkedIn OAuth app client secret |
| `FERNET_KEY` | Yes | Encryption key for storing LinkedIn tokens |
| `AI_PROVIDER` | No | `openai` or `anthropic` (default: `openai`) |
| `OPENAI_API_KEY` | If using OpenAI | OpenAI API key |
| `ANTHROPIC_API_KEY` | If using Anthropic | Anthropic API key |
| `ENV` | No | `local` or `prod` (default: `local`) |
| `MONGO_CONNECTION_STRING` | No | MongoDB URI (auto-configured by Docker Compose) |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Admin login |
| `GET` | `/api/auth/linkedin/initiate` | Start LinkedIn OAuth flow |
| `GET` | `/api/auth/linkedin/status` | Check LinkedIn connection |
| `GET` | `/api/posts/queue` | List queued posts |
| `POST` | `/api/posts` | Create post |
| `PUT` | `/api/posts/:id` | Update post |
| `POST` | `/api/posts/:id/publish-now` | Publish immediately |
| `PUT` | `/api/posts/reorder` | Reorder queue |
| `POST` | `/api/generate` | Generate AI posts |
| `POST` | `/api/generate/improve` | Improve existing post |
| `GET/PUT` | `/api/settings/schedule` | Posting schedule |
| `GET/PUT` | `/api/settings/ai` | AI provider settings |
| `GET` | `/api/history` | Published posts history |

## Tech Stack

- **Frontend** — React 18, Bootstrap 5, React Router, @hello-pangea/dnd
- **Backend** — Python, FastAPI, Motor (async MongoDB driver)
- **Database** — MongoDB 7.0
- **AI** — OpenAI GPT-4o / Anthropic Claude
- **Deployment** — Docker Compose, Nginx

## License

MIT
