import os
import secrets

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy.orm import Session

from . import database, schemas, search, matcher, config, llm, retrieval, seed_data, v1, openai_schemas

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


def render_template(filename: str) -> str:
    path = os.path.join(TEMPLATES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    return (
        html.replace("{{APP_NAME}}", config.APP_NAME)
        .replace("{{CREATOR_NAME}}", config.CREATOR_NAME)
    )

app = FastAPI(title=config.APP_NAME)

# Lock this down to your actual frontend domain before going to production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1.router)


def _openai_error_type(status_code: int) -> str:
    return {
        400: "invalid_request_error",
        401: "authentication_error",
        404: "not_found_error",
        429: "rate_limit_error",
    }.get(status_code, "server_error")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if request.url.path.startswith("/v1/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.detail,
                    "type": _openai_error_type(exc.status_code),
                    "code": exc.status_code,
                }
            },
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def readable_error_handler(request: Request, exc: Exception):
    # Turns any unhandled crash into a plain JSON message instead of
    # Vercel's generic "Serverless Function has crashed" page.
    if request.url.path.startswith("/v1/"):
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(exc), "type": "server_error", "code": 500}},
        )
    return JSONResponse(status_code=500, content={"error": str(exc)})


@app.on_event("startup")
def on_startup():
    try:
        database.init_db()
        if database.SessionLocal is not None:
            db = database.SessionLocal()
            try:
                seed_data.seed_if_empty(db, database)
            finally:
                db.close()
    except Exception:
        pass  # never let a startup hiccup crash the whole function


@app.get("/")
def root():
    return {
        "app": config.APP_NAME,
        "creator": config.CREATOR_NAME,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/code", response_class=HTMLResponse)
def code_page():
    return render_template("code.html")


@app.get("/ai", response_class=HTMLResponse)
def ai_page():
    return render_template("chat.html")


@app.get("/chat-ui", response_class=HTMLResponse)
def chat_ui_page():
    return render_template("chat.html")


@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return render_template("admin.html")


@app.get("/api", response_class=HTMLResponse)
def api_key_page():
    return render_template("api_key.html")


@app.post("/api/generate-key", response_model=schemas.ApiKeyOut)
def generate_api_key(db: Session = Depends(database.get_db)):
    new_key = "gms_" + secrets.token_urlsafe(24)
    row = database.ApiKey(key=new_key)
    db.add(row)
    db.commit()
    db.refresh(row)
    return schemas.ApiKeyOut(api_key=row.key, status="success")


@app.post("/reseed")
def reseed(db: Session = Depends(database.get_db)):
    added = seed_data.add_missing_seed_replies(db, database)
    return {"added": added}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": config.APP_NAME,
        "creator": config.CREATOR_NAME,
        "database_configured": database.engine is not None,
        "google_search_configured": bool(search.GOOGLE_API_KEY and search.GOOGLE_CSE_ID),
        "ai_configured": llm.is_configured(),
        "ai_provider": llm.active_provider(),
        "v1_endpoint": "/v1/chat/completions (requires Authorization: Bearer <key>, get one at /api)",
    }


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

FALLBACK_REPLY = (
    "I don't have an answer for that yet. Try asking it as a question, "
    "or ask the bot owner to add a custom reply for this."
)


@app.post("/chat", response_model=schemas.ChatResponse)
async def chat(req: schemas.ChatRequest, db: Session = Depends(database.get_db)):
    # Get or create the conversation
    if req.conversation_id:
        conversation = (
            db.query(database.Conversation)
            .filter(database.Conversation.id == req.conversation_id)
            .first()
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = database.Conversation(title=req.message[:40] or "New Conversation")
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    db.add(database.Message(conversation_id=conversation.id, role="user", content=req.message))
    db.commit()

    # Delegate to the SAME resolution pipeline /v1/chat/completions uses
    # (calculator -> custom replies -> documents -> AI -> search ->
    # fallback), so there's exactly one place this logic lives instead of
    # two copies that can drift out of sync with each other.
    history_messages = [
        openai_schemas.OAIMessage(role=m.role, content=m.content)
        for m in sorted(conversation.messages, key=lambda m: m.created_at)
    ]
    fake_request = openai_schemas.ChatCompletionRequest(
        messages=history_messages, use_documents=True, web_search=None
    )
    reply_text, answer_type, sources = await v1._resolve_reply(fake_request, db, request_id="widget")
    sources_out = [schemas.SourceOut(title=s["title"], link=s["link"]) for s in sources]

    db.add(database.Message(conversation_id=conversation.id, role="assistant", content=reply_text))
    db.commit()

    return schemas.ChatResponse(
        conversation_id=conversation.id,
        reply=reply_text,
        answer_type=answer_type,
        sources=sources_out,
    )


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------

@app.get("/conversations", response_model=list[schemas.ConversationOut])
def list_conversations(db: Session = Depends(database.get_db)):
    return (
        db.query(database.Conversation)
        .order_by(database.Conversation.created_at.desc())
        .all()
    )


@app.get("/conversations/{conversation_id}", response_model=schemas.ConversationDetail)
def get_conversation(conversation_id: str, db: Session = Depends(database.get_db)):
    conversation = (
        db.query(database.Conversation)
        .filter(database.Conversation.id == conversation_id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(database.get_db)):
    conversation = (
        db.query(database.Conversation)
        .filter(database.Conversation.id == conversation_id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conversation)
    db.commit()
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Bulk import -- load many custom replies and/or documents in one request
# ---------------------------------------------------------------------------

@app.post("/bulk-import", response_model=schemas.BulkImportOut)
def bulk_import(payload: schemas.BulkImportIn, db: Session = Depends(database.get_db)):
    for r in payload.custom_replies:
        db.add(database.CustomReply(trigger=r.trigger, response=r.response))
    for d in payload.documents:
        db.add(database.Document(title=d.title, content=d.content))
    db.commit()
    return schemas.BulkImportOut(
        custom_replies_added=len(payload.custom_replies),
        documents_added=len(payload.documents),
    )


# ---------------------------------------------------------------------------
# Your own documents (private knowledge base)
# ---------------------------------------------------------------------------

@app.post("/documents", response_model=schemas.DocumentOut)
def add_document(doc: schemas.DocumentIn, db: Session = Depends(database.get_db)):
    row = database.Document(title=doc.title, content=doc.content)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/documents", response_model=list[schemas.DocumentOut])
def list_documents(db: Session = Depends(database.get_db)):
    return db.query(database.Document).order_by(database.Document.created_at.desc()).all()


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str, db: Session = Depends(database.get_db)):
    row = db.query(database.Document).filter(database.Document.id == doc_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Custom replies (your own canned answers)
# ---------------------------------------------------------------------------

@app.post("/custom-replies", response_model=schemas.CustomReplyOut)
def add_custom_reply(entry: schemas.CustomReplyIn, db: Session = Depends(database.get_db)):
    row = database.CustomReply(trigger=entry.trigger, response=entry.response)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/custom-replies", response_model=list[schemas.CustomReplyOut])
def list_custom_replies(db: Session = Depends(database.get_db)):
    return db.query(database.CustomReply).order_by(database.CustomReply.created_at).all()


@app.delete("/custom-replies/{reply_id}")
def delete_custom_reply(reply_id: str, db: Session = Depends(database.get_db)):
    row = db.query(database.CustomReply).filter(database.CustomReply.id == reply_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Custom reply not found")
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Trainer notes -- kept for optional future use (not used in the chat flow
# right now since there's no LLM to feed instructions to, but the storage
# and endpoints are here if you add one later)
# ---------------------------------------------------------------------------

@app.post("/memory", response_model=schemas.MemoryNoteOut)
def add_memory_note(note: schemas.MemoryNoteIn, db: Session = Depends(database.get_db)):
    entry = database.MemoryNote(note=note.note)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@app.get("/memory", response_model=list[schemas.MemoryNoteOut])
def list_memory_notes(db: Session = Depends(database.get_db)):
    return db.query(database.MemoryNote).order_by(database.MemoryNote.created_at).all()


@app.delete("/memory/{note_id}")
def delete_memory_note(note_id: str, db: Session = Depends(database.get_db)):
    entry = db.query(database.MemoryNote).filter(database.MemoryNote.id == note_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(entry)
    db.commit()
    return {"status": "deleted"}
