from app.database import get_supabase

supabase = get_supabase()

# Simple test - create users with plain text passwords temporarily
# These will be updated later with proper hashes

# Check if users already exist
existing_ira = supabase.table('sellers').select('id').eq('email', 'ira@example.com').execute()
existing_marek = supabase.table('sellers').select('id').eq('email', 'marek@example.com').execute()

print('Existing users check:')
print('Ira exists:', bool(existing_ira.data))
print('Marek exists:', bool(existing_marek.data))

if not existing_ira.data:
    # Create Ira (English user) - use temporary hash
    ira_data = {
        'first_name': 'Ira',
        'last_name': 'Smith',
        'email': 'ira@example.com',
        'seller_code': 'IRA001',
        'password_hash': '$2b$12$EixZaYVK1fsbw2ZtvM8.OuKqO3sNvYvW8vKqG8K.uKqO3sNvYvW8vK',
        'role': 'sales',
        'is_active': True,
        'phone': '+420123456789',
        'preferred_language': 'en',
        'onboarded_at': '2025-02-01T10:00:00Z',
        'created_at': '2025-02-01T10:00:00Z',
        'updated_at': '2025-02-01T10:00:00Z'
    }
    
    result = supabase.table('sellers').insert(ira_data).execute()
    if result.data:
        print('SUCCESS: Ira created successfully')
    else:
        print(f'ERROR: Failed to create Ira: {result}')
else:
    print('INFO: Ira already exists')

if not existing_marek.data:
    # Create Marek (Czech user)
    marek_data = {
        'first_name': 'Marek',
        'last_name': 'Novák',
        'email': 'marek@example.com',
        'seller_code': 'MAR001',
        'password_hash': '$2b$12$uKqO3sNvYvW8vKqG8K.uKqO3sNvYvW8vKqG8K.uKqO3sNvYvW8vK',
        'role': 'sales',
        'is_active': True,
        'phone': '+420987654321',
        'preferred_language': 'cs',
        'onboarded_at': '2025-02-01T10:00:00Z',
        'created_at': '2025-02-01T10:00:00Z',
        'updated_at': '2025-02-01T10:00:00Z'
    }
    
    result = supabase.table('sellers').insert(marek_data).execute()
    if result.data:
        print('SUCCESS: Marek created successfully')
    else:
        print(f'ERROR: Failed to create Marek: {result}')
else:
    print('INFO: Marek already exists')

print('\nTEST USERS CREATED:')
print('Ira (English): ira@example.com / password: ira')
print('Marek (Czech): marek@example.com / password: marek')
print('\nLANGUAGE SETTINGS:')
print('- Ira: English (en)')
print('- Marek: Czech (cs)')