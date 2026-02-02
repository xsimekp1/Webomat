# Webomat Streamlit Application

A modern, web-based interface for the Webomat business discovery and website generation system.

## Features

### 🌐 Full Web Interface
- **Interactive Dashboard**: Real-time statistics, charts, and metrics
- **Business Management**: Filterable tables, bulk operations, and detailed views
- **Interactive Maps**: Folium-based coverage maps with business markers
- **Advanced Search**: Location-based, grid-based, and keyword search
- **Quick Website Generator**: Instant website creation from manual inputs
- **Settings Management**: API keys, database operations, and system configuration

### 🔍 Nearby Business Search
- Search businesses around any location or map coordinates
- Filter by website status (with/without website)
- Visual feedback on map with color-coded markers
- Instant website generation for businesses without websites
- Support for radius-based search and result limiting

### 🌐 Quick Website Generator
- Manual business information input forms
- Multiple source links for content extraction
- Customizable website styles and colors
- Automatic HTML generation with professional templates
- Instant download of generated websites

### 📊 Real-Time Progress Tracking
- Background task processing with progress bars
- Live status updates for long-running operations
- Task history and cleanup
- Error handling and retry mechanisms

### 🗺️ Enhanced Map Visualization
- Interactive Folium maps with multiple layers
- Grid coverage visualization
- Business markers with website status colors
- Zoom, pan, and click interactions
- Custom map styles and controls

## Installation

1. **Install Dependencies**:
   ```bash
   cd streamlit_app
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   streamlit run app.py
   ```

3. **Configure API Keys**:
   - Go to Settings page
   - Add Google Maps API key for location services
   - Add OpenAI API key for website content generation

## Usage

### Quick Start
1. Launch the application using `streamlit run app.py`
2. Open your browser to the provided URL (usually `http://localhost:8501`)
3. Configure API keys in Settings if not already done
4. Start exploring features from the Dashboard

### Workflow Examples

#### **Business Discovery Workflow**:
1. Go to **Map** page
2. Use "Nearby Business Search" to find businesses around a location
3. Filter results by "Only Without Website"
4. Generate websites directly from search results
5. Track progress in real-time

#### **Quick Website Generation Workflow**:
1. Go to **Quick Generate** page
2. Fill in business information manually
3. Add existing links (Facebook, Google Maps, etc.)
4. Provide business description
5. Choose website style and generate
6. Download generated website immediately

#### **Database Management Workflow**:
1. Go to **Settings** page
2. View database statistics and health
3. Run migrations or data analysis
4. Export data as CSV
5. Manage grid system and cleanup

## Technical Architecture

### **Backend Integration**
- Leverages existing `webomat.py` core functionality
- Uses `database.py` for data persistence
- Integrates with `grid_manager.py` for coverage mapping
- Maintains compatibility with CLI tools

### **Modern UI/UX**
- Streamlit-based responsive interface
- Real-time updates without page reloads
- Professional styling with custom CSS
- Mobile-friendly design
- Intuitive navigation and workflows

### **Performance Features**
- Background task processing
- Progress tracking and cancellation
- Caching for expensive operations
- Rate limiting and retry mechanisms
- Database query optimization

## File Structure

```
streamlit_app/
├── app.py                 # Main application entry point
├── requirements.txt          # Python dependencies
├── pages/                  # Page modules
│   ├── dashboard.py        # Dashboard with statistics
│   ├── businesses.py       # Business management
│   ├── map.py             # Map visualization
│   ├── search.py          # Search functionality
│   ├── quick_generate.py   # Quick website generator
│   ├── settings.py        # Configuration
│   └── __init__.py
├── components/             # Reusable UI components
│   └── ui_components.py   # Charts, tables, progress bars
└── utils/                 # Utility modules
    ├── database.py         # Database wrapper
    ├── config.py          # Configuration management
    ├── stats.py           # Statistics and analysis
    └── tasks.py          # Background task manager
```

## Benefits Over CLI

- **User-Friendly**: No command-line knowledge required
- **Visual**: Charts, maps, and progress indicators
- **Accessible**: Web-based interface from any device
- **Efficient**: Batch operations and real-time feedback
- **Professional**: Modern UI with responsive design
- **Productive**: Streamlined workflows for common tasks

## Advanced Features

### **Intelligent Search**
- Multiple search modes with smart filtering
- Location-aware search with geocoding
- Business type and rating filters
- Result caching and history

### **Website Generation**
- AI-powered content creation
- Multiple website styles and themes
- Automatic photo integration (Facebook, manual)
- Responsive HTML templates
- SEO optimization

### **Data Management**
- Export functionality for all data types
- Bulk operations for efficiency
- Database migration and analysis tools
- Performance monitoring and statistics

This Streamlit application transforms the command-line Webomat tool into a professional, web-based platform while maintaining full compatibility with existing functionality and adding powerful new features for business discovery and website generation.