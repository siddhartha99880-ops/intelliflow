# Deploy IntelliFlow backend on Railway

Agents cannot log into your Railway account. Follow these steps once (about 10 minutes).

## Architecture on Railway

| Service | Purpose |
|---------|---------|
| **Postgres** (plugin) | Database — injects `DATABASE_URL` |
| **Redis** (plugin) | Celery broker — injects `REDIS_URL` |
| **intelliflow-api** | FastAPI (`uvicorn`) |
| **intelliflow-worker** | Celery worker (same Docker image, different start command) |

Frontend stays on **Netlify** (or elsewhere). Point `NEXT_PUBLIC_API_URL` at the Railway API public URL.

---

## 1. Create a Railway project

1. Go to [railway.app](https://railway.app) → **New Project**.
2. **Deploy from GitHub repo** (recommended) or upload this folder.

If the repo root is `Downloads/` with `backend/` inside, you will set **Root Directory** to `backend` for each app service.

---

## 2. Add Postgres

1. In the project → **+ New** → **Database** → **PostgreSQL**.
2. After it provisions, open the Postgres service → **Variables** → copy `DATABASE_URL` (Railway auto-links it to services that reference `${{Postgres.DATABASE_URL}}` when you use **Add Reference**).

---

## 3. Add Redis

1. **+ New** → **Database** → **Redis**.
2. Link `REDIS_URL` to your API and worker services the same way.

---

## 4. Deploy the API service

1. **+ New** → **GitHub Repo** (or **Empty Service** + connect repo).
2. **Settings**:
   - **Root Directory:** `backend`
   - **Builder:** Dockerfile (`backend/Dockerfile`)
3. **Variables** (service → Variables):

   | Variable | Value |
   |----------|--------|
   | `DATABASE_URL` | Reference → Postgres → `DATABASE_URL` |
   | `REDIS_URL` | Reference → Redis → `REDIS_URL` |
   | `SECRET_KEY` | Long random string (required in prod) |
   | `ENVIRONMENT` | `production` |
   | `DEBUG` | `false` |
   | `SEED_DEMO_DATA` | `1` (first deploy only; then `0`) |
   | `BACKEND_CORS_ORIGINS` | `["https://YOUR-SITE.netlify.app","http://localhost:3000"]` |
   | `OPENAI_API_KEY` | Optional |

4. **Networking** → **Generate Domain** → note the URL, e.g. `https://intelliflow-api-production.up.railway.app`.

5. Deploy. Health check: `GET https://YOUR-RAILWAY-URL/healthz` → `{"status":"ok"}`.

6. API docs: `https://YOUR-RAILWAY-URL/docs`

---

## 5. Deploy the Celery worker (required for workflow runs)

1. **+ New** → duplicate service from same repo (or **Empty Service** + same repo).
2. **Root Directory:** `backend` (same Dockerfile).
3. **Settings** → **Deploy** → **Custom Start Command**:

   ```bash
   celery -A app.workers.celery_app:celery worker --loglevel=INFO --concurrency=1
   ```

4. **Variables:** same `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `OPENAI_API_KEY` as the API (use variable references).
5. No public domain needed for the worker.

Without this service, workflows stay `queued` and never execute.

---

## 6. Connect Netlify frontend

In Netlify → **Environment variables**:

```bash
NEXT_PUBLIC_API_URL=https://YOUR-RAILWAY-API-DOMAIN
```

Redeploy Netlify after changing env vars.

---

## 7. Demo login (if `SEED_DEMO_DATA=1`)

- Email: `demo@intelliflow.local`
- Password: `demo-password`

Test: `POST https://YOUR-RAILWAY-URL/api/auth/login`

---

## CLI (optional)

```bash
npm i -g @railway/cli
railway login
cd backend
railway link
railway up
```

Set variables with `railway variables set KEY=value`.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Build fails | Ensure **Root Directory** is `backend` and Dockerfile path is correct. |
| DB connection error | Confirm `DATABASE_URL` is referenced from Postgres; SSL is added automatically for Railway hosts. |
| CORS errors from Netlify | Update `BACKEND_CORS_ORIGINS` with exact Netlify URL (https, no trailing slash). |
| Workflows stuck `queued` | Deploy the **Celery worker** service and share `REDIS_URL` with it. |
| 502 on cold start | Wait for healthcheck; increase timeout in `railway.toml` if needed. |
