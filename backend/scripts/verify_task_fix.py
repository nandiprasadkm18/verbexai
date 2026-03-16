import asyncio
from prisma import Prisma

async def verify():
    db = Prisma()
    await db.connect()
    
    # Get a task
    task = await db.task.find_first()
    if not task:
        print("No tasks found to test.")
        await db.disconnect()
        return
    
    print(f"Testing status update for task: {task.id}")
    try:
        updated = await db.task.update(
            where={"id": task.id},
            data={"status": "completed"}
        )
        print(f"✅ Success! New status: {updated.status}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(verify())
