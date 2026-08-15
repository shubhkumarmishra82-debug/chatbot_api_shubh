"""
The OpenAI-compatible /v1/chat/completions endpoint. Reply priority:

  1. Calculator tool   (pure arithmetic, answered instantly, no AI call)
  2. Custom replies     (your keyword-matched canned answers)
  3. Your documents      (RAG over content you've added)
  4. Your own AI server  (if OWN_SERVER_URL is set), grounded with search
  5. Live search results (if no AI configured)
  6. Fallback message

Requires an API key (Authorization: Bearer <key>, get one at /api).
Rate-limited per key. Supports streaming (stream: true) via SSE in the
same chunk format OpenAI's API uses, so existing OpenAI client libraries
work against this unmodified (just point base_url at your deployment).
"""
import json
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from . import database, matcher, retrieval, search, tools, config, cache
from .auth import require_api_key
from .observability import estimate_tokens, setup_logging
from .openai_schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    OAIChoice,
    OAIMessage,
    OAIUsage,
)
from .providers import router as ai_router
from .providers import AllProvidersFailedError

log = setup_logging()
router = APIRouter()

FALLBACK_REPLY = (
    "I don't have an answer for that yet. Try asking it as a question, "
    "or ask the bot owner to add a custom reply for this."
)


def _build_response(request_id: str, model: str, content: str,
                     prompt_tokens: int, completion_tokens: int,
                     answer_type: str) -> ChatCompletionResponse:
    return ChatCompletionResponse(
        id=request_id,
        created=int(time.time()),
        model=model,
        choices=[
            OAIChoice(
                index=0,
                message=OAIMessage(role="assistant", content=content),
                finish_reason="stop",
            )
        ],
        usage=OAIUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
        gms_answer_type=answer_type,
    )


async def _resolve_reply(req: ChatCompletionRequest, db: Session, request_id: str, history: list = None):
    """Runs the full priority pipeline, returns (content, answer_type, sources).
    `history` is prior stored turns (if conversation_id was used), prepended
    before the client's own messages."""
    last_user_msg = ""
    for m in reversed(req.messages):
        if m.role == "user":
            last_user_msg = m.content
            break

    # 1. Calculator
    calc_result = tools.try_calculate(last_user_msg)
    if calc_result:
        return calc_result, "calculator", []

    # 2. Custom replies
    custom_replies = db.query(database.CustomReply).all()
    custom_match = matcher.find_custom_reply(last_user_msg, custom_replies)
    if custom_match:
        return custom_match, "custom", []

    # 3-6. Documents -> AI (grounded with search) -> search-only -> fallback
    sources = []
    if ai_router.is_configured():
        system_prompt = config.BOT_PERSONA
        notes = db.query(database.MemoryNote).all()
        if notes:
            system_prompt += "\n\nAdditional instructions you must follow:\n" + "\n".join(
                f"- {n.note}" for n in notes
            )

        doc_chunks = []
        if req.use_documents:
            documents = db.query(database.Document).all()
            doc_chunks = retrieval.top_chunks_for_query(last_user_msg, documents) if documents else []
            if doc_chunks:
                system_prompt += "\n\nRelevant material from your own documents:\n" + "\n".join(
                    f"- ({c['title']}) {c['text']}" for c in doc_chunks
                )

        should_search = req.web_search if req.web_search is not None else not doc_chunks
        if should_search:
            results = await search.web_search(last_user_msg)
            if results:
                system_prompt += "\n\nBackground info found via web search (facts only -- write your own original explanation, do not copy sentences):\n" + "\n".join(
                    f"- {r['title']}: {r['snippet']}" for r in results
                )
                sources = [{"title": r["title"], "link": r["link"]} for r in results]

        full_messages = [{"role": "system", "content": system_prompt}]
        if history:
            full_messages += history
        full_messages += [{"role": m.role, "content": m.content} for m in req.messages]

        cached = cache.get(full_messages, req.model)
        if cached is not None:
            log.info("[%s] cache hit", request_id)
            return cached, "ai", sources

        try:
            content = await ai_router.chat(full_messages, request_id=request_id)
            cache.set(full_messages, req.model, content)
            return content, "ai", sources
        except AllProvidersFailedError as e:
            log.warning("[%s] AI provider failed, degrading to search: %s", request_id, e)
            if sources:
                content = search.format_search_reply(
                    [{"title": s["title"], "snippet": "", "link": s["link"]} for s in sources]
                )
                return content, "search", sources
            return FALLBACK_REPLY, "fallback", []

    # No AI configured at all -- plain transparent search
    if req.web_search is not False and search.looks_like_question(last_user_msg):
        results = await search.web_search(last_user_msg)
        content = search.format_search_reply(results)
        sources = [{"title": r["title"], "link": r["link"]} for r in results]
        return content, ("search" if results else "fallback"), sources

    return FALLBACK_REPLY, "fallback", []


def _load_conversation_history(db: Session, conversation_id: str) -> list:
    """Loads prior turns for a conversation_id as plain role/content dicts."""
    convo = db.query(database.Conversation).filter(database.Conversation.id == conversation_id).first()
    if not convo:
        return []
    return [
        {"role": m.role, "content": m.content}
        for m in sorted(convo.messages, key=lambda m: m.created_at)
    ]


def _get_or_create_conversation(db: Session, conversation_id: str, title_hint: str) -> "database.Conversation":
    convo = db.query(database.Conversation).filter(database.Conversation.id == conversation_id).first()
    if convo:
        return convo
    convo = database.Conversation(id=conversation_id, title=title_hint[:40] or "New Conversation")
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo


def _persist_turn(db: Session, conversation_id: str, user_content: str, assistant_content: str):
    db.add(database.Message(conversation_id=conversation_id, role="user", content=user_content))
    db.add(database.Message(conversation_id=conversation_id, role="assistant", content=assistant_content))
    db.commit()


@router.post("/v1/chat/completions")
async def chat_completions(
    req: ChatCompletionRequest,
    http_request: Request,
    api_key_row: database.ApiKey = Depends(require_api_key),
    db: Session = Depends(database.get_db),
):
    request_id = "chatcmpl-" + uuid.uuid4().hex[:24]

    if not req.messages:
        raise HTTPException(status_code=400, detail="`messages` must not be empty.")
    if any(m.role not in ("system", "user", "assistant") for m in req.messages):
        raise HTTPException(status_code=400, detail="Each message role must be system, user, or assistant.")

    log.info("[%s] key=%s stream=%s messages=%d", request_id, api_key_row.id, req.stream, len(req.messages))

    conversation_id = req.conversation_id
    history = []
    if conversation_id:
        _get_or_create_conversation(db, conversation_id, req.messages[-1].content if req.messages else "")
        history = _load_conversation_history(db, conversation_id)

    if req.stream:
        return StreamingResponse(
            _stream_response(req, db, request_id, api_key_row, history, conversation_id),
            media_type="text/event-stream",
        )

    content, answer_type, sources = await _resolve_reply(req, db, request_id, history=history)

    if conversation_id:
        last_user_msg = next((m.content for m in reversed(req.messages) if m.role == "user"), "")
        _persist_turn(db, conversation_id, last_user_msg, content)

    prompt_tokens = sum(estimate_tokens(m.content) for m in req.messages) + sum(
        estimate_tokens(h["content"]) for h in history
    )
    completion_tokens = estimate_tokens(content)

    api_key_row.total_requests = (api_key_row.total_requests or 0) + 1
    api_key_row.total_tokens = (api_key_row.total_tokens or 0) + prompt_tokens + completion_tokens
    db.commit()

    response = _build_response(request_id, req.model, content, prompt_tokens, completion_tokens, answer_type)
    response.conversation_id = conversation_id
    return response


async def _stream_response(req: ChatCompletionRequest, db: Session, request_id: str,
                            api_key_row: database.ApiKey, history: list = None,
                            conversation_id: str = None):
    """
    SSE stream in OpenAI's chunk format. Note: only the AI-provider path
    streams token-by-token (since that's the only source that generates
    incrementally) -- calculator/custom-reply/search-only answers are
    already fully known, so they're sent as one chunk immediately
    followed by [DONE], which is valid behavior for OpenAI-compatible
    clients either way.
    """
    last_user_msg = ""
    for m in reversed(req.messages):
        if m.role == "user":
            last_user_msg = m.content
            break

    def _chunk(delta: dict, finish_reason=None):
        payload = {
            "id": request_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": req.model,
            "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
        }
        return f"data: {json.dumps(payload)}\n\n"

    calc_result = tools.try_calculate(last_user_msg)
    custom_replies = db.query(database.CustomReply).all()
    custom_match = matcher.find_custom_reply(last_user_msg, custom_replies)

    if calc_result or custom_match:
        content = calc_result or custom_match
        yield _chunk({"role": "assistant", "content": content})
        yield _chunk({}, finish_reason="stop")
        yield "data: [DONE]\n\n"
        if conversation_id:
            _persist_turn(db, conversation_id, last_user_msg, content)
        return

    if not ai_router.is_configured():
        content, _, _ = await _resolve_reply(req, db, request_id, history=history)
        yield _chunk({"role": "assistant", "content": content})
        yield _chunk({}, finish_reason="stop")
        yield "data: [DONE]\n\n"
        if conversation_id:
            _persist_turn(db, conversation_id, last_user_msg, content)
        return

    system_prompt = config.BOT_PERSONA
    documents = db.query(database.Document).all()
    doc_chunks = retrieval.top_chunks_for_query(last_user_msg, documents) if documents else []
    if doc_chunks:
        system_prompt += "\n\nRelevant material from your own documents:\n" + "\n".join(
            f"- ({c['title']}) {c['text']}" for c in doc_chunks
        )
    full_messages = [{"role": "system", "content": system_prompt}]
    if history:
        full_messages += history
    full_messages += [{"role": m.role, "content": m.content} for m in req.messages]

    yield _chunk({"role": "assistant", "content": ""})
    accumulated = ""
    try:
        async for piece in ai_router.chat_stream(full_messages, request_id=request_id):
            accumulated += piece
            yield _chunk({"content": piece})
    except Exception as e:
        log.warning("[%s] stream failed: %s", request_id, e)
        yield _chunk({"content": f"\n\n[stream error: {e}]"})
    yield _chunk({}, finish_reason="stop")
    yield "data: [DONE]\n\n"

    if conversation_id and accumulated:
        _persist_turn(db, conversation_id, last_user_msg, accumulated)
