import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import db
from app.routers import meetings, employees
import asyncio
import logging
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse

# Setup logging for the application
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Verbex", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception caught: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "message": str(exc)},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.on_event("startup")
async def startup():
    if not db.is_connected():
        await db.connect()
    print("="*50)
    print("Verbex Backend Started (Prisma + PostgreSQL)")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    print("="*50)

@app.on_event("shutdown")
async def shutdown():
    if db.is_connected():
        await db.disconnect()

@app.get("/")
def read_root():
    return {"status": "Verbex is running", "version": "1.2.2"}

@app.post("/api/webhooks/github")
async def github_webhook(request: Request):
    try:
        payload = await request.json()
        event = request.headers.get("X-GitHub-Event")
        
        # We only care about issue events
        if event == "issues":
            action = payload.get("action")
            issue = payload.get("issue", {})
            issue_url = issue.get("html_url")
            
            if issue_url and action in ["closed", "reopened"]:
                task_status = "completed" if action == "closed" else "in_progress"
                
                # Use raw query to bypass Prisma client limitations
                tasks = await db.query_raw(
                    "SELECT id, meeting_id FROM tasks WHERE github_issue_url = $1 LIMIT 1",
                    issue_url
                )
                
                if tasks:
                    task = tasks[0]
                    task_id = task["id"]
                    meeting_id = task["meeting_id"]
                    
                    # Update task status
                    await db.execute_raw(
                        "UPDATE tasks SET status = $1 WHERE id = $2",
                        task_status, task_id
                    )
                    logger.info(f"Webhook matched! Task {task_id} status updated to {task_status}")
                    
                    # Also update health score for the meeting
                    all_tasks = await db.task.find_many(where={"meeting_id": meeting_id})
                    if all_tasks:
                        approved_count = len([t for t in all_tasks if t.status in ["approved", "completed"]])
                        new_health = round((approved_count / len(all_tasks)) * 100)
                        await db.meeting.update(
                            where={"id": meeting_id},
                            data={"health_score": float(new_health)}
                        )
                else:
                    logger.info(f"Webhook received but no matching task found for {issue_url}")
                    
        return {"status": "success", "message": "Webhook processed"}
    except Exception as e:
        logger.error(f"Error processing GitHub webhook: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

# Include the meetings router which contains stats, tasks, decisions
app.include_router(meetings.router, prefix="/api")
app.include_router(employees.router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
# TRIGGER RELOAD 8
