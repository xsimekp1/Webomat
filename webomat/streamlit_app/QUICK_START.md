# Webomat - Quick Start Guide

## 🚀 Quick Start

### Method 1: Run App (Windows)
```bash
cd streamlit_app
run_app.bat
```

### Method 2: Run App (Linux/Mac)
```bash
cd streamlit_app
chmod +x run_app.sh
./run_app.sh
```

### Method 3: Manual Run
```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

## 📋 First Steps

1. **Configure API Keys**: Go to Settings → API Keys and add:
   - Google Maps API Key (for business search)
   - OpenAI API Key (for website generation)

2. **Try Quick Generate**: Go to Quick Generate page and create a test website:
   - Enter business name and description
   - Add some links (optional)
   - Choose style and generate

3. **Explore Map Features**: Go to Map page and:
   - Use "Nearby Business Search" to find businesses
   - Filter by website status
   - Generate websites directly from results

4. **Check Dashboard**: Monitor:
   - Real-time statistics
   - Running tasks
   - Recent activity

## 🌐 Key Features

### **Quick Website Generator**
- Instant website creation from manual inputs
- Support for multiple source links
- Customizable styles and themes
- Download generated websites immediately

### **Nearby Business Search**
- Search around any location on map
- Filter by website status (with/without)
- Visual map markers with business details
- One-click website generation for results

### **Interactive Dashboard**
- Real-time statistics and charts
- Progress tracking for long-running tasks
- Business coverage analysis
- Quick action buttons

### **Advanced Search**
- Multiple search modes (location, grid, keyword)
- Smart filtering options
- Result export and bulk operations

## 🔧 Configuration

### **Environment Setup**
1. Install Python dependencies
2. Configure API keys in Settings
3. Initialize grid system (if needed)
4. Test API connections

### **Customization**
- Choose theme colors in Settings
- Configure performance settings
- Set map styles and preferences
- Adjust display options

## 📊 Troubleshooting

### **Common Issues**
- **Streamlit not found**: Run `pip install streamlit`
- **API errors**: Check API key configuration
- **No businesses found**: Ensure grid is initialized
- **Website generation fails**: Check OpenAI API key

### **Support**
- Check Settings → System for debug information
- Use Dashboard → Running Tasks to monitor progress
- Export data for offline analysis

## 🎯 Workflows

### **For Business Discovery**
1. Map → Nearby Search → Enter location
2. Set radius and filters
3. Click search and wait for results
4. Generate websites for businesses without web presence
5. Export results as needed

### **For Quick Website Creation**
1. Quick Generate → Fill business form
2. Add description and any existing links
3. Choose style options
4. Generate and download website
5. Share generated website link

### **For Data Analysis**
1. Check Dashboard for overview statistics
2. Use Businesses page for detailed filtering
3. Export filtered data as CSV
4. Use Settings → Database for management operations

This interface provides a modern, user-friendly way to access all Webomat functionality through a web browser.