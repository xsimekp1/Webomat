# Deployment Best Practices - Webomat

Tento dokument popisuje ověřený proces pro bezpečné a rychlé deploymenty, aby se předešlo výpadkům a chybám.

## 🔧 Před Deploymentem

### 1. Lokální kontrola buildu
**VŽDY** otestuj build lokálně před pushnutím:

```bash
# Frontend build check
cd frontend
npm run build:check  # Zkontroluje TypeScript a build

# Backend type check
cd backend  
python -m py_compile app/main.py
```

### 2. Testovací změny
- Pokud je to major změna, testuj na testovacím prostředí
- Použij `dry_run` pro AI funkcionality
- Ověř, že se nic nerozbilo v existujících funkcích

### 3. Git prepare
```bash
# Check status - žádné unwanted changes
git status
git diff

# Add relevant files only
git add frontend/app/dashboard/crm/[id]/page.tsx
git add backend/app/routers/crm.py
```

## 🚀 Deployment Process

### 1. Backend (Railway) - VŽDY PRVNÍ!
Backend obsahuje API endpointy, takže se musí deploynout jako první:

```bash
# Automatický redeploy
powershell -ExecutionPolicy Bypass -Command "Invoke-RestMethod -Uri 'https://backboard.railway.app/graphql/v2' -Method Post -Headers @{'Content-Type'='application/json'; 'Authorization'='Bearer 66977604-f06c-4e9c-afd2-0440b57f6150'} -Body '{\"query\": \"mutation { serviceInstanceRedeploy(environmentId: \\\"9afdeb2c-17e7-44d5-bfe9-1258121a59aa\\\", serviceId: \\\"54b194dd-644f-4c26-a806-faabaaeacc7b\\\") }\"}'"

# Počkat na redeploy (45s)
sleep 45

# Health check
curl -s https://webomat-backend-production.up.railway.app/health
```

### 2. Frontend (Vercel) - Automatický
```bash
# Push changes
git add .
git commit -m "Clear commit message with what changed"
git push origin master

# Vercel se automaticky deploynout (2-3 minuty)
```

### 3. Deploy Status Kontrola
```bash
# Počkat na deploy start
sleep 30

# Zkontrolovat status
bash scripts/check-vercel-deploy.sh

# Nebo manuálně
curl -s -o /dev/null -w "%{http_code}" https://webomat.vercel.app
# Očekávaný výsledek: 200
```

## 🧪 Post-Deployment Validace

### 1. Basic Health Checks
```bash
# Backend health
curl -s https://webomat-backend-production.up.railway.app/health

# Frontend access
curl -s -o /dev/null -w "%{http_code}" https://webomat.vercel.app

# API connectivity
curl -s https://webomat.vercel.app/api/auth/login
```

### 2. Funkční testy
1. **Login** - Zkus se přihlásit na webomat.vercel.app
2. **CRM** - Otevři nějakého klienta a zkus vytvořit projekt
3. **Dashboard** - Ověř, že se zobrazují rozpracované projekty
4. **API Calls** - Zkontroluj network logy v browser dev tools

### 3. Rollback Plan (pokud něco selže)
**Backend rollback:**
```bash
# Git revert na předchozí verzi
git log --oneline -5
git revert <commit_hash>
git push origin master
# Railway automaticky redeploynout
```

**Frontend rollback:**
```bash
# Vercel dashboard -> Production -> Redeploy previous deployment
# Nebo rollback commit:
git revert <commit_hash>
git push origin master
```

## ⚠️ Časté problémy a jejich řešení

### 1. "n/a Network Error"
- **Příčina**: Backend je down nebo nepřístupný
- **Řešení**: Redeploy backend ( Railway)
- **Prevence**: VŽDY deploy backend jako první

### 2. Build chyba na Vercelu
- **Příčina**: TypeScript duplicity, chybějící dependencies
- **Řešení**: Lokální build check před commitem
- **Prevence**: `npm run build:check` v pre-commit hooku

### 3. Environment variables
- **Příčina**: Chybějící `.env.local` nebo production variables
- **Řešení**: Ověřit Vercel dashboard a Railway environment
- **Prevence**: Mít `.env.local.example` šablonu

### 4. CORS error
- **Příčina**: Backend nemá správně nastavené CORS origins
- **Řešení**: Přidat Vercel URL do CORS_ORIGINS na Railway
- **Prevence**: Testovat CORS changes v dev režimu

## 🔄 CI/CD Process (Cílový stav)

### Git Hooks (automatické)
```bash
# Pre-commit - zabrání broken buildům
.hooks/pre-commit:
  npm run build:check

# Post-push - kontrola deployment status
scripts/check-vercel-deploy.sh
```

### Deploy Commands (one-liners)
```bash
# Full deployment (backend + frontend)
npm run deploy:all

# Backend only
npm run deploy:backend

# Frontend only (auto na push)
npm run deploy:frontend
```

## 📋 Deployment Checklist

Před každým deploymentem:

- [ ] Lokální build projede (`npm run build:check`)
- [ ] TypeScript bez chyb
- [ ] Změny otestované v dev režimu
- [ ] Git commit je čistý (jen relevantní soubory)
- [ ] Commit message je popisný
- [ ] Nejsou sensitive data v commitu

Po každém deploymentu:

- [ ] Backend health check proběhl
- [ ] Frontend je dostupný (HTTP 200)
- [ ] API volání fungují
- [ ] Klíčové funkcionality otestované
- [ ] Network error se neobjevuje

## 🆘 Emergency Recovery

Pokud je úplný výpadek:

1. **Okamžitá diagnostika:**
   ```bash
   # Backend status
   curl -s https://webomat-backend-production.up.railway.app/health
   
   # Frontend status  
   curl -s -o /dev/null -w "%{http_code}" https://webomat.vercel.app
   ```

2. **Rychlý rollback:**
   ```bash
   # Najdi poslední funkční commit
   git log --oneline -10
   
   # Revert
   git revert <problematic_commit>
   git push origin master
   
   # Počkej na auto-deploy
   ```

3. **Komunikace:**
   - Informuj team o stavu
   - Změna statusu ve Slack/Discord
   - Aktualizuj issue tracker

---

**Tento proces se bude neustále vylepšovat podle zkušeností z reálných deploymentů.**