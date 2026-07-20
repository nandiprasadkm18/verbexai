import asyncio
import os
import shutil
from prisma import Prisma

async def clear_data():
    db = Prisma()
    await db.connect()
    
    print("Purging database...")
    print("Inspecting tables...")
    try:
        tables = await db.query_raw("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        print(f"Tables found: {[t['table_name'] for t in tables]}")
    except Exception as e:
        print(f"Error inspecting tables: {e}")

    print("Purging database (Raw SQL)...")
    try:
        # We'll try common variations or use the names found above
        # Based on typical Prisma conventions for Postgres, they might be lowercase
        await db.execute_raw('TRUNCATE TABLE "employees", "tasks", "decisions", "meetings" RESTART IDENTITY CASCADE;')
        print("- Transactional data purged successfully")
    except Exception as e:
        print(f"Error purging database: {e}")
    finally:
        await db.disconnect()

    print("Clearing storage...")
    audio_dir = "storage/audio"
    if os.path.exists(audio_dir):
        for filename in os.listdir(audio_dir):
            file_path = os.path.join(audio_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                print(f"- Deleted: {filename}")
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    else:
        print("- Storage directory not found")

    print("\nData clearance complete!")

if __name__ == "__main__":
    asyncio.run(clear_data())
