from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from . import database, schemas, search, matcher, config

app = FastAPI(title=config.APP_NAME)

# Lock this down to your actual frontend domain before going to production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def readable_error_handler(request: Request, exc: Exception):
    # Turns any unhandled crash into a plain JSON message instead of
    # Vercel's generic "Serverless Function has crashed" page.
    return JSONResponse(status_code=500, content={"error": str(exc)})


@app.on_event("startup")
def on_startup():
    database.init_db()  # no-op if no DB is configured yet -- won't crash


@app.get("/")
def root():
    return {
        "app": config.APP_NAME,
        "creator": config.CREATOR_NAME,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": config.APP_NAME,
        "creator": config.CREATOR_NAME,
        "database_configured": database.engine is not None,
        "google_search_configured": bool(search.GOOGLE_API_KEY and search.GOOGLE_CSE_ID),
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

    # 1. Check your own custom replies first
    custom_replies = db.query(database.CustomReply).all()
    custom_match = matcher.find_custom_reply(req.message, custom_replies)

    sources_out = []
    if custom_match:
        reply_text = custom_match
        answer_type = "custom"

    # 2. If it looks like a question, search Google and return results transparently
    elif search.looks_like_question(req.message):
        results = await search.google_search(req.message)
        reply_text = search.format_search_reply(results)
        sources_out = [schemas.SourceOut(title=r["title"], link=r["link"]) for r in results]
        answer_type = "search" if results else "fallback"

    # 3. Otherwise, fallback
    else:
        reply_text = FALLBACK_REPLY
        answer_type = "fallback"

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
