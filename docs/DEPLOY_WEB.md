# Hosting the JuaKazi web app for experts

No Streamlit, no HuggingFace. Use **Vercel** (frontend) + **Railway** or **Render** (API).

## 1. Deploy the API (backend)

### Option A: Railway

1. Go to [railway.app](https://railway.app), sign in with GitHub.
2. **New Project** → **Deploy from GitHub repo** → select `gender-sensitization-engine`.
3. **Settings** → set **Root Directory** to repo root (leave empty).
4. **Settings** → **Build**:  
   - Builder: **Dockerfile**  
   - Dockerfile path: `Dockerfile.api`
5. **Settings** → **Deploy**: no start command needed (Dockerfile CMD runs uvicorn).
6. **Settings** → **Networking** → enable **Public networking**; note the generated URL (e.g. `https://xxx.up.railway.app`).
7. Deploy. After build, copy the **public URL** — you’ll use it as `NEXT_PUBLIC_API_URL` for the frontend.

### Option B: Render

1. Go to [render.com](https://render.com), sign in with GitHub.
2. **New** → **Web Service** → connect the repo.
3. **Build & deploy**:  
   - Environment: **Docker**  
   - Dockerfile path: `Dockerfile.api` (or leave blank if Dockerfile.api is at root).
4. **Instance type**: Free or paid. Ensure **Auto-Deploy** is on if you want.
5. After deploy, copy the service URL (e.g. `https://juakazi-api.onrender.com`).

---

## 2. Deploy the frontend (Vercel)

**Step-by-step:** see **[VERCEL_DEPLOY_STEPS.md](VERCEL_DEPLOY_STEPS.md)** for copy-paste instructions.

Summary:
1. Go to [vercel.com](https://vercel.com), sign in with GitHub.
2. **Add New** → **Project** → import `gender-sensitization-engine`.
3. **Configure**: **Root Directory** = `apps/web` (not repo root). Framework: Next.js.
4. **Environment Variables**: add `NEXT_PUBLIC_API_URL` = your API URL (no trailing slash).
5. Deploy. Experts can use the Vercel URL to try the app.

---

## 3. Local dev (no hosting)

- **API**: from repo root: `uvicorn api.main:app --reload --host 0.0.0.0 --port 8000`
- **Web**: `cd apps/web && npm run dev` — open http://localhost:3000; the app proxies `/api` to port 8000 in development.

---

## 4. If the app shows “API error”

- **Use the JuaKazi FastAPI backend only.** `NEXT_PUBLIC_API_URL` must point to the app that runs `uvicorn api.main:app` (or the image built from `Dockerfile.api`). Do **not** point it at another service (e.g. NiceGUI, Streamlit, or a different project).
- Check the backend: open `{YOUR_API_URL}/docs` in a browser. You should see **FastAPI Swagger** with `POST /rewrite`. If you see a different UI or 404, that URL is wrong.
- Local dev: run `uvicorn api.main:app --reload --host 0.0.0.0 --port 8000` and nothing else on port 8000.
- CORS: the API has `allow_origins=["*"]`; no extra CORS config needed.
