import asyncio
import os
from prisma import Prisma
from dotenv import load_dotenv
from app.services.integration_service import push_all_approved_tasks

load_dotenv()

async def debug_push():
    db = Prisma()
    await db.connect()
    try:
        # Get latest meeting
        meeting = await db.meeting.find_first(order={"created_at": "desc"})
        if not meeting:
            print("No meetings found")
            return
        
        print(f"Triggering push for meeting: {meeting.title} ({meeting.id})")
        
        # Check how many approved tasks it thinks it has
        print("Checking status 'approved' in DB via Prisma...")
        tasks = await db.task.find_many(where={"meeting_id": meeting.id, "status": "approved"})
        print(f"Prisma found {len(tasks)} approved tasks for this meeting.")
        
        if not tasks:
            print("No approved tasks to push.")
            return

        results = await push_all_approved_tasks(meeting.id, db)
        print(f"\nPush Results (Total: {len(results)}):")
        for i, res in enumerate(results):
            print(f"Task {i+1}:")
            print(f"  GitHub: {res.get('github')}")
            print(f"  Jira: {res.get('jira')}")
            if res.get('error'):
                 print(f"  Overall Error: {res.get('error')}")

    except Exception as e:
        print(f"FATAL ERROR during push: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(debug_push())
