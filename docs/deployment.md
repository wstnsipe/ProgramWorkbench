# Deployment Notes — Vercel + Railway

## Architecture

```
User browser
    ↓ HTTPS
Vercel (frontend)          React SPA, static files
    ↓ HTTPS API calls
Railway (backend)          FastAPI + uvicorn
    ↓ internal network
Railway Postgres plugin    PostgreSQL 16 + pgvector
```

---

## Backend — Railway

### Initial setup

1. Create a new Railway project
2. Add a **PostgreSQL** service (this automatically sets `DATABASE_URL`)
3. Add your backend as a **GitHub repo** deployment or **Docker** service
4. Railway uses the `Procfile` to start the server:
   ```
   web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

### Environment variables (set in Railway dashboard)

| Variable | Value |
|----------|-------|
| `OPENAI_API_KEY` | `sk-...` |
| `OPENAI_MODEL` | `gpt-4o-mini` |
| `FRONTEND_URL` | `https://your-app.vercel.app` |
| `DATABASE_URL` | *(auto-injected by Railway Postgres plugin)* |
| `PORT` | *(auto-injected by Railway — do not set)* |

### pgvector

The Railway Postgres plugin uses standard PostgreSQL.
You must enable the `vector` extension manually after the database is created:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Connect via Railway's "Connect" tab → copy the connection string → run:
```bash
psql "postgresql://..." -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Then run the app — `Base.metadata.create_all()` creates the tables on startup.

### Persistent file storage

Railway's filesystem is **ephemeral** — uploaded files are lost on redeploy.

For production, replace local file storage with an S3-compatible store:
1. Set `UPLOAD_DIR` and `OUTPUT_DIR` to `/tmp` (temporary local buffer)
2. Add boto3 to `requirements.txt`
3. After upload, stream to S3; serve downloads via signed URL

Until then, file uploads work in development but not across Railway redeploys.

### Deploy command

Railway auto-deploys on `git push` to the connected branch. To trigger manually:
```bash
railway up
```

---

## Frontend — Vercel

### Initial setup

1. Import the GitHub repo into Vercel
2. Set **Root Directory** to `frontend`
3. Framework: **Vite** (auto-detected)
4. Build command: `npm run build` (default)
5. Output directory: `dist` (default)

### Environment variables (set in Vercel dashboard)

| Variable | Value |
|----------|-------|
| `VITE_API_BASE_URL` | `https://your-backend.up.railway.app` |

**Important:** Vite bakes env vars into the bundle at build time.
After changing `VITE_API_BASE_URL`, you must trigger a new deployment.

### SPA routing

The `frontend/vercel.json` (already committed) handles client-side routing:
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

Without this, direct URL access (e.g., `/programs/3`) returns 404.

### CORS

The backend must allow requests from your Vercel domain.
Set `FRONTEND_URL` on Railway to your Vercel URL.
The backend also allows `*.vercel.app` via regex:
```python
allow_origin_regex=r"https://.*\.vercel\.app"
```
This covers preview deployments automatically.

---

## Common deployment issues

| Problem | Cause | Fix |
|---------|-------|-----|
| `pgvector` type not found | Extension not installed | Run `CREATE EXTENSION IF NOT EXISTS vector;` |
| CORS error in browser | `FRONTEND_URL` not set on Railway | Add env var in Railway dashboard |
| Blank page on Vercel | `VITE_API_BASE_URL` missing | Add env var in Vercel, redeploy |
| 404 on page refresh | `vercel.json` missing or not in root | Confirm `frontend/vercel.json` is committed |
| Uploads lost after redeploy | Ephemeral Railway filesystem | Use `/tmp` or migrate to S3 |
| `postgres://` connection error | Railway uses `postgres://`, SQLAlchemy needs `postgresql://` | `database.py` handles this automatically |

---

## Health check

Railway can ping a health endpoint. The backend exposes:
```
GET /health
→ {"status": "ok"}
```

Set this as the Railway health check path in service settings.

---

## Database backups

Railway Postgres plugin supports point-in-time recovery on paid plans.
For development, manually export:
```bash
railway run pg_dump $DATABASE_URL > backup.sql
```
