This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### Local development (one command)

From the **repo root**:

```bash
make run
```

Then open **http://localhost:3000** and click **Analyse**. This starts the API and the Next.js UI together; Ctrl+C stops both. The UI calls the backend via a dev proxy (`/api` → backend), so Analyse works without any `.env` setup.

### Local 404 or “Backend returned 404 or an HTML page”?

The frontend proxies `/api` to **http://127.0.0.1:8000**. If that fails, one of these is wrong:

1. **Nothing (or the wrong app) is on port 8000**
   - **Fix:** Start the JuaKazi API first. From the **repo root**:  
     `uvicorn api.main:app --reload --host 0.0.0.0 --port 8000`  
     Or use `make run-api` in one terminal, then `make run-web` (or `cd apps/web && npm run dev`) in another.
   - **Check:** Open http://localhost:8000/docs — you must see **FastAPI Swagger** and **POST /rewrite**. If you see a different UI (e.g. NiceGUI) or “connection refused”, something else is using 8000 or the API isn’t running. Stop any other app on 8000 and start only the FastAPI app.

2. **You only started the frontend**
   - The Next.js dev server (port 3000) is running, but the API (port 8000) is not. Start the API as above, then try Analyse again.

**One command for both:** From repo root, `make run` starts the API and the web app together.

### Docker (API + Next.js)

From the **repo root**: `make up-web` — starts API on :8000 and this app on :3000. Open http://localhost:3000; the app is built with `NEXT_PUBLIC_API_URL=http://localhost:8000` so the browser can reach the API.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel (host for experts)

To host the app so experts can try it (no Streamlit, no HuggingFace):

1. **Deploy the API** (Railway or Render) using the repo’s `Dockerfile.api`. See **[docs/DEPLOY_WEB.md](../docs/DEPLOY_WEB.md)** for step-by-step instructions.
2. **Deploy this frontend** on [Vercel](https://vercel.com): import the repo, set **Root Directory** to `apps/web`, and add env **`NEXT_PUBLIC_API_URL`** = your API URL (e.g. `https://your-api.up.railway.app`).

Details: **[docs/DEPLOY_WEB.md](../docs/DEPLOY_WEB.md)**.
