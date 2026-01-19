"""
Správa SQLite databáze pro Webomat
"""

import sqlite3
import pandas as pd
from typing import List, Dict, Optional
from config import DATABASE_PATH


class DatabaseManager:
    """Správce SQLite databáze pro uložení podniků"""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Inicializace databáze a vytvoření tabulek"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Vytvoření tabulky businesses
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS businesses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT,
                    phone TEXT,
                    rating REAL,
                    review_count INTEGER,
                    lat REAL,
                    lng REAL,
                    place_id TEXT UNIQUE,
                    website TEXT DEFAULT NULL,
                    email TEXT,
                    status TEXT DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Index pro rychlejší vyhledávání
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_place_id ON businesses(place_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_website ON businesses(website)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_status ON businesses(status)"
            )

            conn.commit()

    def business_exists(self, place_id: str) -> bool:
        """Kontroluje, zda podnik již existuje v databázi"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM businesses WHERE place_id = ? LIMIT 1", (place_id,)
            )
            return cursor.fetchone() is not None

    def save_business(self, business_data: Dict) -> bool:
        """Uloží podnik do databáze"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO businesses
                    (name, address, phone, rating, review_count, lat, lng, place_id, website, email, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        business_data.get("name"),
                        business_data.get("address"),
                        business_data.get("phone"),
                        business_data.get("rating"),
                        business_data.get("review_count"),
                        business_data.get("lat"),
                        business_data.get("lng"),
                        business_data.get("place_id"),
                        business_data.get("website"),
                        business_data.get("email"),
                        business_data.get("status", "new"),
                    ),
                )

                conn.commit()
                return True

        except sqlite3.Error as e:
            print(f"Chyba při ukládání do databáze: {e}")
            return False

    def get_businesses_without_website(self) -> List[Dict]:
        """Vrátí všechny podniky bez webu"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM businesses
                WHERE website IS NULL OR website = ''
                ORDER BY rating DESC, review_count DESC
            """)

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_all_businesses(self) -> List[Dict]:
        """Vrátí všechny podniky"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM businesses ORDER BY created_at DESC")

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def update_business_status(self, place_id: str, status: str) -> bool:
        """Aktualizuje status podniku"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE businesses SET status = ? WHERE place_id = ?",
                    (status, place_id),
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Chyba při aktualizaci statusu: {e}")
            return False

    def export_to_csv(self, filepath: str, businesses: Optional[List[Dict]] = None):
        """Export podniků do CSV souboru"""
        if businesses is None:
            businesses = self.get_businesses_without_website()

        if not businesses:
            print("Žádné podniky k exportu")
            return

        df = pd.DataFrame(businesses)
        df.to_csv(filepath, index=False, encoding="utf-8")
        print(f"Exportováno {len(businesses)} podniků do {filepath}")

    def get_stats(self) -> Dict:
        """Vrátí statistiky databáze"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Celkový počet podniků
            cursor.execute("SELECT COUNT(*) FROM businesses")
            total_businesses = cursor.fetchone()[0]

            # Počet bez webu
            cursor.execute(
                "SELECT COUNT(*) FROM businesses WHERE website IS NULL OR website = ''"
            )
            without_website = cursor.fetchone()[0]

            # Průměrné hodnocení
            cursor.execute("SELECT AVG(rating) FROM businesses WHERE rating > 0")
            avg_rating = cursor.fetchone()[0] or 0

            # Průměrný počet recenzí
            cursor.execute(
                "SELECT AVG(review_count) FROM businesses WHERE review_count > 0"
            )
            avg_reviews = cursor.fetchone()[0] or 0

            return {
                "total_businesses": total_businesses,
                "without_website": without_website,
                "with_website": total_businesses - without_website,
                "avg_rating": round(avg_rating, 2),
                "avg_reviews": round(avg_reviews, 2),
            }
