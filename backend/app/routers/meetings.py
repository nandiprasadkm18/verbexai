from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from typing import List, Optional
import uuid
import os
import aiofiles
import asyncio
import io
import json
from datetime import datetime
from pypdf import PdfReader
from docx import Document
from prisma import Prisma

from ..database import get_db
from ..schemas.meeting import MeetingCreate, Meeting as MeetingSchema, MeetingWithResults
from ..schemas.task import Task as TaskSchema
from ..schemas.decision import Decision as DecisionSchema
from ..services.gemini_service import process_transcript_with_gemini
from ..services.transcription import transcribe_audio_file, clean_transcript
from ..services.audio_service import save_audio_file
from ..services.integration_service import push_task_to_integrations, push_all_approved_tasks
from pydantic import BaseModel, Field
from typing import List, Optional
from ..config import settings

router = APIRouter(tags=["meetings"])

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    assignee_name: Optional[str] = None
    owner_emp_id: Optional[str] = None
    owner_dept: Optional[str] = None
    status: Optional[str] = None
    confidence_score: Optional[float] = None
    employee_id: Optional[str] = None

class DecisionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

async def extract_text_from_file(file: UploadFile) -> str:
    try:
        content = await file.read()
        filename = file.filename.lower()
        
        if filename.endswith(".pdf"):
            pdf = PdfReader(io.BytesIO(content))
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        elif filename.endswith(".docx"):
            doc = Document(io.BytesIO(content))
            return "\n".join([para.text for para in doc.paragraphs if para.text])
        else:
            # Default to text
            try:
                return content.decode("utf-8")
            except:
                return content.decode("latin-1")
    except Exception as e:
        print(f"Error extracting text from {file.filename}: {e}")
        return f"[Error extracting text from file: {str(e)}]"

async def save_tasks_and_decisions(meeting_id: str, ai_data: dict, db: Prisma):
    """
    Unified helper to save tasks and decisions from Gemini response.
    Includes employee upsert logic.
    """
    # Save Tasks
    for t in ai_data.get("tasks", []):
        try:
            confidence = float(t.get("confidence_score", 0))
        except (TypeError, ValueError):
            confidence = 0.0
            
        status = "discarded"
        if confidence >= settings.CONFIDENCE_AUTO_APPROVE:
            status = "approved"
        elif confidence >= settings.CONFIDENCE_REVIEW_THRESHOLD:
            status = "pending_review"
            
        priority = str(t.get("priority", "medium")).lower()
        if priority not in ["high", "medium", "low"]:
            priority = "medium"
            
        # Employee Extraction Logic
        employee_id_db = None
        assignee_name = t.get("assignee_name")
        owner_emp_id = t.get("owner_emp_id")
        
        if assignee_name or owner_emp_id:
            try:
                # 1. Try finding by emp_id if provided
                if owner_emp_id:
                    emp = await db.employee.find_unique(where={"emp_id": owner_emp_id})
                    if emp:
                        employee_id_db = emp.id
                
                # 2. Try finding by name if no employee_id_db yet
                if not employee_id_db and assignee_name:
                    emp = await db.employee.find_first(
                        where={"name": {"equals": assignee_name, "mode": "insensitive"}}
                    )
                    if emp:
                        employee_id_db = emp.id
                
                # 3. If still not found and we have both, upsert as new (legacy behavior)
                if not employee_id_db and owner_emp_id and assignee_name:
                    emp = await db.employee.upsert(
                        where={"emp_id": owner_emp_id},
                        data={
                            "create": {
                                "name": assignee_name,
                                "emp_id": owner_emp_id,
                                "department": t.get("owner_dept") or "Engineering"
                            },
                            "update": {
                                "name": assignee_name,
                                "department": t.get("owner_dept") or "Engineering"
                            }
                        }
                    )
                    employee_id_db = emp.id
            except Exception as emp_err:
                print(f"DEBUG: Error mapping employee: {emp_err}")

        await db.task.create(
            data={
                "meeting_id": meeting_id,
                "title": t.get("title") or "Unnamed Task",
                "description": t.get("description"),
                "priority": priority,
                "status": status,
                "confidence_score": confidence,
                "assignee_name": t.get("assignee_name"),
                "owner_emp_id": t.get("owner_emp_id"),
                "owner_dept": t.get("owner_dept"),
                "employee_id": employee_id_db,
                "source_quote": t.get("source_quote")
            }
        )
        
    # Save Decisions
    for d in ai_data.get("decisions", []):
        await db.decision.create(
            data={
                "meeting_id": meeting_id,
                "title": d.get("title") or "Unnamed Decision",
                "description": d.get("description"),
                "decided_by_name": d.get("decided_by_name"),
                "source_quote": d.get("source_quote")
            }
        )

@router.post("/meetings/create", response_model=MeetingSchema)
async def create_meeting(meeting_in: MeetingCreate, db: Prisma = Depends(get_db)):
    try:
        meeting = await db.meeting.create(
            data={
                "title": meeting_in.title,
                "host_name": meeting_in.host_name,
                "description": meeting_in.description,
                "status": "pending"
            }
        )
        return meeting
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/meetings/{meeting_id}/push-all")
async def push_all_tasks(meeting_id: str, db: Prisma = Depends(get_db)):
    """Push ALL approved tasks from a meeting at once"""
    try:
        results = await push_all_approved_tasks(meeting_id=meeting_id, db=db)
        return {
            "meeting_id": meeting_id,
            "success": True,
            "pushed": len([r for r in results if (r.get("github") and r["github"].get("success")) or (r.get("jira") and r["jira"].get("success"))]),
            "total": len(results),
            "results": results,
        }
    except Exception as e:
        print(f"PUSH ERR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/meetings/{meeting_id}/sync")
async def sync_meeting_tasks(meeting_id: str, db: Prisma = Depends(get_db)):
    """Sync real-time status from external platforms"""
    try:
        from app.services.integration_service import sync_all_task_statuses
        results = await sync_all_task_statuses(meeting_id, db)
        return {"success": True, "synced_count": len(results), "updates": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/meetings/{meeting_id}/upload-text", response_model=MeetingWithResults)
async def upload_text(meeting_id: str, file: UploadFile = File(...), db: Prisma = Depends(get_db)):
    try:
        meeting = await db.meeting.find_unique(where={"id": meeting_id})
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        content = await extract_text_from_file(file)
        
        await db.meeting.update(
            where={"id": meeting_id},
            data={
                "raw_transcript": content,
                "cleaned_transcript": clean_transcript(content),
                "input_type": "text",
                "status": "processing"
            }
        )
        
        # AI Processing with Gemini
        ai_data = await process_transcript_with_gemini(content, meeting.title, meeting.host_name)
        
        # Save Tasks & Decisions
        await save_tasks_and_decisions(meeting_id, ai_data, db)
        
        # Final update and fetch with results
        try:
            health_score = float(ai_data.get("health_score", 0))
        except (TypeError, ValueError):
            health_score = 0.0

        res = await db.meeting.update(
            where={"id": meeting_id},
            data={
                "tldr": ai_data.get("tldr") or "No summary available",
                "health_score": health_score,
                "status": "complete",
                "processed_at": datetime.now()
            },
            include={
                "tasks": True,
                "decisions": True
            }
        )
        
        meeting_dict = res.model_dump()
        meeting_dict["tasks"] = res.tasks
        meeting_dict["decisions"] = res.decisions
        meeting_dict["task_count"] = len(res.tasks) if res.tasks else 0
        meeting_dict["decision_count"] = len(res.decisions) if res.decisions else 0
        
        return meeting_dict
    except Exception as e:
        await db.meeting.update(where={"id": meeting_id}, data={"status": "failed"})
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/meetings/{meeting_id}/upload-audio", response_model=MeetingWithResults)
async def upload_audio(meeting_id: str, file: UploadFile = File(...), db: Prisma = Depends(get_db)):
    meeting = await db.meeting.find_unique(where={"id": meeting_id})
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    try:
        # Step 2 — Save file to disk with validation
        file_path = await save_audio_file(file, meeting_id)
        
        await db.meeting.update(
            where={"id": meeting_id},
            data={
                "raw_file_path": file_path,
                "input_type": "uploaded_audio",
                "status": "transcribing"
            }
        )
        
        # Step 3 — Transcribe with OpenAI Whisper
        transcript = await transcribe_audio_file(file_path)
        cleaned = clean_transcript(transcript)
        
        await db.meeting.update(
            where={"id": meeting_id},
            data={
                "raw_transcript": transcript,
                "cleaned_transcript": cleaned,
                "status": "processing"
            }
        )
        
        # Step 4 — Process with Gemini
        ai_data = await process_transcript_with_gemini(cleaned, meeting.title, meeting.host_name)
        await save_tasks_and_decisions(meeting_id, ai_data, db)
        
        try:
            health_score = float(ai_data.get("health_score", 0))
        except (TypeError, ValueError):
            health_score = 0.0

        res = await db.meeting.update(
            where={"id": meeting_id},
            data={
                "tldr": ai_data.get("tldr") or "No summary available",
                "health_score": health_score,
                "status": "complete",
                "processed_at": datetime.now()
            },
            include={
                "tasks": True,
                "decisions": True
            }
        )

        meeting_dict = res.model_dump()
        meeting_dict["tasks"] = res.tasks
        meeting_dict["decisions"] = res.decisions
        meeting_dict["task_count"] = len(res.tasks) if res.tasks else 0
        meeting_dict["decision_count"] = len(res.decisions) if res.decisions else 0
        
        return meeting_dict
    except Exception as e:
        await db.meeting.update(where={"id": meeting_id}, data={"status": "failed"})
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/meetings/{meeting_id}/process-live", response_model=MeetingWithResults)
async def process_live_transcript(
    meeting_id: str, 
    file: UploadFile = File(...), 
    live_transcript: Optional[str] = Form(None),
    db: Prisma = Depends(get_db)
):
    """
    Receives an audio file from the frontend's MediaRecorder,
    saves it, transcribes it with Whisper, and processes it with Gemini.
    """
    meeting = await db.meeting.find_unique(where={"id": meeting_id})
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    try:
        # Step 1: Save audio file
        file_path = await save_audio_file(file, meeting_id)
        
        await db.meeting.update(
            where={"id": meeting_id},
            data={
                "raw_file_path": file_path,
                "input_type": "live_audio",
                "status": "transcribing"
            }
        )
        
        # Step 2: Transcribe with Whisper
        transcript = await transcribe_audio_file(file_path)
        
        # HYBRID FALLBACK
        if not transcript.strip() or (live_transcript and len(transcript) < len(live_transcript) * 0.3):
            if live_transcript:
                print(f"DEBUG: Whisper returned minimal data ({len(transcript)} chars). Falling back to live transcript ({len(live_transcript)} chars).")
                transcript = live_transcript
            else:
                print("DEBUG: BOTH Whisper and live transcript are missing.")
        
        cleaned = clean_transcript(transcript)
        
        await db.meeting.update(
            where={"id": meeting_id},
            data={
                "raw_transcript": transcript,
                "cleaned_transcript": cleaned,
                "status": "processing"
            }
        )
        
        # Step 3: Process with Gemini (Groq Premium)
        ai_data = await process_transcript_with_gemini(cleaned, meeting.title, meeting.host_name)
        await save_tasks_and_decisions(meeting_id, ai_data, db)
        
        health_score = float(ai_data.get("health_score", 0))
        
        # Step 4: Final update and fetch with results (MATCHING upload-audio structure)
        res = await db.meeting.update(
            where={"id": meeting_id},
            data={
                "tldr": ai_data.get("tldr") or "No summary available",
                "health_score": health_score,
                "status": "complete",
                "processed_at": datetime.now()
            },
            include={
                "tasks": True,
                "decisions": True
            }
        )
        
        meeting_dict = res.model_dump()
        meeting_dict["tasks"] = res.tasks
        meeting_dict["decisions"] = res.decisions
        meeting_dict["task_count"] = len(res.tasks) if res.tasks else 0
        meeting_dict["decision_count"] = len(res.decisions) if res.decisions else 0
        
        return meeting_dict

    except Exception as e:
        print(f"AI ERR: {e}")
        await db.meeting.update(where={"id": meeting_id}, data={"status": "failed"})
        raise HTTPException(status_code=500, detail=f"Live processing failed: {str(e)}")




@router.post("/meetings/transcribe")
async def transcribe_full(file: UploadFile = File(...)):
    """
    High-accuracy final transcription using Whisper V3.
    """
    try:
        temp_id = str(uuid.uuid4())
        os.makedirs("temp", exist_ok=True)
        file_path = f"temp/full_{temp_id}.webm"
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(await file.read())
            
        from ..services.transcription import transcribe_audio_file
        transcript = await transcribe_audio_file(file_path)
        
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return {"transcript": transcript}
    except Exception as e:
        print(f"FULL TRANS ERR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/meetings/transcribe-chunk")
async def transcribe_chunk(file: UploadFile = File(...)):
    """
    Fast transcription for live chunks using Whisper.
    """
    try:
        temp_id = str(uuid.uuid4())
        os.makedirs("temp", exist_ok=True)
        file_path = f"temp/chunk_{temp_id}.webm"
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(await file.read())
            
        from ..services.transcription import transcribe_audio_file
        transcript = await transcribe_audio_file(file_path)
        
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return {"transcript": transcript}
    except Exception as e:
        print(f"CHUNK ERR: {e}")
        return {"transcript": ""}

@router.post("/meetings/{meeting_id}/tasks/{task_id}/push")
async def push_task(
    meeting_id: str,
    task_id: str,
    db: Prisma = Depends(get_db),
):
    result = await push_task_to_integrations(
        task_id=task_id,
        db=db,
        push_github=True,
        push_jira=True,
    )
    return result


@router.get("/meetings", response_model=List[MeetingWithResults])
async def list_meetings(db: Prisma = Depends(get_db)):
    meetings = await db.meeting.find_many(
        order={"created_at": "desc"},
        include={"tasks": True, "decisions": True}
    )
    results = []
    for m in meetings:
        m_dict = m.model_dump()
        m_dict["task_count"] = len(m.tasks)
        m_dict["decision_count"] = len(m.decisions)
        results.append(m_dict)
    return results

@router.get("/meetings/tasks/all", response_model=List[TaskSchema])
async def get_all_tasks(db: Prisma = Depends(get_db)):
    return await db.task.find_many(order={"created_at": "desc"})

@router.get("/meetings/decisions/all", response_model=List[DecisionSchema])
async def get_all_decisions(db: Prisma = Depends(get_db)):
    return await db.decision.find_many(order={"created_at": "desc"})

@router.get("/meetings/stats")
async def get_stats(db: Prisma = Depends(get_db)):
    total_meetings = await db.meeting.count()
    total_tasks = await db.task.count()
    total_decisions = await db.decision.count()
    stale_tasks_count = 2 # Hardcoded to match the mock data in /stale-tasks
    
    # Calculate dynamic intelligence metrics
    all_tasks = await db.task.find_many()
    precision = 94.2 # Base baseline
    if all_tasks:
        scores = [t.confidence_score for t in all_tasks if t.confidence_score is not None]
        if scores:
            precision = round((sum(scores) / len(scores)) * 100, 1)

    return {
        "meetings": {"value": total_meetings, "delta": "+12%"},
        "tasks": {"value": total_tasks, "delta": "+5%"},
        "decisions": {"value": total_decisions, "delta": "+2%"},
        "stale_tasks": {"value": stale_tasks_count, "delta": "Low"},
        "confidence": {"value": f"{precision}%", "delta": "+2.1%"},
        "intelligence": {
            "precision": f"{precision}%",
            "provider": "Groq LLaMA 3.3",
            "fallback_active": False,
            "contextual_load": f"{min(100, total_tasks * 2)}%",
            "system_health": "Optimal",
            "trend": [92.1, 91.5, 93.8, 92.4, 94.2, 93.9, 94.5] # Confidence trend
        }
    }

@router.get("/speakers")
async def get_speakers(db: Prisma = Depends(get_db)):
    # Get the official employees from the database
    employees = await db.employee.find_many()
    
    # Get all tasks for correlation
    tasks = await db.task.find_many()
    
    results = []
    colors = ["bg-emerald-500", "bg-accent-blue", "bg-purple-500", "bg-rose-500", "bg-amber-500"]
    
    for i, emp in enumerate(employees):
        # Count tasks owned by this specific employee
        owned_tasks = [t for t in tasks if t.employee_id == emp.id or (t.assignee_name and emp.name.lower() in t.assignee_name.lower())]
        task_count = len(owned_tasks)
        
        # Get a quote if they have one, otherwise use a placeholder
        quote = ""
        for t in owned_tasks:
            if t.source_quote:
                quote = t.source_quote
                break
                
        initials = "".join([n[0] for n in emp.name.split()]).upper()[:2]
        
        results.append({
            "id": emp.id, 
            "name": emp.name, 
            "role": emp.role or "Team Member", 
            "initials": initials,
            "color": colors[i % len(colors)], 
            "tasks_owned": task_count,
            "decisions_triggered": (task_count // 2), 
            "words_spoken": task_count * 150 + 500, # Mock metric based on activity
            "notable_quote": quote or f"Active contributor to Team {emp.department or 'Engineering'}."
        })
        
    return results

@router.get("/stale-tasks")
async def get_stale_tasks(db: Prisma = Depends(get_db)):
    # Hardcoded, high-quality mock data for the Stale Tasks feature demonstration
    return [
        {
            "id": "stale-001",
            "title": "Finalize Payment Gateway API Contracts",
            "description": "The frontend team is blocked waiting for the final Swagger definitions for the Stripe V2 integration. This was assigned last sprint but hasn't moved.",
            "owner_dept": "Backend Eng",
            "assignee_name": "Suman S.",
            "assignee_initials": "SS",
            "assignee_color": "bg-accent-blue",
            "priority": "critical",
            "status": "stale",
            "days_overdue": 14,
            "mentioned_in_meeting_id": "SYNC-492",
            "created_at": "2026-03-01T10:00:00Z"
        },
        {
            "id": "stale-002",
            "title": "Provide Figma Handoff for Settings Panel",
            "description": "Engineering cannot begin building the new user settings panel until Design provides the final interactive prototypes and spacing tokens.",
            "owner_dept": "Design",
            "assignee_name": "Suman S.",
            "assignee_initials": "SS",
            "assignee_color": "bg-emerald-500",
            "priority": "high",
            "status": "stale",
            "days_overdue": 8,
            "mentioned_in_meeting_id": "SYNC-501",
            "created_at": "2026-03-06T14:30:00Z"
        }
    ]

@router.get("/meetings/{meeting_id}")
async def get_meeting(meeting_id: str, db: Prisma = Depends(get_db)):
    meeting = await db.meeting.find_unique(where={"id": meeting_id}, include={"tasks": True, "decisions": True})
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting

@router.delete("/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str, db: Prisma = Depends(get_db)):
    meeting = await db.meeting.find_unique(where={"id": meeting_id})
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # 1. Cleanup physical file if exists
    if meeting.raw_file_path and os.path.exists(meeting.raw_file_path):
        try:
            os.remove(meeting.raw_file_path)
        except Exception as e:
            print(f"DEBUG: Error removing file {meeting.raw_file_path}: {e}")

    # 2. Delete related results (Tasks and Decisions)
    # We do this explicitly since the schema doesn't have Cascade set up
    await db.task.delete_many(where={"meeting_id": meeting_id})
    await db.decision.delete_many(where={"meeting_id": meeting_id})
    
    # 3. Delete Meeting
    await db.meeting.delete(where={"id": meeting_id})
    return {"status": "success", "message": "Meeting and intelligence data purged"}

@router.patch("/tasks/{task_id}", response_model=TaskSchema)
async def update_task(task_id: str, data: TaskUpdate, db: Prisma = Depends(get_db)):
    # Use exclude_unset=True to only update fields actually provided in the request
    update_data = data.model_dump(exclude_unset=True)
    try:
        updated_task = await db.task.update(where={"id": task_id}, data=update_data)
        
        # Recalculate health score for the meeting to maintain consistency across the site
        meeting_id = updated_task.meeting_id
        all_tasks = await db.task.find_many(where={"meeting_id": meeting_id})
        
        if all_tasks:
            approved_count = len([t for t in all_tasks if t.status in ["approved", "completed"]])
            new_health = round((approved_count / len(all_tasks)) * 100)
            
            await db.meeting.update(
                where={"id": meeting_id},
                data={"health_score": float(new_health)}
            )
            
        # Push status to GitHub if connected
        if data.status and updated_task.github_issue_url:
            try:
                issue_num = int(updated_task.github_issue_url.split("/")[-1])
                emp_id = updated_task.owner_emp_id or "EMP001"
                from ..config import settings
                creds = settings.get_employee_credentials(emp_id)
                from ..services.github_service import update_github_issue_state
                
                github_state = "closed" if data.status == "completed" else "open"
                await update_github_issue_state(
                    issue_number=issue_num,
                    repo_owner=creds["gh_owner"],
                    repo_name=creds["gh_repo"],
                    token=creds["gh_token"],
                    state=github_state
                )
            except Exception as e:
                print(f"DEBUG: Failed to push status to GitHub for task {task_id}: {e}")
                
        return updated_task
    except Exception as e:
        print(f"DEBUG: Error updating task {task_id}: {e}")
        raise HTTPException(status_code=404, detail="Task not found")

@router.patch("/decisions/{decision_id}", response_model=DecisionSchema)
async def update_decision(decision_id: str, data: DecisionUpdate, db: Prisma = Depends(get_db)):
    update_data = data.model_dump(exclude_unset=True)
    try:
        return await db.decision.update(where={"id": decision_id}, data=update_data)
    except Exception as e:
        print(f"DEBUG: Error updating decision {decision_id}: {e}")
        raise HTTPException(status_code=404, detail="Decision not found")

@router.get("/meetings/{meeting_id}/status")
async def get_status(meeting_id: str, db: Prisma = Depends(get_db)):
    meeting = await db.meeting.find_unique(where={"id": meeting_id})
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    progress = {"pending": 10, "transcribing": 40, "processing": 70, "complete": 100, "failed": 0}
    steps = {"pending": "Waiting", "transcribing": "Transcribing", "processing": "AI Extraction", "complete": "Finished", "failed": "Failed"}
    return {
        "status": meeting.status,
        "progress_percent": progress.get(meeting.status, 0),
        "current_step": steps.get(meeting.status, "Unknown")
    }
