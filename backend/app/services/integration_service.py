from prisma import Prisma
from .github_service import create_github_issue, check_duplicate_issue, get_github_issue_status, trigger_github_action
from .jira_service import create_jira_ticket, get_jira_ticket_status
from datetime import datetime
from ..config import settings

async def push_task_to_integrations(
    task_id: str,
    db: Prisma,
    push_github: bool = True,
    push_jira: bool = True,
) -> dict:
    # Fetch task with meeting and employee
    task = await db.task.find_unique(
        where={"id": task_id},
        include={"meeting": True, "employee": True}
    )
    
    if not task:
        return {"success": False, "error": "Task not found"}

    results = {
        "task_id": str(task.id),
        "task_title": task.title,
        "assignee_name": task.assignee_name,
        "github": None,
        "jira": None,
    }

    meeting_title = task.meeting.title if task.meeting else ""
    priority_str = task.priority
    
    # --- FETCH DYNAMIC CREDENTIALS ---
    emp_id = task.employee.emp_id if task.employee else "EMP001"
    creds = settings.get_employee_credentials(emp_id)

    # --- FALLBACK LOGIC ---
    # If no employee is currently linked to the task, try to find the "Master Employee"
    target_employee = task.employee
    if not target_employee:
        # Use first employee just to get credentials (API Tokens)
        employees = await db.query_raw(
            "SELECT * FROM employees WHERE github_username IS NOT NULL OR jira_account_id IS NOT NULL LIMIT 1"
        )
        if employees:
            emp_data = employees[0]
            # DO NOT overwrite task's employee_id in DB!
            # DO NOT use their github_user or jira_id for assignment!
            github_user = None
            jira_id = None
        else:
            github_user = None
            jira_id = None
    else:
        # Fetch employee details via raw SQL to ensure we get all columns
        emp_records = await db.query_raw(
            "SELECT * FROM employees WHERE id = $1",
            target_employee.id
        )
        if emp_records:
            emp_data = emp_records[0]
            github_user = emp_data.get("github_username")
            jira_id = emp_data.get("jira_account_id")
        else:
            github_user = None
            jira_id = None

    if push_github:
        # Removed the aggressive check_duplicate_issue logic that blocked similar task titles.
        github_result = await create_github_issue(
            task_title=task.title,
            task_description=task.description or "",
            source_quote=task.source_quote or "",
            meeting_title=meeting_title,
            priority=priority_str,
            github_username=github_user,
            assignee_name=task.assignee_name,
            repo_owner=creds["gh_owner"],
            repo_name=creds["gh_repo"],
            token=creds["gh_token"],
        )
        if github_result["success"]:
            # trigger action
            await trigger_github_action(
                repo_owner=creds["gh_owner"],
                repo_name=creds["gh_repo"],
                token=creds["gh_token"]
            )
            await db.task.update(
                where={"id": task_id},
                data={
                    "github_issue_url": github_result["issue_url"], 
                    "status": "approved"
                }
            )
        results["github"] = github_result

    if push_jira:
        # Resolve Jira Account ID if needed
        real_jira_id = jira_id
        if jira_id and "@" in jira_id or (jira_id and len(jira_id) < 20): # Not a UUID
            from .jira_service import get_jira_account_id
            resolved_id = await get_jira_account_id(
                email=emp_data.get("email") or jira_id,
                jira_domain=creds["jira_domain"],
                jira_email=creds["jira_email"],
                jira_token=creds["jira_token"]
            )
            if resolved_id:
                real_jira_id = resolved_id
        
        jira_result = await create_jira_ticket(
            task_title=task.title,
            task_description=task.description or "",
            source_quote=task.source_quote or "",
            meeting_title=meeting_title,
            priority=priority_str,
            jira_account_id=real_jira_id,
            assignee_name=task.assignee_name,
            jira_domain=creds["jira_domain"],
            jira_email=creds["jira_email"],
            jira_token=creds["jira_token"],
            jira_project_key=creds["jira_project"],
        )
        if jira_result["success"]:
            await db.task.update(
                where={"id": task_id},
                data={
                    "jira_issue_key": jira_result["issue_key"], 
                    "status": "approved"
                }
            )
        results["jira"] = jira_result

    return results

async def sync_all_task_statuses(meeting_id: str, db: Prisma):
    """Fetch real-time status from GitHub/Jira and update local Task records"""
    # Use query_raw to fetch columns that might not be in the client model
    tasks = await db.query_raw(
        "SELECT * FROM tasks WHERE meeting_id = $1 AND (github_issue_url IS NOT NULL OR jira_issue_key IS NOT NULL)",
        meeting_id
    )

    sync_results = []
    for task_data in tasks:
        task_id = task_data["id"]
        github_issue_url = task_data.get("github_issue_url")
        jira_issue_key = task_data.get("jira_issue_key")
        emp_id = task_data.get("owner_emp_id") or "EMP001"
        
        # Fetch credentials for this specific employee
        creds = settings.get_employee_credentials(emp_id)
        
        new_status = None
        
        # 1. Sync GitHub Status
        if github_issue_url:
            try:
                issue_num = int(github_issue_url.split("/")[-1])
                github_data = await get_github_issue_status(
                    issue_number=issue_num,
                    repo_owner=creds["gh_owner"],
                    repo_name=creds["gh_repo"],
                    token=creds["gh_token"]
                )
                github_state = github_data.get("state") if github_data else None
                
                if github_state == "closed":
                    new_status = "completed"
                elif github_state == "in_progress":
                    new_status = "in_progress"
            except Exception as e:
                print(f"GH SYNC ERR for {task_id}: {e}")

        # 2. Sync Jira Status
        if jira_issue_key:
            try:
                jira_status = await get_jira_ticket_status(
                    issue_key=jira_issue_key,
                    jira_domain=creds["jira_domain"],
                    jira_email=creds["jira_email"],
                    jira_token=creds["jira_token"]
                )
                if jira_status in ["Done", "Resolved", "Closed", "Complete"]:
                    new_status = "completed"
                elif jira_status in ["In Progress", "In Dev", "In Review"]:
                    new_status = "in_progress"
                elif jira_status in ["To Do", "Backlog", "Open"]:
                    new_status = "approved"
            except Exception as e:
                print(f"JIRA SYNC ERR for {task_id}: {e}")

        if new_status and new_status != task_data.get("status"):
            await db.task.update(
                where={"id": task_id},
                data={"status": new_status}
            )
            sync_results.append({"task_id": task_id, "status": new_status})

    # Recalculate and update meeting health score after sync
    if sync_results:
        all_tasks = await db.task.find_many(where={"meeting_id": meeting_id})
        if all_tasks:
            approved_completed = len([t for t in all_tasks if t.status in ["approved", "completed"]])
            new_health = round((approved_completed / len(all_tasks)) * 100)
            await db.meeting.update(
                where={"id": meeting_id},
                data={"health_score": float(new_health)}
            )

    return sync_results
async def push_all_approved_tasks(meeting_id: str, db: Prisma) -> list:
    tasks = await db.task.find_many(
        where={
            "meeting_id": meeting_id,
            "status": {
                "in": ["approved", "pending_review"]
            }
        }
    )

    results = []
    for task in tasks:
        result = await push_task_to_integrations(
            task_id=task.id,
            db=db,
            push_github=True,
            push_jira=True,
        )
        results.append(result)

    return results
