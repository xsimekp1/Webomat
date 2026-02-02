"""Get sellers from database."""
import sys
import os
from dotenv import load_dotenv

# Load .env from backend directory
load_dotenv('backend/.env')

sys.path.insert(0, 'backend')

from app.database import get_supabase

s = get_supabase()
result = s.table('sellers').select('id, email, first_name, last_name').execute()

for u in result.data:
    print(f"{u['first_name']} {u['last_name']}: {u['id']} ({u['email']})")
