#!/usr/bin/env python3
"""
Seed test users with different language preferences
Ira (English) - password: "ira"
Marek (Czech) - password: "marek"
"""

import asyncio
import sys
import os
from datetime import datetime

# Add backend to path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import get_supabase
from app.dependencies import get_password_hash


async def create_test_users():
    """Create test users with different language preferences"""
    supabase = get_supabase()
    
    # Check if users already exist
    existing_ira = supabase.table("sellers").select("id").eq("email", "ira@example.com").execute()
    existing_marek = supabase.table("sellers").select("id").eq("email", "marek@example.com").execute()
    
    if existing_ira.data:
        print("Ira already exists, skipping...")
    else:
        # Create Ira (English user)
        ira_data = {
            "first_name": "Ira",
            "last_name": "Smith",
            "email": "ira@example.com",
            "password_hash": get_password_hash("ira"),
            "role": "sales",
            "is_active": True,
            "phone": "+420123456789",
            "preferred_language": "en",
            "onboarded_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("sellers").insert(ira_data).execute()
        if result.data:
            print("✅ Ira (English user) created successfully")
        else:
            print(f"❌ Failed to create Ira: {result}")
    
    if existing_marek.data:
        print("Marek already exists, skipping...")
    else:
        # Create Marek (Czech user)
        marek_data = {
            "first_name": "Marek",
            "last_name": "Novák",
            "email": "marek@example.com",
            "password_hash": get_password_hash("marek"),
            "role": "sales",
            "is_active": True,
            "phone": "+420987654321",
            "preferred_language": "cs",
            "onboarded_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("sellers").insert(marek_data).execute()
        if result.data:
            print("✅ Marek (Czech user) created successfully")
        else:
            print(f"❌ Failed to create Marek: {result}")
    
    print("\n📋 Test Users Created:")
    print("🇬🇧 Ira (English): ira@example.com / password: ira")
    print("🇨🇿 Marek (Czech): marek@example.com / password: marek")
    print("\n🌐 Language Settings:")
    print("- Ira: English (en)")
    print("- Marek: Czech (cs)")


if __name__ == "__main__":
    asyncio.run(create_test_users())