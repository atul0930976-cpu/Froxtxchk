# reset_db.py
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Database connection
DB_HOST = os.getenv("DB_HOST", "db.mtfvvbmtkjevkdzkbhec.supabase.co")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "Atulfroxt-73")
DB_PORT = os.getenv("DB_PORT", "5432")

try:
    # Connect to database
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("✅ Connected to database")
    
    # Drop existing tables (in correct order due to foreign keys)
    print("Dropping existing tables...")
    cursor.execute("DROP TABLE IF EXISTS redeem_codes CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS user_plans CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS gate_status CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS custom_gates CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS users CASCADE;")
    
    print("✅ Tables dropped successfully")
    
    cursor.close()
    conn.close()
    print("✅ Database reset complete. Now run your bot to recreate tables.")
    
except Exception as e:
    print(f"❌ Error: {e}")
