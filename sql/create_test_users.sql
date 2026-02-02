-- Insert Ira (English user) and Marek (Czech user)
-- Passwords: ira / marek
-- Run these commands in Supabase SQL Editor after running the migration

-- First, create temporary plain text passwords (will be hashed by backend)
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
  'ira_temp_plain_text',
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
  'marek_temp_plain_text',
  'sales',
  true,
  '+420987654321',
  'cs',
  NOW(),
  NOW(),
  NOW()
);

-- Then update with proper password hashes:
UPDATE sellers SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkOY1Lq3vJHtq5LxNvXBLkQ2XK8wJwz5e' WHERE email = 'ira@example.com';
UPDATE sellers SET password_hash = '$2b$12$rQG8vLq1vG1xW5KqG8K.uKqO3sNvYvW8vKqG8K.uKqO3sNvYvW8vK' WHERE email = 'marek@example.com';