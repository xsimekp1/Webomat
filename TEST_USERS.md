# Test Users for Language Switching

## Created Users ✅

### 1. Ira (English User)
- **Email**: ira@example.com  
- **Password**: ira
- **Language**: English (en)
- **Expected UI**: All interface in English

### 2. Marek (Czech User)  
- **Email**: marek@example.com
- **Password**: marek  
- **Language**: Czech (cs)
- **Expected UI**: All interface in Czech

## Testing Instructions

### 1. Language Detection
1. Login as **Ira** → Should see English interface immediately
2. Login as **Marek** → Should see Czech interface immediately

### 2. Language Switching
1. Go to Profile page
2. Look for language selector in header right
3. Switch language → Should save to database and redirect to correct locale

### 3. URL Structure
- **Czech**: `/dashboard/profile` (default)
- **English**: `/en/dashboard/profile` (with /en/ prefix)

### 4. Admin Testing
1. Login as admin
2. Go to Admin section  
3. See language column in users table
4. Change user language → Should update immediately

## Notes
- Password hashes use test format (not real bcrypt)
- Language preference stored in `preferred_language` column
- Default language fallback: Czech (cs)

## Expected Behavior
✅ Language loads from user profile on login  
✅ Language switcher works in profile  
✅ URLs update correctly with locale prefix  
✅ Admin can change user language  
✅ Language persists across page refreshes