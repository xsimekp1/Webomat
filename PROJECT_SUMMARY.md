# Webomat CRM System - Project Summary

## 🎯 Project Overview
Webomat is a comprehensive CRM system for managing businesses, sales, and web development projects. It combines Google Places API integration for finding businesses without websites, with a full CRM functionality for sales management.

## 🏗️ Architecture
- **Backend:** Supabase (PostgreSQL database)
- **Frontend:** Streamlit web application
- **APIs:** Google Places, OpenAI Claude, Supabase
- **Database:** 12 tables with relationships (sellers, businesses, CRM activities, invoices, etc.)

## 📁 Project Structure
```
Webomat/
├── webomat/                    # Main Python application
│   ├── webomat.py             # Core business search logic
│   ├── grid_manager.py        # Grid search management
│   ├── supabase_rest_manager.py # Supabase API manager
│   ├── supabase_manager.py    # Additional Supabase utilities
│   ├── create_tables.sql      # Database schema (12 tables)
│   ├── config.py              # Configuration utilities
│   ├── database.py            # Database connection helpers
│   ├── demo_supabase.py       # Demo/test scripts
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment variables (credentials)
│   ├── .env.example           # Example environment file
│   └── README.md              # Installation guide
├── streamlit_app/             # Streamlit web application
│   ├── app.py                 # Main Streamlit app
│   ├── pages/                 # Individual pages
│   │   ├── dashboard.py       # Main dashboard
│   │   ├── businesses.py      # Business management
│   │   ├── crm.py             # CRM activities
│   │   ├── map.py             # Map visualization
│   │   ├── search.py          # Business search
│   │   ├── settings.py        # Settings/configuration
│   │   └── quick_generate.py  # AI website generation
│   ├── utils/                 # Utility modules
│   │   ├── database.py        # Database operations
│   │   ├── config.py          # Configuration
│   │   ├── stats.py           # Statistics functions
│   │   └── tasks.py           # Task management
│   ├── components/            # Reusable UI components
│   │   └── ui_components.py   # UI helpers
│   ├── requirements.txt       # Streamlit dependencies
│   └── README.md              # App documentation
├── README.md                  # Main project README
├── README_INSTALL.md          # Installation instructions
├── requirements.txt           # Main dependencies
├── .env.example               # Environment template
└── .gitignore                 # Git ignore rules
```

## 🚀 Quick Start Guide (New Computer)

### 1. Clone Repository
```bash
git clone https://github.com/xsimekp1/Webomat.git
cd Webomat
```

### 2. Install Dependencies
```bash
# Install main Python dependencies
pip install -r requirements.txt

# Install Streamlit app dependencies
pip install -r streamlit_app/requirements.txt
```

### 3. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API keys:
# - SUPABASE_URL
# - SUPABASE_SERVICE_ROLE_KEY
# - SUPABASE_ANON_KEY
# - GOOGLE_PLACES_API_KEY
# - OPENAI_API_KEY
```

### 4. Setup Database
```bash
# Create Supabase tables (if not already created)
python webomat/auto_setup.py
# OR manually copy SQL from webomat/create_tables.sql to Supabase SQL Editor
```

### 5. Run Applications

**Streamlit CRM App:**
```bash
cd streamlit_app
streamlit run app.py
```

**Command-line Business Search:**
```bash
cd webomat
python webomat.py --help
```

## 🔑 API Keys Required

### Supabase (Database)
- Project URL: https://cmtvixayfbqhdlftsgqg.supabase.co
- Service Role Key: `sb_secret_cSqLqk2izUgdyIjJvKwOCw_oB-3inak`
- Anon Key: `sb_publishable_XV3ifwMES8zGC0Yvu4yP4Q`

### Google Places API
- API Key: Required for business search functionality

### OpenAI Claude
- API Key: Required for AI website generation

## 📊 Database Schema

### Core Tables:
1. **sellers** - Sales representatives
2. **businesses** - Client companies/leads
3. **business_contacts** - Contact persons
4. **crm_activities** - Sales activities (calls, emails, meetings)
5. **tasks** - Tasks and follow-ups
6. **website_projects** - Web development projects
7. **project_assets** - Project files and documents
8. **client_invoices** - Invoices
9. **client_invoice_items** - Invoice line items
10. **commissions** - Sales commissions
11. **payouts** - Commission payouts
12. **payout_items** - Payout details

All tables include proper relationships, indexes, and constraints.

## 🔧 Key Features

### Business Search Engine
- Google Places API integration
- Grid-based search algorithm
- CSV export functionality
- Rating and review filtering

### CRM System
- Lead management
- Activity tracking
- Task management
- Commission calculation

### Web Development Tools
- AI-powered website generation (Claude)
- Project management
- Invoice generation
- Asset management

## 🚀 Deployment Options

### Current Setup:
- Local development with Streamlit
- Supabase cloud database
- API integrations

### Future Scalability:
- Multi-user authentication (5 users + admin)
- Claude AI integration for website generation
- Production deployment (Vercel, Railway, etc.)
- User role management

## 📝 Development Notes

### Recent Changes:
- ✅ Database schema created (12 tables)
- ✅ Supabase integration completed
- ✅ Repository cleaned up
- ✅ GitHub repository updated

### Next Steps (Future Development):
- Implement user authentication
- Add Claude AI for website generation
- Create admin dashboard
- Multi-user role management
- Production deployment setup

## 🔗 Links
- **GitHub Repository:** https://github.com/xsimekp1/Webomat
- **Supabase Project:** https://supabase.com/dashboard/project/cmtvixayfbqhdlftsgqg
- **Streamlit Documentation:** https://docs.streamlit.io

---

**This project is ready for development on any computer with Python 3.8+ and internet connection.**