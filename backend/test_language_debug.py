#!/usr/bin/env python3
"""
Test script to debug the preferred language issue.
Run this to test the full flow from API to database.
"""

import asyncio
import json
from app.database import get_supabase
from app.schemas.auth import UserUpdate


async def test_language_update():
    print("=== Testing Preferred Language Update ===")

    # Test 1: Check current database state
    print("\n1. Checking current database state...")
    s = get_supabase()

    # Check Ira's current language
    result = (
        s.table("sellers")
        .select("email, preferred_language")
        .eq("email", "ira@example.com")
        .execute()
    )
    print(f"Ira's current data: {result.data}")

    # Test 2: Direct database update
    print("\n2. Testing direct database update...")
    update_result = (
        s.table("sellers")
        .update({"preferred_language": "en"})
        .eq("email", "ira@example.com")
        .execute()
    )
    print(f"Direct update result: {update_result.data}")

    # Test 3: Verify update
    verify_result = (
        s.table("sellers")
        .select("email, preferred_language")
        .eq("email", "ira@example.com")
        .execute()
    )
    print(f"After update: {verify_result.data}")

    # Test 4: Test UserUpdate schema
    print("\n3. Testing UserUpdate schema...")
    user_update = UserUpdate(preferred_language="cs")
    print(f"UserUpdate schema: {user_update.model_dump()}")

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_language_update())
