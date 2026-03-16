import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    url = os.getenv('DATABASE_URL')
    if '?' in url:
        url = url.split('?')[0]
    conn = await asyncpg.connect(url)
    try:
        rows = await conn.fetch("SELECT * FROM employees")
        data = [dict(r) for r in rows]
        import json
        with open('scripts/employees_data.json', 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print("Wrote to scripts/employees_data.json")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run())
