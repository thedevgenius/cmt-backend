import asyncio
from sqlalchemy.exc import IntegrityError

# Import your existing app setup
from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.jwt import get_password_hash
from app.core.utils import format_phone

async def create_super_admin():
    print("\n" + "="*40)
    print("🛡️  Comynity Super Admin Setup 🛡️")
    print("="*40 + "\n")

    # 1. Gather input from the terminal
    phone = input("Enter admin phone (e.g., +919876543210): ").strip()
    email = input("Enter admin email: ").strip()
    name = input("Enter admin full name: ").strip()
    password = input("Enter a secure password: ").strip()

    # 2. Hash the password using the utility we built earlier
    hashed_pw = get_password_hash(password)

    # 3. Create the User object with elevated privileges
    admin_user = User(
        phone=format_phone(phone, "IN"),
        email=email,
        full_name=name,
        password=hashed_pw,
        role=UserRole.ADMIN,
        is_verified=True, # Bypass the OTP requirement for the initial setup
        is_active=True
    )

    # 4. Insert into PostgreSQL
    async with AsyncSessionLocal() as session:
        try:
            session.add(admin_user)
            await session.commit()
            print("\n✅ Success! Super Admin created.")
            print(f"You can now log in at /api/auth/staff/login with {email}")
        except IntegrityError:
            # Catch duplicates if you run the script twice
            await session.rollback()
            print("\n❌ Error: A user with that email or phone number already exists.")
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Unexpected Error: {e}")

if __name__ == "__main__":
    # Because we use asyncpg, we must run this inside an asyncio event loop
    asyncio.run(create_super_admin())