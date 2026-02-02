"""
Simple script to create test users using direct database insertion
Ira (English) - password: "ira"
Marek (Czech) - password: "marek"
"""

import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the hashing function directly
from app.dependencies import get_password_hash

def create_test_users():
    """Create test users with proper password hashes"""
    
    # Generate password hashes
    ira_password_hash = get_password_hash("ira")
    marek_password_hash = get_password_hash("marek")
    
    print("📋 Password hashes generated:")
    print(f"Ira: {ira_password_hash}")
    print(f"Marek: {marek_password_hash}")
    
    # SQL INSERT statements
    sql_statements = f"""
-- Insert Ira (English user)
INSERT INTO sellers (
  id,
  first_name,
  last_name,
  email,
  password_hash,
  role,
  is_active,
  phone,
  preferred_language,
  onboarded_at,
  created_at,
  updated_at
) VALUES
(
  gen_random_uuid(),
  'Ira',
  'Smith',
  'ira@example.com',
  '{ira_password_hash}',
  'sales',
  true,
  '+420123456789',
  'en',
  NOW(),
  NOW(),
  NOW()
);

-- Insert Marek (Czech user)
INSERT INTO sellers (
  id,
  first_name,
  last_name,
  email,
  password_hash,
  role,
  is_active,
  phone,
  preferred_language,
  onboarded_at,
  created_at,
  updated_at
) VALUES
(
  gen_random_uuid(),
  'Marek',
  'Novák',
  'marek@example.com',
  '{marek_password_hash}',
  'sales',
  true,
  '+420987654321',
  'cs',
  NOW(),
  NOW(),
  NOW()
);
"""
    
    # Write to SQL file
    with open('sql/seed_test_users_with_hashes.sql', 'w') as f:
        f.write(sql_statements)
    
    print("✅ SQL file generated: sql/seed_test_users_with_hashes.sql")
    print("\n📋 Test Users to Create:")
    print("🇬🇧 Ira (English): ira@example.com / password: ira")
    print("🇨🇿 Marek (Czech): marek@example.com / password: marek")
    print("\n🌐 Language Settings:")
    print("- Ira: English (en)")
    print("- Marek: Czech (cs)")
    print("\n🔧 Run the SQL in Supabase Dashboard to create the users.")

if __name__ == "__main__":
    create_test_users()