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
    def esc(s):
        if not s: return ""
        return str(s).replace("'", "''")

    # Use raw SQL to fetch task data to avoid FieldNotFoundError from outdated client
    task_records = await db.query_raw(
        'SELECT * FROM "tasks" WHERE id = $1', task_id
    )
    if not task_records:
        task_records = await db.query_raw(
            'SELECT * FROM tasks WHERE id = $1', task_id
        )

    if not task_records:
        return {"success": False, "error": "Task not found"}
    
    task_data = task_records[0]
    
    # Fetch meeting data
    meeting_records = await db.query_raw(
        'SELECT * FROM "meetings" WHERE id = $1', task_data.get("meeting_id")
    )
    meeting_data = meeting_records[0] if meeting_records else {}
    
    # Fetch employee data
    employee_data = {}
    if task_data.get("employee_id"):
        emp_records = await db.query_raw(
            'SELECT * FROM "employees" WHERE id = $1', task_data.get("employee_id")
        )
        employee_data = emp_records[0] if emp_records else {}

    results = {
        "task_id": str(task_id),
        "task_title": task_data.get("title"),
        "assignee_name": task_data.get("assignee_name") or (employee_data.get("name") if employee_data else None),
        "github": None,
        "jira": None,
    }

    # --- FETCH DYNAMIC CREDENTIALS ---
    emp_id = employee_data.get("emp_id") if employee_data else "EMP001"
    creds = settings.get_employee_credentials(emp_id)

    meeting_title = meeting_data.get("title", "Meeting")
    priority_str = task_data.get("priority", "medium")
    
    github_user = employee_data.get("github_username")
    jira_id = employee_data.get("jira_account_id")
    assignee_name = task_data.get("assignee_name") or (employee_data.get("name") if employee_data else None)

    if push_github:
        github_result = await create_github_issue(
            task_title=task_data.get("title"),
            task_description=task_data.get("description") or "",
            source_quote=task_data.get("source_quote") or "",
            meeting_title=meeting_title,
            priority=priority_str,
            github_username=github_user,
            assignee_name=assignee_name,
            repo_owner=creds["gh_owner"],
            repo_name=creds["gh_repo"],
            token=creds["gh_token"],
        )
        if github_result["success"]:
            # Trigger Action
            await trigger_github_action(
                repo_owner=creds["gh_owner"],
                repo_name=creds["gh_repo"],
                token=creds["gh_token"]
            )
            # Use formatted string to bypass $ parameter bug on this environment
            await db.execute_raw(
                f"UPDATE \"tasks\" SET github_issue_url = '{esc(github_result['issue_url'])}', status = 'approved' WHERE id = '{esc(task_id)}'"
            )
        results["github"] = github_result

    if push_jira:
        real_jira_id = jira_id
        if jira_id and "@" in jira_id or (jira_id and len(jira_id) < 20):
            from .jira_service import get_jira_account_id
            resolved_id = await get_jira_account_id(
                email=employee_data.get("email") or jira_id,
                jira_domain=creds["jira_domain"],
                jira_email=creds["jira_email"],
                jira_token=creds["jira_token"]
            )
            if resolved_id:
                real_jira_id = resolved_id
        
        jira_result = await create_jira_ticket(
            task_title=task_data.get("title"),
            task_description=task_data.get("description") or "",
            source_quote=task_data.get("source_quote") or "",
            meeting_title=meeting_title,
            priority=priority_str,
            jira_account_id=real_jira_id,
            assignee_name=assignee_name,
            jira_domain=creds["jira_domain"],
            jira_email=creds["jira_email"],
            jira_token=creds["jira_token"],
            jira_project_key=creds["jira_project"],
        )
        if jira_result["success"]:
            # Use formatted string to bypass $ parameter bug on this environment
            await db.execute_raw(
                f"UPDATE \"tasks\" SET jira_issue_key = '{esc(jira_result['issue_key'])}', status = 'approved' WHERE id = '{esc(task_id)}'"
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
            # Use formatted string to bypass $ parameter bug on this environment
            await db.execute_raw(
                f"UPDATE \"tasks\" SET status = '{esc(new_status)}' WHERE id = '{esc(task_id)}'"
            )
            sync_results.append({"task_id": task_id, "status": new_status})

    # Recalculate and update meeting health score after sync
    if sync_results:
        # Use query_raw for health calculation
        all_tasks = await db.query_raw(
            'SELECT status FROM "tasks" WHERE meeting_id = $1', meeting_id
        )
        if all_tasks:
            approved_completed = len([t for t in all_tasks if t.get("status") in ["approved", "completed"]])
            new_health = round((approved_completed / len(all_tasks)) * 100)
            await db.execute_raw(
                f"UPDATE \"meetings\" SET health_score = {float(new_health)} WHERE id = '{esc(meeting_id)}'"
            )

    return sync_results

async def push_all_approved_tasks(meeting_id: str, db: Prisma) -> list:
    # Use query_raw to fetch tasks
    tasks = await db.query_raw(
        'SELECT id FROM "tasks" WHERE meeting_id = $1 AND status IN (\'approved\', \'pending_review\')',
        meeting_id
    )

    results = []
    for task_data in tasks:
        result = await push_task_to_integrations(
            task_id=task_data["id"],
            db=db,
            push_github=True,
            push_jira=True,
        )
        results.append(result)

    return results
