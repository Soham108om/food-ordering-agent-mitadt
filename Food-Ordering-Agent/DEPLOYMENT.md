# Free-tier deployment

This setup hosts the Next.js frontend on Vercel and the FastAPI backend on
Render. The frontend proxies `/api/v1/*` requests to the backend so browser
requests and the OAuth callback stay on the frontend origin.

## Important limitations

- Render's free web service can sleep when idle. The first request after sleep
  may take a while.
- The SQLite file is stored under `/tmp` and is not durable. Sessions,
  authentication tokens, and workflow state may be lost when the service
  restarts or redeploys. Do not use this setup for real orders or important
  personal data.
- Free-tier quotas and availability are controlled by each hosting provider.
- Live Swiggy OAuth/MCP access depends on the Swiggy integration accepting the
  deployed redirect URI. Never put API keys or tokens in source control.

## 1. Deploy the backend to Render

1. In Render, create a Blueprint from the GitHub repository. Select the
   repository root containing `render.yaml` and deploy the `food-ordering-agent-api`
   service.
2. In the service's Environment settings, set:
   - `GEMINI_API_KEY`: your Gemini API key.
   - `SWIGGY_REDIRECT_URI`: `https://YOUR-VERCEL-DOMAIN/api/v1/auth/callback`
   - `FRONTEND_ORIGIN`: `https://YOUR-VERCEL-DOMAIN`
3. Wait for the service to deploy. Verify its health URL, which is the Render
   service URL followed by `/`.

Render generates `SESSION_ENCRYPTION_KEY` through the Blueprint. Keep it
private and do not rotate it while expecting existing tokens to remain
decryptable.

## 2. Deploy the frontend to Vercel

1. Import the same GitHub repository into Vercel.
2. Set the Root Directory to `Food-Ordering-Agent/frontend`.
3. Add the environment variable `BACKEND_URL` with the Render service URL,
   without a trailing slash (for example, `https://your-service.onrender.com`).
4. Deploy and note the Vercel domain.
5. Update the Render `SWIGGY_REDIRECT_URI` and `FRONTEND_ORIGIN` values with
   that exact Vercel domain, then redeploy the Render service.

The callback URL must exactly match the redirect URI accepted by the Swiggy
OAuth integration. If the provider requires allowlisting, add the deployed
callback there as well.

## 3. Verify

1. Open the Vercel site and check that the home page loads.
2. Open `https://YOUR-VERCEL-DOMAIN/api/v1/auth/status` to verify the
   frontend proxy reaches the backend. An unauthenticated response is expected.
3. Try Swiggy login only after confirming the deployed callback URL is
   accepted. Do not confirm or place a real order during a deployment test.

For durable sessions, replace the SQLite session store with a persistent
database before relying on hosted authentication or orders.
