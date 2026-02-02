"""
Database utility functions for Streamlit app
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import from webomat
sys.path.append(str(Path(__file__).parent.parent))

from database import DatabaseManager
from grid_manager import GridManager
from config import DATABASE_PATH, BUSINESS_DATA_DIR
import os

# Initialize database manager - použij hlavní databázi z webomat adresáře
db_path = os.path.join(os.path.dirname(__file__), "..", "..", "businesses.db")
db = DatabaseManager(db_path)
grid_manager = GridManager(db)
