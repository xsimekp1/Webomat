# Webomat Streamlit Application

🌐 **Complete web-based interface for business discovery and website generation**

## 🚀 Quick Start

### Windows:
```bash
cd streamlit_app
run_app.bat
```

### Linux/Mac:
```bash
cd streamlit_app
chmod +x run_app.sh
./run_app.sh
```

### Manual:
```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

## ✨ New Features Added

### 1. **🔍 Nearby Business Search on Map**
- **Location-based search**: Search for businesses around any location
- **Visual feedback**: Results displayed directly on interactive map
- **Website filtering**: Filter results by website status (with/without)
- **Instant website generation**: One-click website creation for businesses without websites
- **Radius control**: Adjustable search radius (100m - 3km)
- **Result limiting**: Control number of businesses returned

### 2. **🌐 Quick Website Generator**
- **Manual business input**: Complete business information forms
- **Multiple source links**: Add existing websites, Facebook, Google Maps links
- **Content extraction**: Automatic processing from provided links
- **Customizable styling**: Choose website colors, themes, and layouts
- **Instant download**: Generated websites ready immediately
- **Template options**: Modern, Classic, Minimal styles

### 3. **📊 Enhanced Dashboard**
- **Real-time statistics**: Live business counts and coverage metrics
- **Interactive charts**: Website status distribution, rating histograms
- **Progress tracking**: Visual feedback for long-running operations
- **Quick actions**: One-click access to all major functions
- **Task monitoring**: Background task status and management

### 4. **🗺️ Interactive Map System**
- **Multi-layer maps**: Toggle grid cells, business markers, search results
- **Color-coded markers**: Blue (has website), Orange (no website), Red (search areas)
- **Click interactions**: Click markers for business details and actions
- **Search integration**: Direct map-based business discovery
- **Coverage visualization**: Grid coverage progress and statistics

## 🔧 Technical Improvements

### **Database Integration**
- ✅ Enhanced schema with `has_website` and `facebook_id` columns
- ✅ Facebook page handling (treated as no website)
- ✅ Photo download integration for Facebook profiles
- ✅ Migration script for existing databases

### **Background Task System**
- ✅ Progress tracking for long-running operations
- ✅ Real-time UI updates without page refreshes
- ✅ Task history and cleanup
- ✅ Error handling and retry mechanisms

### **Modern UI/UX**
- ✅ Responsive design for mobile and desktop
- ✅ Custom styling with theme colors
- ✅ Intuitive navigation with sidebar menu
- ✅ Professional data tables with filtering
- ✅ Interactive charts and visualizations

## 📱 Complete User Workflows

### **Business Discovery Workflow:**
1. **Map** → Enter location → Set radius → Search
2. **Filter results** → "Only Without Website" → Get target businesses
3. **Generate websites** → One-click generation for each business
4. **Track progress** → Real-time updates in dashboard

### **Quick Website Workflow:**
1. **Quick Generate** → Fill business form → Add links/description
2. **Customize style** → Choose colors, themes, layout
3. **Generate instantly** → Progress bar → Ready for download
4. **Export immediately** → Get HTML files for hosting

### **Data Management Workflow:**
1. **Settings** → Configure API keys → Test connections
2. **Database** → View statistics → Run analysis → Export data
3. **System** → Performance settings → Cache management → Cleanup

## 🛠️ File Structure

```
streamlit_app/
├── app.py                    # Main Streamlit application
├── requirements.txt            # Dependencies
├── run_app.sh/.bat           # Launch scripts
├── README.md                  # Documentation
├── QUICK_START.md             # Quick guide
├── pages/                    # Application pages
│   ├── dashboard.py          # Dashboard with stats & charts
│   ├── businesses.py         # Business management & filtering
│   ├── map.py               # Interactive maps & nearby search
│   ├── search.py            # Advanced search functionality
│   ├── quick_generate.py     # Quick website generator
│   ├── settings.py          # Configuration & management
│   └── __init__.py
├── components/              # Reusable UI components
│   └── ui_components.py    # Charts, tables, progress bars
└── utils/                  # Utility modules
    ├── database.py          # Database wrapper & operations
    ├── config.py            # Configuration management
    ├── stats.py             # Statistics & analysis
    └── tasks.py            # Background task manager
```

## 🎯 Key Benefits

### **Over CLI:**
- **User-friendly**: No command-line knowledge required
- **Visual feedback**: Real-time progress and statistics
- **Mobile accessible**: Web interface from any device
- **Batch operations**: Efficient multi-select and bulk actions
- **Interactive maps**: Point-and-click business discovery

### **Business Value:**
- **Rapid discovery**: Find nearby businesses instantly
- **Website gap analysis**: Visualize businesses without online presence
- **Quick website creation**: Generate professional websites in minutes
- **Data export**: CSV export for external analysis
- **Performance monitoring**: Track API usage and costs

## 🔑 First-Time Setup

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Configure API keys**: Go to Settings → API Keys
3. **Initialize database**: Run Settings → Database Operations
4. **Test functionality**: Try Quick Generate with sample business
5. **Explore features**: Use Dashboard, Map, and Search pages

The Streamlit app transforms Webomat from a command-line tool into a professional web platform while maintaining full compatibility with existing functionality and adding powerful new capabilities for modern business discovery and website generation workflows.