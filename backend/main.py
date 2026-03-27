"""
Multilingual Government Complaint Portal — FastAPI Backend
Run: uvicorn backend.main:app --reload --port 8000
"""

import uuid
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Internal imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from backend.database import get_db, create_tables, Complaint
from backend.services.whisper_service import transcribe_audio, detect_language
from backend.services.ollama_service import translate_to_english, generate_summary, assess_priority
from backend.services.classifier_service import classify_complaint
from backend.utils.report_generator import generate_complaint_report

app = FastAPI(
    title="Multilingual Complaint Portal API",
    description="Government complaint portal supporting voice, text, and file submissions in any language.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    create_tables()
    print("[API] Database ready.")


# ──────────────────────────────────────────────
# HEALTH
# ──────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ──────────────────────────────────────────────
# VOICE — transcribe audio
# ──────────────────────────────────────────────

@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """Transcribe an uploaded audio file using Whisper."""
    audio_bytes = await audio.read()
    result = transcribe_audio(audio_bytes, filename=audio.filename)
    return result


# ──────────────────────────────────────────────
# FULL COMPLAINT SUBMISSION PIPELINE
# ──────────────────────────────────────────────

@app.post("/submit/voice")
async def submit_voice_complaint(
    audio: UploadFile = File(...),
    citizen_name: Optional[str] = Form(None),
    contact: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Submit a voice complaint — runs full pipeline: Whisper → translate → classify → report."""
    # Step 1: Transcribe
    audio_bytes = await audio.read()
    transcription = transcribe_audio(audio_bytes, filename=audio.filename)
    original_text = transcription["text"]
    detected_lang = transcription["language"]

    return await _process_complaint(
        original_text=original_text,
        detected_lang=detected_lang,
        input_type="voice",
        citizen_name=citizen_name,
        contact=contact,
        location=location,
        db=db,
    )


class TextComplaintRequest(BaseModel):
    text: str
    language: Optional[str] = "auto"
    citizen_name: Optional[str] = None
    contact: Optional[str] = None
    location: Optional[str] = None


@app.post("/submit/text")
async def submit_text_complaint(
    req: TextComplaintRequest,
    db: Session = Depends(get_db),
):
    """Submit a text complaint in any language."""
    lang = req.language if req.language != "auto" else detect_language(req.text)
    return await _process_complaint(
        original_text=req.text,
        detected_lang=lang,
        input_type="text",
        citizen_name=req.citizen_name,
        contact=req.contact,
        location=req.location,
        db=db,
    )


@app.post("/submit/file")
async def submit_file_complaint(
    file: UploadFile = File(...),
    citizen_name: Optional[str] = Form(None),
    contact: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Submit a complaint via uploaded text/PDF file."""
    content = await file.read()

    # Extract text based on file type
    if file.filename.endswith(".pdf"):
        try:
            import io
            import pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                original_text = "\n".join(p.extract_text() or "" for p in pdf.pages).strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not read PDF: {e}")
    else:
        try:
            original_text = content.decode("utf-8").strip()
        except Exception:
            raise HTTPException(status_code=400, detail="Could not decode file as text.")

    if not original_text:
        raise HTTPException(status_code=400, detail="Extracted text is empty.")

    lang = detect_language(original_text)
    return await _process_complaint(
        original_text=original_text,
        detected_lang=lang,
        input_type="file",
        citizen_name=citizen_name,
        contact=contact,
        location=location,
        db=db,
    )


# ──────────────────────────────────────────────
# SHARED PIPELINE
# ──────────────────────────────────────────────

async def _process_complaint(
    original_text: str,
    detected_lang: str,
    input_type: str,
    citizen_name: Optional[str],
    contact: Optional[str],
    location: Optional[str],
    db: Session,
) -> dict:
    complaint_id = f"CMP-{uuid.uuid4().hex[:8].upper()}"

    # Step 2: Translate to English (if not already English)
    if detected_lang not in ("en", "english"):
        translation = translate_to_english(original_text, detected_lang)
        translated_text = translation["translated_text"]
    else:
        translated_text = original_text

    # Step 3: Classify (TensorFlow)
    classification = classify_complaint(translated_text)

    # Step 4: Assess priority (Ollama)
    priority = assess_priority(translated_text)

    # Step 5: Generate summary (Ollama)
    summary = generate_summary(
        translated_text,
        classification["category"],
        classification["department"],
    )

    # Step 6: Persist to DB
    complaint = Complaint(
        complaint_id=complaint_id,
        original_text=original_text,
        original_language=detected_lang,
        input_type=input_type,
        translated_text=translated_text,
        summary=summary,
        category=classification["category"],
        sub_category="",
        department=classification["department"],
        priority=priority,
        confidence=classification["confidence"],
        citizen_name=citizen_name,
        contact=contact,
        location=location,
        status="submitted",
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    # Step 7: Generate PDF report
    report_data = {
        "complaint_id": complaint_id,
        "original_text": original_text,
        "translated_text": translated_text,
        "summary": summary,
        "category": classification["category"],
        "department": classification["department"],
        "priority": priority,
        "confidence": classification["confidence"],
        "original_language": detected_lang,
        "input_type": input_type,
        "status": "submitted",
        "citizen_name": citizen_name,
        "contact": contact,
        "location": location,
    }
    report_path = generate_complaint_report(report_data)
    complaint.report_path = report_path
    db.commit()

    return {
        "complaint_id": complaint_id,
        "status": "submitted",
        "category": classification["category"],
        "department": classification["department"],
        "priority": priority,
        "confidence": classification["confidence"],
        "original_language": detected_lang,
        "translated_text": translated_text,
        "summary": summary,
        "report_path": report_path,
        "message": f"Complaint {complaint_id} submitted and routed to {classification['department']}.",
    }


# ──────────────────────────────────────────────
# ADMIN / QUERY ROUTES
# ──────────────────────────────────────────────

@app.get("/complaints")
def list_complaints(
    status: Optional[str] = None,
    department: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(Complaint)
    if status:
        q = q.filter(Complaint.status == status)
    if department:
        q = q.filter(Complaint.department == department)
    if priority:
        q = q.filter(Complaint.priority == priority)
    complaints = q.order_by(Complaint.created_at.desc()).limit(limit).all()

    return [
        {
            "complaint_id": c.complaint_id,
            "category": c.category,
            "department": c.department,
            "priority": c.priority,
            "status": c.status,
            "original_language": c.original_language,
            "summary": c.summary,
            "created_at": c.created_at.isoformat(),
        }
        for c in complaints
    ]


@app.get("/complaints/{complaint_id}")
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    c = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    return {k: v for k, v in c.__dict__.items() if not k.startswith("_")}


@app.patch("/complaints/{complaint_id}/status")
def update_status(complaint_id: str, status: str, db: Session = Depends(get_db)):
    c = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    valid = {"submitted", "in_review", "resolved"}
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Status must be one of {valid}")
    c.status = status
    c.updated_at = datetime.utcnow()
    db.commit()
    return {"complaint_id": complaint_id, "status": status}


@app.get("/complaints/{complaint_id}/report")
def download_report(complaint_id: str, db: Session = Depends(get_db)):
    c = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not c or not c.report_path:
        raise HTTPException(status_code=404, detail="Report not found.")
    return FileResponse(c.report_path, media_type="application/pdf",
                        filename=f"complaint_{complaint_id}.pdf")


@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func
    total = db.query(Complaint).count()
    by_status = db.query(Complaint.status, func.count()).group_by(Complaint.status).all()
    by_dept = db.query(Complaint.department, func.count()).group_by(Complaint.department).all()
    by_priority = db.query(Complaint.priority, func.count()).group_by(Complaint.priority).all()
    by_lang = db.query(Complaint.original_language, func.count()).group_by(Complaint.original_language).all()
    return {
        "total": total,
        "by_status": dict(by_status),
        "by_department": dict(by_dept),
        "by_priority": dict(by_priority),
        "by_language": dict(by_lang),
    }
