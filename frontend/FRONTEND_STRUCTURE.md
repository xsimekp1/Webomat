# Frontend Directory Structure

## Project Structure
```
frontend/
├── app/
│   ├── [locale]/
│   │   ├── dashboard/
│   │   │   ├── admin/
│   │   │   │   ├── page.tsx          # 4 levels from app/
│   │   │   ├── feedback/
│   │   │   │   └── page.tsx      # 5 levels from app/
│   │   │   └── invoices/
│   │   │       └── page.tsx      # 5 levels from app/
│   │   ├── account/
│   │   │   └── page.tsx              # 4 levels from app/
│   │   ├── crm/
│   │   │   ├── page.tsx              # 3 levels from app/
│   │   │   └── [id]/
│   │   │       └── page.tsx          # 4 levels from app/
│   │   ├── generate-website/
│   │   │   ├── page.tsx              # 3 levels from app/
│   │   │   └── GenerateWebsiteClient.tsx
│   │   ├── invoices/
│   │   │   └── [invoiceId]/
│   │   │       └── page.tsx          # 5 levels from app/
│   │   ├── profile/
│   │   │   └── page.tsx              # 4 levels from app/
│   │   ├── web-project/
│   │   │   └── [projectId]/
│   │   │       └── page.tsx          # 5 levels from app/
│   │   ├── layout.tsx                  # 2 levels from app/
│   │   └── page.tsx                  # 2 levels from app/
│   ├── context/
│   │   ├── AuthContext.tsx
│   │   ├── LanguageContext.tsx
│   │   └── ToastContext.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   └── utils.ts
│   ├── components/
│   │   ├── LanguageSwitcher.tsx
│   │   └── ui/
│   │       ├── index.ts
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── badge.tsx
│   │       └── select.tsx
│   ├── globals.css
│   ├── layout.tsx
│   ├── middleware.ts
│   └── providers.tsx
├── components/
│   ├── LanguageSwitcher.tsx    # Legacy location, prefer app/components/
│   └── __tests__/
└── [configuration files]
```

## Import Path Guidelines

### Relative Paths from app/[locale]/dashboard/[subfolder]/page.tsx

**Important:** All imports should be relative to the `app/` directory, NOT the project root!

#### Level Calculation:
- From `app/[locale]/dashboard/page.tsx` → `app/`: 3 levels up (`../../../`)
- From `app/[locale]/dashboard/admin/page.tsx` → `app/`: 4 levels up (`../../../../`) 
- From `app/[locale]/dashboard/admin/feedback/page.tsx` → `app/`: 5 levels up (`../../../../../`)

### Common Import Patterns:

```typescript
// Correct imports from dashboard level (3 levels up)
import ApiClient from '../../../lib/api'
import { useAuth } from '../../../context/AuthContext'
import { useToast } from '../../../context/ToastContext'

// Correct imports from admin level (4 levels up) 
import ApiClient from '../../../../lib/api'
import { useAuth } from '../../../../context/AuthContext'

// Correct imports from admin subfolders (5 levels up)
import ApiClient from '../../../../../lib/api'
import { useAuth } from '../../../../../context/AuthContext'
```

### Common Mistakes to Avoid:

1. **Going outside app/ folder**: Using `../../../..` (4+ levels) from dashboard files
2. **Mixing app/ and root folders**: Importing from `frontend/lib/` instead of `app/lib/`
3. **Case sensitivity**: Vercel runs on Linux - file names are case-sensitive
4. **Missing UI components**: Always check `components/ui/index.ts` exists when importing from `components/ui`

### Build Troubleshooting:

1. **404 Errors**: Check if `[locale]/layout.tsx` exists
2. **Import Errors**: Verify path depth and target file existence
3. **TypeScript Errors**: Ensure `tsconfig.json` paths are correct
4. **Runtime Errors**: Check if all imported files compile successfully

### Next.js 15 Migration Notes:

- `useSearchParams()` requires `Suspense` wrapper
- Use `headers()` instead of `useSearchParams()` where possible
- Ensure all internationalization files exist

**Last Updated:** 2026-02-02
**Issues Fixed:**
- Import path depth calculations
- Missing UI component exports
- TypeScript configuration for Vercel
- Next.js 15 compatibility