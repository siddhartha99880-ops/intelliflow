## IntelliFlow – AI-Powered Workflow Automation

IntelliFlow is an AI workflow automation SaaS that lets businesses compose multi-step automations using an LLM agent workflow graph and run them asynchronously with execution logs.

This repository contains:

- `backend/` – FastAPI, PostgreSQL, Redis, Celery, LangChain/OpenAI integration layer, workflow execution engine
- `frontend/` – Next.js 15 SaaS dashboard with a React Flow workflow builder and analytics

## Quick Start (Docker Compose)

From the repository root:

1. Start all services:
   ```bash
   docker compose up --build
   ```
2. IntelliFlow UI:
   - Frontend: http://localhost:3000
   - Backend health: http://localhost:8000/healthz

The compose file enables demo seed data (`SEED_DEMO_DATA=1`). A demo team/workflow/user is created at startup.

## Demo Login

The backend seed script creates:

- Email: `demo@intelliflow.local`
- Password: `demo-password`

Sign in on the `/login` page.

## Key Features Implemented (MVP)

### Workflow Builder (React Flow)

Backend persists a workflow graph as:

- `Workflows`
- `WorkflowNodes` (node type + node JSON data + UI position)
- `WorkflowEdges` (from/to node links + optional `condition_key`)

Frontend supports building nodes + connecting edges, then saving and executing a workflow.

### Multi-step Execution Engine (Async + Logs)

Backend executes workflows step-by-step in a Celery worker:

- per-step logs in `execution_steps`
- workflow execution summary in `executions`
- retries per step (MVP policy)

LLM nodes are implemented via `app/agents/llm.py`:

- If `OPENAI_API_KEY` is set, real JSON output is requested via LangChain + OpenAI.
- If not set, deterministic fallback JSON is used so the demo runs anywhere.

### Integrations (Mock Clients)

The workflow node executors currently call mock integrations:

- Slack (send message / trigger input passthrough)
- Notion (create task page)
- Google (mock invoice extraction + calendar events)
- ERP mock (in-memory finance/customer/order/inventory entries)

These are wired as stubs to keep the MVP runnable.

## API Routes

Base URL: `http://localhost:8000`

### Auth

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `GET /api/auth/me`

### Workflows

- `GET /api/workflows`
- `POST /api/workflows` (save graph)
- `POST /api/workflows/{workflow_id}/execute` (enqueue execution)

### Execution Logs

- `GET /api/executions?limit=20` (recent executions)
- `GET /api/executions/{execution_id}` (includes step logs)

### Integrations

- `GET /api/integrations/health` (mock integration status)

### Teams & API Keys (MVP / Stub)

- `GET /api/teams/me`
- `POST /api/teams/invite` (mock invite)
- `GET /api/api-keys`
- `POST /api/api-keys` (create key)

## Sample Workflow JSON

Frontend builder and backend API use the same graph shape:

`backend/sample_workflows/slack_to_notion_email_demo.json`

## Environment Variables

Backend uses `backend/.env.example`.

Frontend uses `frontend/.env.example` (`NEXT_PUBLIC_API_URL`).

## Architecture (Folder Layout)

Backend (`backend/app/`):

- `api/routers/` – FastAPI route handlers
- `core/` – config, database session/engine, JWT security
- `models/` – SQLAlchemy models (Users/Teams/Workflows/Executions)
- `workflows/` – workflow execution engine (graph runner)
- `agents/` – LangChain/OpenAI runner + agent utilities
- `integrations/` – Slack/Notion/Google/ERP mock clients
- `workers/` – Celery app + tasks

## Deploy backend on Railway

Step-by-step guide: **[docs/RAILWAY.md](docs/RAILWAY.md)**

Summary: create a Railway project → add **Postgres** + **Redis** → deploy **API** (`backend/`, Dockerfile) → deploy **Celery worker** (same image, custom start command) → set `BACKEND_CORS_ORIGINS` for your Netlify URL → use the generated Railway domain as `NEXT_PUBLIC_API_URL`.

## Deploy frontend on Netlify (I can’t log in as you)

Agents here **cannot** sign into your Netlify account or click “Deploy” for you—you need one short setup on your side.

**Important:** Netlify only runs the **Next.js frontend** (`frontend/`). The **FastAPI + Postgres + Redis + Celery** stack must stay on something like Railway, Render, Fly.io, or any VPS/Docker host. Point the frontend at that API:

1. Deploy the backend and note its public URL (e.g. `https://api-yourapp.onrender.com`).
2. In Netlify → **Site** → **Environment variables**, set:
   - `NEXT_PUBLIC_API_URL` = your backend base URL (`https://...` **no trailing slash**).
3. Back end CORS must allow your Netlify domain: set `BACKEND_CORS_ORIGINS` to include `"https://your-site.netlify.app"` (JSON array).

**Netlify project settings**

- **Base directory:** `frontend`
- **Build command:** `npm run build` (default; `frontend/netlify.toml` also sets this)
- **Plugin:** `@netlify/plugin-nextjs` (listed in `frontend/package.json` devDependencies and `frontend/netlify.toml`)

**Ways to deploy**

- **Git:** Push the repo to GitHub → Netlify → “Add new site” → import repo → set base directory `frontend` → deploy.
- **CLI (on your machine):** [Netlify CLI](https://docs.netlify.com/cli/get-started/) → `netlify login` → from `frontend/`, run `netlify init` / `netlify deploy --prod`.

## Notes / Next Steps

This is a working MVP skeleton suitable for demos and portfolios. The next iteration should extend:

- Human-in-the-loop: pause/resume workflow executions on approval
- Decision node branching with richer edge conditions + UI editing
- Real integrations (Slack/Notion/Gmail) and OAuth connections
- Full RBAC + team invite acceptance + persisted API-key auth
- Workflow template marketplace + copilot suggestions inside the dashboard

