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
