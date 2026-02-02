-- Seed test users with different languages
-- Insert Ira (English user) and Marek (Czech user)

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
  '$2b$12$EXAMPLE_HASH_FOR_IRA_PASSWORD',
  'sales',
  true,
  '+420123456789',
  'en',
  NOW(),
  NOW(),
  NOW()
),
(
  gen_random_uuid(),
  'Marek',
  'Novák',
  'marek@example.com',
  '$2b$12$EXAMPLE_HASH_FOR_MAREK_PASSWORD',
  'sales',
  true,
  '+420987654321',
  'cs',
  NOW(),
  NOW(),
  NOW()
);

-- Note: Replace EXAMPLE_HASH values with actual password hashes using your backend's password hashing function