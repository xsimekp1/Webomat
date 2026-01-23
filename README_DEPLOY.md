# Webomat - CRM & Business Discovery System

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Railway CLI (`npm install -g @railway/cli`)
- Vercel CLI (`npm install -g vercel`)
- EAS CLI (`npm install -g @expo/eas-cli`)

### Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/xsimekp1/Webomat.git
   cd Webomat
   ```

2. **Setup backend:**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your Supabase credentials
   pip install -r requirements.txt
   ```

3. **Setup frontend:**
   ```bash
   cd ../frontend
   npm install
   cp .env.example .env.local
   # Add NEXT_PUBLIC_API_URL
   ```

4. **Setup mobile:**
   ```bash
   cd ../mobile
   npm install
   ```

## 🏗️ Development

```bash
# Backend
npm run backend:dev

# Frontend
npm run frontend:dev

# Mobile
npm run mobile
```

## 🚀 Deployment

### One-click deploy all services:
```bash
npm run deploy:all
```

### Individual deployments:

**Backend (Railway):**
```bash
./scripts/deploy-backend.sh
# Or manually: railway login && cd backend && railway deploy
```

**Frontend (Vercel):**
```bash
./scripts/deploy-frontend.sh
# Or manually: cd frontend && vercel --prod
```

**Mobile (EAS):**
```bash
./scripts/deploy-mobile.sh
# Or manually: cd mobile && eas build --profile production
```

## 🌐 Live URLs

- **Web App:** https://webomat.vercel.app
- **API:** https://webomat-backend-production.up.railway.app
- **Mobile:** Expo Go or downloaded APKs

## 📱 Mobile Testing

1. **Development:** `npm run mobile` → scan QR in Expo Go
2. **Production build:** `npm run mobile:build:prod`
3. **Download:** Check Expo dashboard for build links

## 🔧 Configuration

### Environment Variables

**Backend (.env):**
```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_key
JWT_SECRET_KEY=your_jwt_secret
```

**Frontend (.env.local):**
```
NEXT_PUBLIC_API_URL=https://webomat-backend-production.up.railway.app
```

**Mobile (app.json):**
```json
{
  "expo": {
    "extra": {
      "eas": {
        "projectId": "your-eas-project-id"
      }
    }
  }
}
```

## 📋 CI/CD

GitHub Actions automatically deploys on push to master:
- ✅ Backend → Railway
- ✅ Frontend → Vercel
- ✅ Mobile → EAS (preview builds)

## 🏛️ Architecture

```
Webomat/
├── backend/          # FastAPI (Railway)
├── frontend/         # Next.js (Vercel)
├── mobile/          # React Native (EAS)
├── shared/          # Common code
└── scripts/         # Deployment scripts
```

## 📞 Support

For issues and questions, check the documentation in `CLAUDE.md` or create an issue.