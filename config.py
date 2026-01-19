"""
Konfigurace pro Webomat - automatické hledání podniků bez webu
"""

import os
from dotenv import load_dotenv

# Načtení proměnných z .env souboru
load_dotenv()

# Google Places API klíč
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

if not GOOGLE_PLACES_API_KEY:
    raise ValueError("GOOGLE_PLACES_API_KEY nenalezen v .env souboru!")

# Nastavení pro hledání
START_ADDRESS = "Balbínova 5, Praha 2, Vinohrady"
SEARCH_RADIUS = 1500  # metry (1.5km)

# Filtry pro podniky
MIN_RATING = 4.0
MIN_REVIEWS = 10

# Databázové nastavení
DATABASE_PATH = "businesses.db"

# Rate limiting
REQUEST_DELAY = 2  # sekundy mezi requesty
MAX_PLACES_PER_SEARCH = 60  # Google Places API limit

# Výstupní soubory
CSV_EXPORT_PATH = "businesses_without_website.csv"

# Adresářová struktura
BUSINESS_DATA_DIR = "businesses_data"

# Debug nastavení
DEBUG_MODE = True
LOG_LEVEL = "INFO"
