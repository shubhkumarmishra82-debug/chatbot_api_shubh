# GMS Chatbot API — Documentation

Created by **Shubh**. Base URL after deploy: `https://your-project.vercel.app`

## How it decides what to reply

For every message sent to `/chat`, in order:

1. **Custom replies** — checks your own trigger/response pairs (see below). If a keyword matches, that exact response is returned. Nothing external is touched.
2. **Google search** — if no custom reply matched and the message looks like a question (ends in `?`, starts with a question word, or looks like a math/physics problem), it queries Google's Custom Search API and returns the results **as search results** — title, snippet, and link for each, clearly presented as "here's what I found." Nothing is reworded to look like the bot wrote it.
3. **Fallback** — otherwise, a default "I don't have an answer for that" message.

Every response tells you which path was taken via `answer_type`: `"custom"`, `"search"`, or `"fallback"`.

---

## Endpoints

### `GET /`
Basic status check.
```json
{ "app": "GMS Chatbot", "creator": "Shubh", "status": "running", "docs": "/docs" }
```

### `GET /health`
Confirms what's configured (useful for debugging deploys).
```json
{
  "status": "ok",
  "database_configured": true,
  "google_search_configured": true
}
```

---

### `POST /chat`
Send a message, get a reply.

**Request**
```json
{
  "message": "What is Newton's second law?",
  "conversation_id": null
}
```
`conversation_id`: omit or `null` to start a new conversation; pass the one you got back to continue it.

**Response**
```json
{
  "conversation_id": "b3f1...",
  "reply": "Here's what I found:\n\n**Newton's Second Law**\nForce equals mass times acceleration...\nhttps://...",
  "answer_type": "search",
  "sources": [
    { "title": "Newton's Second Law", "link": "https://..." }
  ]
}
```

---

### Custom replies — your own canned answers

#### `POST /custom-replies`
```json
{ "trigger": "hi,hello,hey", "response": "Hi! I'm GMS Chatbot, made by Shubh 👋" }
```
`trigger` is comma-separated keywords; if the user's message contains **any** of them, this response is returned. More specific (longer) keywords win if several match.

Response:
```json
{ "id": "a1c2...", "trigger": "hi,hello,hey", "response": "Hi! I'm GMS Chatbot...", "created_at": "2026-08-03T10:00:00" }
```

#### `GET /custom-replies`
Lists all your custom replies.

#### `DELETE /custom-replies/{id}`
Removes one.

---

### Conversations

#### `GET /conversations`
List all conversations (id, title, created_at).

#### `GET /conversations/{id}`
Full message history for one conversation.

#### `DELETE /conversations/{id}`
Deletes a conversation and its messages.

---

### Trainer notes (optional, reserved for future use)

`POST /memory`, `GET /memory`, `DELETE /memory/{id}` — stored but not currently used in the reply logic (there's no AI model in this build to feed instructions to). Left in place in case you add one later.

---

## Setup checklist

1. **Database**: Vercel project → Storage tab → Create Database → Postgres. Sets `POSTGRES_URL` automatically.
2. **Google Search**:
   - Enable "Custom Search API" at console.cloud.google.com
   - Create a search engine at programmablesearchengine.google.com (set to "search the entire web")
   - Set `GOOGLE_API_KEY` and `GOOGLE_CSE_ID` in Vercel env vars
3. **Branding**: set `APP_NAME` / `CREATOR_NAME` env vars.
4. Redeploy after adding env vars: `vercel --prod`

## Example: building up your bot's personality

```bash
curl -X POST https://your-project.vercel.app/custom-replies \
  -H "Content-Type: application/json" \
  -d '{"trigger": "who made you,who created you", "response": "I was built by Shubh!"}'

curl -X POST https://your-project.vercel.app/custom-replies \
  -H "Content-Type: application/json" \
  -d '{"trigger": "bye,goodbye", "response": "See you later! 👋"}'
```

Then any message containing "who made you" or "bye" hits these instantly — no search needed.

## Limits to know about

- Google Custom Search free tier: 100 queries/day.
- Vercel Hobby plan function timeout: 10s (60s on Pro) — fine for search, since there's no AI generation step slowing things down.
- CORS is currently open (`*`) — restrict to your actual frontend domain before going live.

---

## `/v1/chat/completions` — OpenAI-compatible endpoint

This is the production-grade endpoint, built for real integrations (external apps, OpenAI client libraries pointed at your `base_url`, etc). It requires an API key.

### Architecture

```
Request
  │
  ├─ 1. Calculator tool     (pure arithmetic, e.g. "12 * 7" -- answered instantly, no AI call)
  ├─ 2. Custom replies       (your keyword-matched canned answers)
  ├─ 3. Your documents        (RAG -- relevant chunks pulled in as context)
  ├─ 4. Your own AI server    (if OWN_SERVER_URL is set), grounded with live search
  ├─ 5. Live search results   (if no AI server configured)
  └─ 6. Fallback message
```

No AI vendor key is used anywhere in this pipeline. Step 4 only activates if you've pointed `OWN_SERVER_URL` at a server you control.

### Authentication

```
Authorization: Bearer <your_api_key>
```
Get a key at `/api`. Missing/invalid key → `401`. Over the rate limit → `429` (default 30 requests/minute per key, set via `RATE_LIMIT_PER_MINUTE` env var).

### Request

```bash
curl https://your-project.vercel.app/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "gms-default",
    "messages": [
      {"role": "user", "content": "What is 15% of 240?"}
    ]
  }'
```

### Response (standard OpenAI shape + one extension field)

```json
{
  "id": "chatcmpl-abc123...",
  "object": "chat.completion",
  "created": 1733500000,
  "model": "gms-default",
  "choices": [
    {
      "index": 0,
      "message": { "role": "assistant", "content": "15% of 240 is 36." },
      "finish_reason": "stop"
    }
  ],
  "usage": { "prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20 },
  "gms_answer_type": "ai"
}
```

`gms_answer_type` tells you which layer answered: `calculator`, `custom`, `ai`, `search`, or `fallback`.

### Extension fields (optional, beyond standard OpenAI)

| Field | Default | Effect |
|---|---|---|
| `web_search` | auto | `true` forces a search, `false` disables it, omitted = auto-decide |
| `use_documents` | `true` | whether to search your own document knowledge base |

### Streaming

Set `"stream": true` and you'll get Server-Sent Events in OpenAI's exact chunk format:
```
data: {"id":"chatcmpl-...","object":"chat.completion.chunk","choices":[{"delta":{"content":"Hello"},"index":0,"finish_reason":null}]}

data: {"id":"chatcmpl-...","object":"chat.completion.chunk","choices":[{"delta":{},"index":0,"finish_reason":"stop"}]}

data: [DONE]
```
This means official OpenAI client libraries (Python, JS, etc) work against this endpoint unmodified — just point `base_url` at `https://your-project.vercel.app/v1` and pass your own API key.

### Honest limitations (so nothing surprises you later)

- **Token counts are estimated** (chars ÷ 4), not exact — there's no tokenizer dependency bundled to keep the deploy lightweight.
- **Caching is per-warm-instance, not distributed** — repeat identical requests are only cached if they hit the same warm serverless instance. Cold starts always recompute. For guaranteed cross-instance caching, an external store like Upstash Redis would be the next step.
- **Rate limiting is DB-backed** (not in-memory) specifically because serverless functions don't share memory between invocations — this makes it accurate, but each check costs one extra DB round-trip.
- **Retries** happen once per provider on failure, with a short backoff, before falling back to search/fallback.

---

## `/reseed`

`POST /reseed` — adds any new entries from the code's built-in starter dataset (`app/seed_data.py`) that aren't already in your database, without touching anything you've customized. Useful after pulling a code update that expanded the seed list.

---

## Conversation memory in `/v1/chat/completions`

Standard OpenAI usage is stateless (you resend the full `messages` array every call). This API also supports an optional extension for server-side memory:

```json
{
  "messages": [{"role": "user", "content": "What's the capital of France?"}],
  "conversation_id": "my-session-123"
}
```

Pass any string as `conversation_id` (reuse the same one across calls). The server stores each turn and automatically prepends prior history before calling the AI, so you only need to send the newest message each time instead of the whole transcript. The same `conversation_id` comes back in the response. Omit it entirely to use the standard stateless OpenAI pattern instead.

## Structured errors

All `/v1/*` errors follow OpenAI's error shape:
```json
{ "error": { "message": "...", "type": "rate_limit_error", "code": 429 } }
```
`type` is one of `invalid_request_error`, `authentication_error`, `rate_limit_error`, `not_found_error`, `server_error`.

## Database migrations

`app/migrations.py` — a lightweight versioned migration runner (no Alembic dependency). Runs automatically on every cold start; each migration only applies once (tracked in a `schema_migrations` table). This matters because `create_all()` alone only creates missing *tables* — it never adds new *columns* to a table that already exists, which would otherwise cause "column does not exist" errors after a schema change to an existing model.
