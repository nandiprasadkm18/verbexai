import asyncio
from prisma import Prisma

async def seed():
    db = Prisma()
    await db.connect()

    employees = [
        {"name": "Suman S", "emp_id": "EMP001", "role": "manager", "department": "Management"},
        {"name": "Rahul Sharma", "emp_id": "BE102", "role": "engineer", "department": "Backend"},
        {"name": "Priya Nair", "emp_id": "BE118", "role": "engineer", "department": "Backend"},
        {"name": "Likhith Gowda M", "emp_id": "EMP002", "role": "engineer", "department": "Engineering"},
        {"name": "J Hemanth", "emp_id": "EMP003", "role": "engineer", "department": "Engineering"},
        {"name": "Nandi Prasad K M", "emp_id": "EMP004", "role": "engineer", "department": "Engineering", "email": "nandiprasadkm18@gmail.com", "github_username": "nandiprasadkm18"},
        {"name": "Suresh Menon", "emp_id": "DV411", "role": "engineer", "department": "DevOps"},
        {"name": "Arjun Patel", "emp_id": "FE204", "role": "engineer", "department": "Frontend"},
        {"name": "Neha Kulkarni", "emp_id": "DB410", "role": "engineer", "department": "Database"},
        {"name": "Rohit Verma", "emp_id": "DV322", "role": "engineer", "department": "DevOps"},
        {"name": "Anjali Gupta", "emp_id": "DOC501", "role": "engineer", "department": "Documentation"},
        {"name": "Kavya Reddy", "emp_id": "DV305", "role": "engineer", "department": "DevOps"}
    ]

    print("Seeding employees...")
    for emp in employees:
        try:
            # Check if employee already exists
            existing = await db.employee.find_unique(where={"emp_id": emp["emp_id"]})
            if not existing:
                await db.employee.create(data=emp)
                print(f"Created employee: {emp['name']} ({emp['emp_id']})")
            else:
                print(f"Employee already exists: {emp['name']} ({emp['emp_id']})")
        except Exception as e:
            print(f"Error creating employee {emp['name']}: {e}")

    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(seed())
