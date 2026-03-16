import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    url = os.getenv('DATABASE_URL')
    if '?' in url:
        url = url.split('?')[0]
    print(f"Connecting to: {url}")
    conn = await asyncpg.connect(url)
    try:
        # Check tables
        tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        print(f"Tables: {[t['table_name'] for t in tables]}")
        
        # Check columns of tasks
        cols = await conn.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tasks'")
        print("Task Columns:")
        for c in cols:
            print(f"  {c['column_name']}: {c['data_type']}")

        # Check columns of meetings
        m_cols = await conn.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'meetings'")
        print("\nMeeting Columns:")
        for c in m_cols:
            print(f"  {c['column_name']}: {c['data_type']}")
            
        # Get latest tasks
        rows = await conn.fetch("SELECT id, title, status, github_issue_url, jira_issue_key FROM tasks ORDER BY created_at DESC LIMIT 5")
        print("\nLatest Tasks:")
        for r in rows:
            print(f"  ID: {r['id']}, Title: {r['title']}, Status: {r['status']}, GH: {r['github_issue_url']}, Jira: {r['jira_issue_key']}")
            
        # Check for approved tasks
        approved = await conn.fetch("SELECT count(*) FROM tasks WHERE status = 'approved'")
        print(f"\nTotal Approved Tasks: {approved[0]['count']}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run())
