# Railway setup — JuaKazi FastAPI backend

Use these steps to run the JuaKazi API on Railway so your Vercel frontend (or local app) can call `POST /rewrite`.

---

## 1. Sign in and create a project

1. Go to **[railway.app](https://railway.app)** and sign in (e.g. with GitHub).
2. Click **New Project**.
3. Choose **Deploy from GitHub repo**.
4. Select the **gender-sensitization-engine** repository (connect GitHub if asked).
5. Railway will add a service from that repo.

---

## 2. Use the API Dockerfile

1. Open the new service (click the service card).
2. Go to **Settings** (or the **Settings** tab).
3. Find **Build** or **Build & Deploy**.
4. Set:
   - **Builder:** Dockerfile (or “Docker”).
   - **Dockerfile path:** `Dockerfile.api`  
     (or “Dockerfile” if your UI only has a single Dockerfile field — then rename `Dockerfile.api` to `Dockerfile` for this repo, or set the path to `Dockerfile.api` if the field accepts a path).
5. **Root Directory:** leave **empty** (repo root). The Dockerfile is at the repo root.
6. **Start command:** leave empty. The Dockerfile already runs `uvicorn`.

---

## 3. Make the API public

1. In the same service, go to **Settings** → **Networking** (or **Deploy** → **Networking**).
2. Under **Public networking** or **Generate domain**, click to **generate a public URL** or **add a domain**.
3. Copy the URL (e.g. `https://gender-sensitization-engine-production-xxxx.up.railway.app`).  
   **No trailing slash.**

---

## 4. Deploy

1. Trigger a deploy (e.g. **Deploy** or push a commit; Railway often auto-deploys from main).
2. Wait for the build to finish (build logs should show Docker build and `uvicorn`).
3. Open **`https://YOUR_RAILWAY_URL/docs`** in a browser. You should see **FastAPI Swagger** and **POST /rewrite**.

---

## 5. Connect your frontend

- **Vercel:** In the Vercel project, set **Environment variable** `NEXT_PUBLIC_API_URL` = your Railway URL (e.g. `https://xxx.up.railway.app`). Redeploy the frontend.
- **Local:** Don’t set `NEXT_PUBLIC_API_URL` for localhost, or set it to `http://localhost:8000` only if you’re running the API locally.

---

## Summary checklist

- [ ] Signed in at railway.app, new project from GitHub repo **gender-sensitization-engine**
- [ ] Service uses **Dockerfile** with path **`Dockerfile.api`**, root directory empty
- [ ] **Public URL** generated and copied (no trailing slash)
- [ ] **`https://YOUR_RAILWAY_URL/docs`** shows FastAPI Swagger and **POST /rewrite**
- [ ] **Vercel** (or other frontend) has **`NEXT_PUBLIC_API_URL`** = that Railway URL; frontend redeployed

---

## If the UI looks different

Railway sometimes changes the layout. If you don’t see “Dockerfile path”:

- Look for **Build** → **Dockerfile** or **Docker** and a text field for the Dockerfile name/path; enter **Dockerfile.api**.
- Or in the repo, temporarily copy the contents of `Dockerfile.api` into a file named `Dockerfile` in the repo root, commit, and then in Railway use **Dockerfile** (default) with no path. Remember to revert if you need the original `Dockerfile` for something else.

If the build fails, check the build logs: the Docker build must have access to `api/`, `core/`, `config.py`, `rules/`, `pyproject.toml`, and `setup.py` at the repo root.
