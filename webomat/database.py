"""
Správa SQLite databáze pro Webomat
"""

import sqlite3
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import DATABASE_PATH, BUSINESS_DATA_DIR


class DatabaseManager:
    """Správce SQLite databáze pro uložení podniků"""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.business_data_dir = Path(BUSINESS_DATA_DIR)
        self.business_data_dir.mkdir(exist_ok=True)
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
                    has_website BOOLEAN DEFAULT FALSE,
                    facebook_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Index pro rychlejší vyhledávání
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_place_id ON businesses(place_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_has_website ON businesses(has_website)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_website ON businesses(website)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_status ON businesses(status)"
            )

            # Přidat sloupce pro reviews a photos pokud neexistují
            try:
                cursor.execute("ALTER TABLE businesses ADD COLUMN reviews TEXT")
            except sqlite3.OperationalError:
                pass  # Sloupec už existuje

            try:
                cursor.execute("ALTER TABLE businesses ADD COLUMN photos TEXT")
            except sqlite3.OperationalError:
                pass  # Sloupec už existuje

            try:
                cursor.execute("ALTER TABLE businesses ADD COLUMN opening_hours TEXT")
            except sqlite3.OperationalError:
                pass  # Sloupec už existuje

            try:
                cursor.execute("ALTER TABLE businesses ADD COLUMN types TEXT")
            except sqlite3.OperationalError:
                pass  # Sloupec už existuje

            # CRM sloupce pro call management
            try:
                cursor.execute("ALTER TABLE businesses ADD COLUMN next_call_date TEXT")
            except sqlite3.OperationalError:
                pass  # Sloupec už existuje

            try:
                cursor.execute("ALTER TABLE businesses ADD COLUMN call_notes TEXT")
            except sqlite3.OperationalError:
                pass  # Sloupec už existuje

            try:
                cursor.execute("ALTER TABLE businesses ADD COLUMN last_contact TEXT")
            except sqlite3.OperationalError:
                pass  # Sloupec už existuje

            # Uživatelský sloupec pro CRM
            try:
                cursor.execute("ALTER TABLE businesses ADD COLUMN assigned_user TEXT")
            except sqlite3.OperationalError:
                pass  # Sloupec už existuje

            # Sloupec pro název domény
            try:
                cursor.execute("ALTER TABLE businesses ADD COLUMN domain_name TEXT")
            except sqlite3.OperationalError:
                pass  # Sloupec už existuje

            # Tabulka pro grid buňky
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS grid_cells (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lat_center REAL NOT NULL,
                    lng_center REAL NOT NULL,
                    lat_min REAL NOT NULL,
                    lng_min REAL NOT NULL,
                    lat_max REAL NOT NULL,
                    lng_max REAL NOT NULL,
                    searched INTEGER DEFAULT 0,
                    last_searched TIMESTAMP,
                    business_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Index pro grid buňky
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_grid_center ON grid_cells(lat_center, lng_center)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_grid_searched ON grid_cells(searched)"
            )

            # Tabulka pro spojení grid buněk a podniků
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS grid_cell_businesses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cell_id INTEGER NOT NULL,
                    place_id TEXT NOT NULL,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (cell_id) REFERENCES grid_cells (id),
                    FOREIGN KEY (place_id) REFERENCES businesses (place_id),
                    UNIQUE(cell_id, place_id)
                )
            """)

            # Index pro grid cell businesses
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_cell_business ON grid_cell_businesses(cell_id)"
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
            # Compute has_website and facebook_id
            website = business_data.get("website", "").strip()
            has_website = (
                bool(website)
                and "facebook.com" not in website.lower()
                and "fb.com" not in website.lower()
            )
            facebook_id = self.extract_facebook_id(website) if website else None

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO businesses
                    (name, address, phone, rating, review_count, lat, lng, place_id, website, email, status, has_website, facebook_id, reviews, photos, opening_hours, types)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        business_data.get("name"),
                        business_data.get("address"),
                        business_data.get("phone"),
                        business_data.get("rating", 0),
                        business_data.get("review_count", 0),
                        business_data.get("lat", 0),
                        business_data.get("lng", 0),
                        business_data.get("place_id"),
                        website,
                        business_data.get("email"),
                        business_data.get("status", "new"),
                        has_website,
                        facebook_id,
                        json.dumps(business_data.get("reviews", [])),
                        json.dumps(business_data.get("photos", [])),
                        json.dumps(business_data.get("opening_hours", {})),
                        json.dumps(business_data.get("types", [])),
                    ),
                )

                conn.commit()
                return True

        except sqlite3.Error as e:
            print(f"Chyba při ukládání do databáze: {e}")
            return False

    def extract_facebook_id(self, url: str) -> Optional[str]:
        """Extract Facebook user/page ID from URL"""
        if not url or "facebook.com" not in url.lower():
            return None

        url = url.lower()
        if "profile.php?id=" in url:
            # https://www.facebook.com/profile.php?id=100064067558367
            id_start = url.find("id=") + 3
            id_end = url.find("&", id_start)
            if id_end == -1:
                return url[id_start:]
            return url[id_start:id_end]
        elif "/pages/" in url:
            # https://www.facebook.com/pages/Category/PageName/123456789
            # Extract the number at the end
            parts = url.rstrip("/").split("/")
            if parts and parts[-1].isdigit():
                return parts[-1]
            return None
        else:
            # https://www.facebook.com/username
            parts = url.rstrip("/").split("/")
            if len(parts) >= 4:
                username = parts[3]
                if username and username != "pages":
                    return username
        return None

    def get_businesses_without_website(self) -> List[Dict]:
        """Vrátí podniky bez webu"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM businesses
                WHERE has_website = 0
                ORDER BY created_at DESC
            """)

            columns = [desc[0] for desc in cursor.description]
            businesses = []
            for row in cursor.fetchall():
                business = dict(zip(columns, row))
                # Parsovat JSON sloupce
                try:
                    business["reviews"] = json.loads(business.get("reviews", "[]"))
                except:
                    business["reviews"] = []
                try:
                    business["photos"] = json.loads(business.get("photos", "[]"))
                except:
                    business["photos"] = []
                try:
                    business["opening_hours"] = json.loads(
                        business.get("opening_hours", "{}")
                    )
                except:
                    business["opening_hours"] = {}
                try:
                    business["types"] = json.loads(business.get("types", "[]"))
                except:
                    business["types"] = []
                businesses.append(business)
            return businesses

    def get_all_businesses(self) -> List[Dict]:
        """Vrátí všechny podniky"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM businesses ORDER BY created_at DESC")

            columns = [desc[0] for desc in cursor.description]
            businesses = []
            for row in cursor.fetchall():
                business = dict(zip(columns, row))
                # Parsovat JSON sloupce
                try:
                    business["reviews"] = json.loads(business.get("reviews", "[]"))
                except:
                    business["reviews"] = []
                try:
                    business["photos"] = json.loads(business.get("photos", "[]"))
                except:
                    business["photos"] = []
                try:
                    business["opening_hours"] = json.loads(
                        business.get("opening_hours", "{}")
                    )
                except:
                    business["opening_hours"] = {}
                try:
                    business["types"] = json.loads(business.get("types", "[]"))
                except:
                    business["types"] = []
                businesses.append(business)
            return businesses

    def get_business_by_id(self, business_id: int) -> Optional[Dict]:
        """Vrátí podnik podle číselného ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM businesses WHERE id = ?", (business_id,))

            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                business = dict(zip(columns, row))
                # Parsovat JSON sloupce
                try:
                    business["reviews"] = json.loads(business.get("reviews", "[]"))
                except:
                    business["reviews"] = []
                try:
                    business["photos"] = json.loads(business.get("photos", "[]"))
                except:
                    business["photos"] = []
                try:
                    business["opening_hours"] = json.loads(
                        business.get("opening_hours", "{}")
                    )
                except:
                    business["opening_hours"] = {}
                try:
                    business["types"] = json.loads(business.get("types", "[]"))
                except:
                    business["types"] = []
                return business
            return None

    def get_business_by_place_id(self, place_id: str) -> Optional[Dict]:
        """Vrátí podnik podle place_id"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM businesses WHERE place_id = ?", (place_id,))

            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                business = dict(zip(columns, row))
                # Parsovat JSON sloupce
                try:
                    business["reviews"] = json.loads(business.get("reviews", "[]"))
                except:
                    business["reviews"] = []
                try:
                    business["photos"] = json.loads(business.get("photos", "[]"))
                except:
                    business["photos"] = []
                try:
                    business["opening_hours"] = json.loads(
                        business.get("opening_hours", "{}")
                    )
                except:
                    business["opening_hours"] = {}
                try:
                    business["types"] = json.loads(business.get("types", "[]"))
                except:
                    business["types"] = []
                return business
            return None

    def search_businesses(self, keyword: str) -> List[Dict]:
        """Prohledá podniky podle klíčového slova"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Hledání v názvu, adrese a telefonu
            cursor.execute(
                """
                SELECT * FROM businesses
                WHERE name LIKE ? OR address LIKE ? OR phone LIKE ?
                ORDER BY rating DESC, review_count DESC
            """,
                (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"),
            )

            columns = [desc[0] for desc in cursor.description]
            businesses = []
            for row in cursor.fetchall():
                business = dict(zip(columns, row))
                # Parsovat JSON sloupce
                try:
                    business["reviews"] = json.loads(business.get("reviews", "[]"))
                except:
                    business["reviews"] = []
                try:
                    business["photos"] = json.loads(business.get("photos", "[]"))
                except:
                    business["photos"] = []
                try:
                    business["opening_hours"] = json.loads(
                        business.get("opening_hours", "{}")
                    )
                except:
                    business["opening_hours"] = {}
                try:
                    business["types"] = json.loads(business.get("types", "[]"))
                except:
                    business["types"] = []
                businesses.append(business)
            return businesses

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

    def get_business_folder_name(self, business: Dict) -> str:
        """Vytvoří normalizované jméno adresáře pro podnik"""
        name = business.get("name", "unknown").lower()
        # Odstranění speciálních znaků
        name = "".join(c if c.isalnum() or c in " _-" else "_" for c in name)
        name = name.replace(" ", "_").replace("-", "_")
        # Přidání souřadnic pro unikátnost
        lat = round(business.get("lat", 0), 4)
        lng = round(business.get("lng", 0), 4)
        return f"{name}_{lat}_{lng}"

    def create_business_folder(self, business: Dict) -> Path:
        """Vytvoří adresářovou strukturu pro podnik"""
        folder_name = self.get_business_folder_name(business)
        business_dir = self.business_data_dir / folder_name
        business_dir.mkdir(exist_ok=True)

        # Vytvoření základních podsložek
        (business_dir / "social_media").mkdir(exist_ok=True)
        (business_dir / "email_communication").mkdir(exist_ok=True)
        (business_dir / "email_communication" / "sent").mkdir(exist_ok=True)
        (business_dir / "email_communication" / "received").mkdir(exist_ok=True)
        (business_dir / "old_website").mkdir(exist_ok=True)
        (business_dir / "generated_website").mkdir(exist_ok=True)

        return business_dir

    def get_business_folder(self, place_id: str) -> Optional[Path]:
        """Najde adresář podniku podle place_id"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM businesses WHERE place_id = ?", (place_id,))
            business = cursor.fetchone()

        if not business:
            return None

        # Převedení na dict
        columns = [desc[0] for desc in cursor.description]
        business_dict = dict(zip(columns, business))

        folder_name = self.get_business_folder_name(business_dict)
        business_dir = self.business_data_dir / folder_name
        return business_dir if business_dir.exists() else None

    def save_business_metadata(self, place_id: str, metadata: Dict):
        """Uloží metadata podniku do JSON souboru"""
        business_dir = self.get_business_folder(place_id)
        if not business_dir:
            return False

        metadata_file = business_dir / "metadata.json"

        # Přidání timestampu
        metadata["updated_at"] = datetime.now().isoformat()

        try:
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Chyba při ukládání metadat: {e}")
            return False

    def load_business_metadata(self, place_id: str) -> Dict:
        """Načte metadata podniku"""
        business_dir = self.get_business_folder(place_id)
        if not business_dir:
            return {}

        metadata_file = business_dir / "metadata.json"
        if not metadata_file.exists():
            return {}

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {}

    def add_social_media(
        self, place_id: str, platform: str, url: str, notes: str = ""
    ) -> bool:
        """Přidá sociální síť k podniku"""
        business_dir = self.get_business_folder(place_id)
        if not business_dir:
            return False

        social_file = business_dir / "social_media" / f"{platform.lower()}.json"

        data = {
            "platform": platform,
            "url": url,
            "notes": notes,
            "added_at": datetime.now().isoformat(),
        }

        try:
            with open(social_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Chyba při ukládání sociální sítě: {e}")
            return False

    def get_social_media(self, place_id: str) -> Dict[str, Dict]:
        """Vrátí všechny sociální sítě podniku"""
        business_dir = self.get_business_folder(place_id)
        if not business_dir:
            return {}

        social_dir = business_dir / "social_media"
        if not social_dir.exists():
            return {}

        social_media = {}
        for file_path in social_dir.glob("*.json"):
            platform = file_path.stem
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    social_media[platform] = json.load(f)
            except Exception:
                continue

        return social_media

    def add_email_communication(
        self,
        place_id: str,
        email_type: str,
        subject: str,
        content: str,
        recipient: str = "",
        sender: str = "",
    ) -> bool:
        """Přidá email komunikaci"""
        business_dir = self.get_business_folder(place_id)
        if not business_dir:
            return False

        email_dir = business_dir / "email_communication" / email_type
        if not email_dir.exists():
            return False

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        email_file = email_dir / f"{timestamp}.json"

        email_data = {
            "subject": subject,
            "content": content,
            "recipient": recipient,
            "sender": sender,
            "timestamp": datetime.now().isoformat(),
            "type": email_type,
        }

        try:
            with open(email_file, "w", encoding="utf-8") as f:
                json.dump(email_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Chyba při ukládání emailu: {e}")
            return False

    def get_email_communications(self, place_id: str) -> Dict[str, List[Dict]]:
        """Vrátí všechnu email komunikaci"""
        business_dir = self.get_business_folder(place_id)
        if not business_dir:
            return {}

        email_base_dir = business_dir / "email_communication"
        if not email_base_dir.exists():
            return {}

        communications = {}
        for email_type_dir in email_base_dir.iterdir():
            if email_type_dir.is_dir():
                email_type = email_type_dir.name
                communications[email_type] = []

                for email_file in email_type_dir.glob("*.json"):
                    try:
                        with open(email_file, "r", encoding="utf-8") as f:
                            communications[email_type].append(json.load(f))
                    except Exception:
                        continue

        return communications

    def add_old_website_info(
        self, place_id: str, url: str, screenshot_path: str = "", analysis: Dict = None
    ) -> bool:
        """Přidá informace o starém webu"""
        business_dir = self.get_business_folder(place_id)
        if not business_dir:
            return False

        old_website_dir = business_dir / "old_website"

        # Uložení URL
        url_file = old_website_dir / "url.txt"
        try:
            with open(url_file, "w", encoding="utf-8") as f:
                f.write(url)
        except Exception as e:
            return False

        # Uložení analýzy
        if analysis:
            analysis_file = old_website_dir / "analysis.json"
            try:
                with open(analysis_file, "w", encoding="utf-8") as f:
                    json.dump(analysis, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

        return True

    def get_old_website_info(self, place_id: str) -> Dict:
        """Vrátí informace o starém webu"""
        business_dir = self.get_business_folder(place_id)
        if not business_dir:
            return {}

        old_website_dir = business_dir / "old_website"
        if not old_website_dir.exists():
            return {}

        info = {}

        # URL
        url_file = old_website_dir / "url.txt"
        if url_file.exists():
            try:
                with open(url_file, "r", encoding="utf-8") as f:
                    info["url"] = f.read().strip()
            except Exception:
                pass

        # Analýza
        analysis_file = old_website_dir / "analysis.json"
        if analysis_file.exists():
            try:
                with open(analysis_file, "r", encoding="utf-8") as f:
                    info["analysis"] = json.load(f)
            except Exception:
                pass

        return info

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

    # Grid management metody
    def insert_grid_cell(
        self,
        lat_center: float,
        lng_center: float,
        lat_min: float,
        lng_min: float,
        lat_max: float,
        lng_max: float,
    ) -> int:
        """Vloží novou grid buňku a vrátí ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO grid_cells
                (lat_center, lng_center, lat_min, lng_min, lat_max, lng_max)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (lat_center, lng_center, lat_min, lng_min, lat_max, lng_max),
            )
            conn.commit()
            return cursor.lastrowid

    def get_grid_cell_by_center(
        self, lat_center: float, lng_center: float
    ) -> Optional[Dict]:
        """Najde grid buňku podle centra"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM grid_cells
                WHERE lat_center = ? AND lng_center = ?
                LIMIT 1
            """,
                (lat_center, lng_center),
            )
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

    def update_grid_cell_searched(self, cell_id: int, business_count: int):
        """Aktualizuje status prohledanosti buňky"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE grid_cells
                SET searched = 1, last_searched = CURRENT_TIMESTAMP, business_count = ?
                WHERE id = ?
            """,
                (business_count, cell_id),
            )
            conn.commit()

    def get_unsearched_grid_cells(self, limit: int = 10) -> List[Dict]:
        """Vrátí neprohledané grid buňky"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM grid_cells
                WHERE searched = 0
                ORDER BY RANDOM()
                LIMIT ?
            """,
                (limit,),
            )
            columns = [desc[0] for desc in cursor.description]
            businesses = []
            for row in cursor.fetchall():
                business = dict(zip(columns, row))
                # Parsovat JSON sloupce
                try:
                    business["reviews"] = json.loads(business.get("reviews", "[]"))
                except:
                    business["reviews"] = []
                try:
                    business["photos"] = json.loads(business.get("photos", "[]"))
                except:
                    business["photos"] = []
                try:
                    business["opening_hours"] = json.loads(
                        business.get("opening_hours", "{}")
                    )
                except:
                    business["opening_hours"] = {}
                try:
                    business["types"] = json.loads(business.get("types", "[]"))
                except:
                    business["types"] = []
                businesses.append(business)
            return businesses

    def get_all_grid_cells(self) -> List[Dict]:
        """Vrátí všechny grid buňky"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM grid_cells ORDER BY lat_center, lng_center")
            columns = [desc[0] for desc in cursor.description]
            businesses = []
            for row in cursor.fetchall():
                business = dict(zip(columns, row))
                # Parsovat JSON sloupce
                try:
                    business["reviews"] = json.loads(business.get("reviews", "[]"))
                except:
                    business["reviews"] = []
                try:
                    business["photos"] = json.loads(business.get("photos", "[]"))
                except:
                    business["photos"] = []
                try:
                    business["opening_hours"] = json.loads(
                        business.get("opening_hours", "{}")
                    )
                except:
                    business["opening_hours"] = {}
                try:
                    business["types"] = json.loads(business.get("types", "[]"))
                except:
                    business["types"] = []
                businesses.append(business)
            return businesses

    def get_grid_cell_business_count(self, cell_id: int) -> int:
        """Vrátí počet podniků v buňce"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM grid_cell_businesses WHERE cell_id = ?",
                (cell_id,),
            )
            return cursor.fetchone()[0]

    def add_business_to_grid_cell(self, cell_id: int, place_id: str):
        """Přidá podnik do grid buňky"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO grid_cell_businesses (cell_id, place_id)
                    VALUES (?, ?)
                """,
                    (cell_id, place_id),
                )
                conn.commit()
        except sqlite3.Error as e:
            print(f"Chyba při přidávání podniku do grid buňky: {e}")

    def get_grid_coverage_stats(self) -> Dict:
        """Vrátí statistiky pokrytí gridu"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Celkový počet buněk
            cursor.execute("SELECT COUNT(*) FROM grid_cells")
            total_cells = cursor.fetchone()[0]

            # Prohledané buňky
            cursor.execute("SELECT COUNT(*) FROM grid_cells WHERE searched = 1")
            searched_cells = cursor.fetchone()[0]

            # Celkový počet podniků v gridu
            cursor.execute("SELECT COUNT(*) FROM grid_cell_businesses")
            total_businesses_in_grid = cursor.fetchone()[0]

            coverage_percentage = (
                (searched_cells / total_cells * 100) if total_cells > 0 else 0
            )

            return {
                "total_cells": total_cells,
                "searched_cells": searched_cells,
                "unsearched_cells": total_cells - searched_cells,
                "coverage_percentage": round(coverage_percentage, 2),
                "total_businesses_in_grid": total_businesses_in_grid,
            }

    # CRM metody
    def update_call_info(
        self,
        business_id: int,
        next_call_date: str = None,
        call_notes: str = None,
        last_contact: str = None,
    ) -> bool:
        """Aktualizuje CRM informace o hovorech"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Dynamicky sestavit UPDATE dotaz
                update_fields = []
                params = []

                if next_call_date is not None:
                    update_fields.append("next_call_date = ?")
                    params.append(next_call_date)

                if call_notes is not None:
                    update_fields.append("call_notes = ?")
                    params.append(call_notes)

                if last_contact is not None:
                    update_fields.append("last_contact = ?")
                    params.append(last_contact)

                if not update_fields:
                    return True  # Nic k aktualizaci

                params.append(business_id)
                update_query = (
                    f"UPDATE businesses SET {', '.join(update_fields)} WHERE id = ?"
                )

                cursor.execute(update_query, tuple(params))
                conn.commit()
                return cursor.rowcount > 0

        except sqlite3.Error as e:
            print(f"Chyba při aktualizaci CRM informací: {e}")
            return False

    def get_businesses_for_calls(self, date: str = None) -> List[Dict]:
        """Vrátí podniky, které mají být kontaktovány daný den"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM businesses 
                WHERE next_call_date = ? OR (next_call_date IS NULL AND status = 'new')
                ORDER BY next_call_date ASC, rating DESC
            """,
                (date,),
            )

            columns = [desc[0] for desc in cursor.description]
            businesses = []
            for row in cursor.fetchall():
                business = dict(zip(columns, row))
                # Parsovat JSON sloupce
                try:
                    business["reviews"] = json.loads(business.get("reviews", "[]"))
                except:
                    business["reviews"] = []
                try:
                    business["photos"] = json.loads(business.get("photos", "[]"))
                except:
                    business["photos"] = []
                try:
                    business["opening_hours"] = json.loads(
                        business.get("opening_hours", "{}")
                    )
                except:
                    business["opening_hours"] = {}
                try:
                    business["types"] = json.loads(business.get("types", "[]"))
                except:
                    business["types"] = []
                businesses.append(business)
            return businesses

    def get_crm_stats(self) -> Dict:
        """Vrátí CRM statistiky"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Dnesní hovory
                today = datetime.now().strftime("%Y-%m-%d")
                cursor.execute(
                    "SELECT COUNT(*) FROM businesses WHERE next_call_date = ?", (today,)
                )
                today_calls = cursor.fetchone()
                today_calls = today_calls[0] if today_calls else 0

                # Zítra hovory
                tomorrow = (
                    datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    + pd.Timedelta(days=1)
                ).strftime("%Y-%m-%d")
                cursor.execute(
                    "SELECT COUNT(*) FROM businesses WHERE next_call_date = ?",
                    (tomorrow,),
                )
                tomorrow_calls = cursor.fetchone()
                tomorrow_calls = tomorrow_calls[0] if tomorrow_calls else 0

                # Celkem naplánovaných hovorů
                cursor.execute(
                    "SELECT COUNT(*) FROM businesses WHERE next_call_date IS NOT NULL"
                )
                total_scheduled = cursor.fetchone()
                total_scheduled = total_scheduled[0] if total_scheduled else 0

                # Podniky s poznámkami
                cursor.execute(
                    "SELECT COUNT(*) FROM businesses WHERE call_notes IS NOT NULL AND call_notes != ''"
                )
                with_notes = cursor.fetchone()
                with_notes = with_notes[0] if with_notes else 0

                # Nedávné kontakty (posledních 7 dní)
                week_ago = (datetime.now() - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
                cursor.execute(
                    "SELECT COUNT(*) FROM businesses WHERE last_contact IS NOT NULL AND last_contact >= ?",
                    (week_ago,),
                )
                recent_contacts = cursor.fetchone()
                recent_contacts = recent_contacts[0] if recent_contacts else 0

                return {
                    "today_calls": int(today_calls),
                    "tomorrow_calls": int(tomorrow_calls),
                    "total_scheduled": int(total_scheduled),
                    "with_notes": int(with_notes),
                    "recent_contacts": int(recent_contacts),
                }
        except Exception as e:
            # Pokud se něco pokazí, vrať výchozí hodnoty
            print(f"Error in get_crm_stats: {e}")
            return {
                "today_calls": 0,
                "tomorrow_calls": 0,
                "total_scheduled": 0,
                "with_notes": 0,
                "recent_contacts": 0,
            }

    def schedule_call_reminder(self, business_id: int, days_from_now: int = 1) -> bool:
        """Naplánuje připomínku hovoru na X dní od dneška"""
        future_date = (datetime.now() + pd.Timedelta(days=days_from_now)).strftime(
            "%Y-%m-%d"
        )
        return self.update_call_info(business_id, next_call_date=future_date)

    def export_crm_data(self, user_name: str = None) -> Dict:
        """Exportuje CRM data pro sdílení"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Exportovat jen CRM relevantní data
            if user_name:
                cursor.execute(
                    """
                    SELECT id, name, address, phone, email, status, next_call_date, call_notes, last_contact, assigned_user
                    FROM businesses
                    WHERE assigned_user = ? OR assigned_user IS NULL
                    ORDER BY next_call_date ASC, name ASC
                """,
                    (user_name,),
                )
            else:
                cursor.execute("""
                    SELECT id, name, address, phone, email, status, next_call_date, call_notes, last_contact, assigned_user
                    FROM businesses
                    ORDER BY next_call_date ASC, name ASC
                """)

            columns = [desc[0] for desc in cursor.description]
            crm_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return {
                "exported_at": datetime.now().isoformat(),
                "user": user_name,
                "crm_data": crm_data,
                "total_clients": len(crm_data),
            }

    def import_crm_data(
        self, crm_data: Dict, user_name: str = None, merge_strategy: str = "update"
    ) -> Dict:
        """Importuje CRM data ze sdíleného souboru"""
        if "crm_data" not in crm_data:
            return {"error": "Invalid CRM data format"}

        imported = 0
        updated = 0
        skipped = 0

        for client in crm_data["crm_data"]:
            try:
                # Najít existujícího klienta podle jména a adresy
                existing = self.find_business_by_name_address(
                    client["name"], client["address"]
                )

                if existing:
                    if merge_strategy == "skip":
                        skipped += 1
                        continue
                    elif merge_strategy == "update":
                        # Aktualizovat CRM data
                        self.update_call_info(
                            existing["id"],
                            next_call_date=client.get("next_call_date"),
                            call_notes=client.get("call_notes"),
                            last_contact=client.get("last_contact"),
                        )
                        updated += 1
                else:
                    # Vytvořit nového klienta
                    new_business = {
                        "name": client["name"],
                        "address": client["address"],
                        "phone": client.get("phone"),
                        "email": client.get("email"),
                        "status": client.get("status", "new"),
                        "next_call_date": client.get("next_call_date"),
                        "call_notes": client.get("call_notes"),
                        "last_contact": client.get("last_contact"),
                        "assigned_user": user_name or client.get("assigned_user"),
                    }
                    self.save_business(new_business)
                    imported += 1

            except Exception as e:
                print(f"Error importing client {client.get('name')}: {e}")
                continue

        return {
            "imported": imported,
            "updated": updated,
            "skipped": skipped,
            "total_processed": len(crm_data["crm_data"]),
        }

    def find_business_by_name_address(self, name: str, address: str) -> Optional[Dict]:
        """Najde podnik podle jména a adresy"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM businesses WHERE name = ? AND address = ? LIMIT 1",
                (name, address),
            )

            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

    def mark_call_completed(self, business_id: int, notes: str = "") -> bool:
        """Označí hovor jako dokončený a naplánuje další"""
        last_contact = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Naplánujeme další hovor za 7 dní
        next_call = (datetime.now() + pd.Timedelta(days=7)).strftime("%Y-%m-%d")

        return self.update_call_info(
            business_id,
            next_call_date=next_call,
            call_notes=notes,
            last_contact=last_contact,
        )
