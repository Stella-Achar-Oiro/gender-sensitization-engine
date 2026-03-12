# Vercel deploy steps (frontend only)

Use these steps to put the JuaKazi web app on Vercel so experts can try it.  
You need the **API already deployed** (e.g. on Railway or Render) and its public URL.

---

## First-time setup (new project)

### 1. Sign in and import the repo

1. Open **[vercel.com](https://vercel.com)** and sign in (GitHub recommended).
2. Click **Add New…** → **Project**.
3. Import the **gender-sensitization-engine** repository (connect GitHub if needed).
4. Click **Import**.

### 2. Set the root directory

1. In **Configure Project**, find **Root Directory**.
2. Click **Edit** and set it to: **`apps/web`**  
   (so Vercel builds the Next.js app, not the repo root).
3. Leave **Framework Preset** as **Next.js** (auto-detected).

### 3. Add the API URL (required)

1. In the same screen, open **Environment Variables**.
2. Add a variable:
   - **Name:** `NEXT_PUBLIC_API_URL`
   - **Value:** your API URL, e.g.  
     `https://your-app.up.railway.app` or  
     `https://juakazi-api.onrender.com`
3. **No trailing slash.**  
   Use the same value for Production, Preview, and Development if you want.
4. Click **Add** (or **Save**).

### 4. Deploy

1. Click **Deploy**.
2. Wait for the build to finish.
3. Open the generated URL (e.g. `https://your-project.vercel.app`).

### 5. Test

1. Open the app URL.
2. Go to **Analyse** (or the main analysis page).
3. Choose a language, enter text, and run analysis.  
   If you see “API error” or no corrections:
   - `NEXT_PUBLIC_API_URL` must be the **JuaKazi FastAPI** backend only (from `Dockerfile.api`). Do not use a URL that serves another app (e.g. NiceGUI). Open `https://your-api-url/docs` — you should see FastAPI Swagger and `POST /rewrite`. Redeploy after changing env vars.

---

## I already have Vercel set up — what do I update?

If the app is deployed but you get **"Backend returned 404 or an HTML page"** or Analyse doesn’t work:

1. **Fix the backend URL**
   - Vercel dashboard → your project → **Settings** → **Environment Variables**.
   - Find **`NEXT_PUBLIC_API_URL`**.
   - Set its value to your **JuaKazi FastAPI** URL only (the one that shows Swagger at `/docs` and has `POST /rewrite`). Example: `https://your-api.up.railway.app` (no trailing slash).
   - If you don’t have the API deployed yet, deploy it first (see [DEPLOY_WEB.md](DEPLOY_WEB.md)) and use that URL here.

2. **Redeploy so the new env is used**
   - **Deployments** tab → open the **⋮** menu on the latest deployment → **Redeploy** (or push a new commit).
   - Env vars are baked in at build time; changing them alone is not enough until you redeploy.

3. **Check Root Directory**
   - **Settings** → **General** → **Root Directory** must be **`apps/web`**. If it’s empty or wrong, change it and redeploy.

4. **Verify the API**
   - In a browser, open `https://YOUR_API_URL/docs`. You must see **FastAPI Swagger** and **POST /rewrite**. If you see another UI (e.g. NiceGUI) or 404, use a different URL in `NEXT_PUBLIC_API_URL`.

---

## Summary checklist

- [ ] Repo imported on Vercel  
- [ ] **Root Directory** = `apps/web`  
- [ ] **Environment variable** `NEXT_PUBLIC_API_URL` = your API URL (no trailing slash)  
- [ ] Deploy finished and app URL opens  
- [ ] Analyse page works with your API  

For **deploying the API** (Railway or Render), see **[DEPLOY_WEB.md](DEPLOY_WEB.md)**.
