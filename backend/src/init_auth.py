"""
Script to initialize authentication tables and seed default user
Run this script to set up authentication in Supabase
"""
import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from sqlalchemy import create_engine, text
from passlib.context import CryptContext

# Load environment
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/qrms")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def init_users_table():
    """Create users table and seed default user"""
    engine = create_engine(DATABASE_URL)
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        hashed_password VARCHAR(255) NOT NULL,
        email VARCHAR(100) UNIQUE,
        is_active BOOLEAN DEFAULT TRUE,
        is_admin BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        last_login TIMESTAMPTZ
    );
    
    CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);
    CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
    """
    
    with engine.connect() as conn:
        # Create table
        conn.execute(text(create_table_sql))
        conn.commit()
        print("✅ Users table created/verified")
        
        # Check if default user exists
        result = conn.execute(
            text("SELECT id FROM users WHERE username = 'qrms'")
        ).fetchone()
        
        if not result:
            # Create default user
            hashed_password = get_password_hash("qrms")
            conn.execute(
                text("""
                    INSERT INTO users (username, hashed_password, email, is_active, is_admin)
                    VALUES (:username, :password, :email, :is_active, :is_admin)
                """),
                {
                    "username": "qrms",
                    "password": hashed_password,
                    "email": "admin@qrms.local",
                    "is_active": True,
                    "is_admin": True
                }
            )
            conn.commit()
            print("✅ Default user 'qrms' created (password: qrms)")
        else:
            print("ℹ️ Default user 'qrms' already exists")


if __name__ == "__main__":
    print("Initializing authentication tables...")
    print(f"Database: {DATABASE_URL[:50]}...")
    init_users_table()
    print("\n🎉 Authentication setup complete!")
