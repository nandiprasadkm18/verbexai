import asyncio
import os
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def migrate_and_seed():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in .env")
        return

    # Handle SQLAlchemy/Prisma URLs that might have ?schema=...
    if "?schema=" in db_url:
        db_url = db_url.split("?")[0]

    print(f"Connecting to database...")
    try:
        conn = await asyncpg.connect(db_url)
        
        print("Migrating schema (adding missing columns)...")
        # 1. Update Employees Table
        await conn.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS email VARCHAR UNIQUE")
        await conn.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS jira_account_id VARCHAR")
        await conn.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'engineer'")
        await conn.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS avatar_url VARCHAR")
        
        # 2. Update Tasks Table
        await conn.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS github_issue_url TEXT")
        await conn.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS jira_issue_key TEXT")
        
        # 3. Handle TaskStatus enum
        new_statuses = ['in_progress', 'completed', 'failed', 'pushed']
        for status in new_statuses:
            try:
                await conn.execute(f"ALTER TYPE \"TaskStatus\" ADD VALUE '{status}'")
                print(f"Added TaskStatus '{status}'")
            except Exception as e:
                if "already exists" in str(e):
                    pass
                else:
                    print(f"Non-critical TaskStatus update error for {status}: {str(e)}")

        print("Seeding master employee...")
        github_user = os.getenv("GITHUB_REPO_OWNER")
        jira_email = os.getenv("JIRA_EMAIL")
        master_name = "Suman S."
        master_emp_id = "MASTER001"

        existing = await conn.fetchrow("SELECT id FROM employees WHERE email = $1", jira_email)
        
        if existing:
            await conn.execute(
                "UPDATE employees SET name = $1, github_username = $2, role = 'Tech Lead' WHERE id = $3",
                master_name, github_user, existing['id']
            )
        else:
            await conn.execute(
                """
                INSERT INTO employees (id, name, emp_id, email, github_username, role, department, created_at)
                VALUES (gen_random_uuid(), $1, $2, $3, $4, 'Tech Lead', 'Engineering', now())
                """,
                master_name, master_emp_id, jira_email, github_user
            )

        print("✅ Migration and seeding successful!")
        await conn.close()
    except Exception as e:
        print(f"❌ Migration error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(migrate_and_seed())
