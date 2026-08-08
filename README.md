# GMS Chatbot Backend

Created by **Shubh**. FastAPI backend, deployable on **Vercel**, with:
- **Postgres** for chat history (Vercel Postgres, Neon, or Supabase)
- **Groq** serving open-source models (Llama 3.3 etc.) — the deployable
  alternative to running Ollama locally, since Vercel functions can't host
  a model process
- **Google Custom Search** grounding for math/physics/problem questions —
  the bot writes its own original explanation using search results as
  background facts, and returns the source links so nothing looks copied
- **Trainer notes** — persistent instructions you feed the bot that apply
  to every conversation

## 1. Deploy to Vercel

```bash
npm i -g vercel        # if you don't have the CLI
cd gms-chatbot
vercel                 # follow prompts, link/create a project
```

Or: push this folder to a GitHub repo and import it at vercel.com/new.

## 2. Add a Postgres database

In your Vercel project → **Storage** tab → **Create Database** → Postgres.
This automatically sets the `POSTGRES_URL` env var — no manual config needed.

## 3. Set the other environment variables

In your Vercel project → **Settings** → **Environment Variables**, add:

| Variable | Where to get it |
|---|---|
| `GROQ_API_KEY` | Free at https://console.groq.com/keys |
| `GOOGLE_API_KEY` | https://console.cloud.google.com → enable "Custom Search API" → create credentials |
| `GOOGLE_CSE_ID` | https://programmablesearchengine.google.com → create a search engine, set it to "Search the entire web" |
| `APP_NAME` | e.g. `GMS Chatbot` |
| `CREATOR_NAME` | e.g. `Shubh` |

Then redeploy: `vercel --prod`

## 4. Test it

```bash
curl -X POST https://your-project.vercel.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Solve 2x + 5 = 15"}'
```

Response:
```json
{
  "conversation_id": "abc-123",
  "reply": "To solve 2x + 5 = 15, first subtract 5 from both sides...",
  "sources": [{"title": "...", "link": "https://..."}]
}
```

Continue the same conversation by passing `conversation_id` back in the next request.

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/chat` | Send a message, get a reply (auto-searches for math/physics/problem questions) |
| GET | `/conversations` | List all conversations |
| GET | `/conversations/{id}` | Full history for one conversation |
| DELETE | `/conversations/{id}` | Delete a conversation |
| POST | `/memory` | Add a "trainer" note — a persistent instruction, e.g. `{"note": "Always explain in simple English"}` |
| GET | `/memory` | List trainer notes |
| DELETE | `/memory/{id}` | Remove a trainer note |
| GET | `/health` | Health check + branding info |

## Branding

Edit `app/config.py` or just set `APP_NAME` / `CREATOR_NAME` / `BOT_PERSONA`
env vars in Vercel — no redeploy of code needed, just re-run with new env vars.

## Local development

```bash
pip install -r requirements.txt
export POSTGRES_URL=postgresql://localhost/gms_chatbot   # or any Postgres you have
export GROQ_API_KEY=...
export GOOGLE_API_KEY=...
export GOOGLE_CSE_ID=...
uvicorn app.main:app --reload --port 8000
```

## Known limits to plan around

- **Vercel function timeout**: 10s on the Hobby plan (60s on Pro). A slow
  search + LLM call can bump into this — Pro plan or trimming `num` results
  in `search.py` helps.
- **Google Custom Search free tier**: 100 queries/day. Fine for testing;
  paid tier is $5 per 1,000 queries beyond that if you scale up.
- **No streaming yet**: replies come back all at once. Can be added with
  `StreamingResponse` if you want token-by-token output later.
- **CORS is wide open** (`allow_origins=["*"]`) — restrict to your actual
  frontend domain before going live.



lulu
