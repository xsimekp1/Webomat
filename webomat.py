#!/usr/bin/env python3
"""
Webomat - Automatické hledání podniků bez webových stránek

Hledá podniky v okolí zadané adresy, které mají dobré hodnocení,
ale nemají uvedenou webovou stránku.
"""

import time
import logging
from typing import List, Dict, Tuple
import googlemaps
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from config import (
    GOOGLE_PLACES_API_KEY,
    START_ADDRESS,
    SEARCH_RADIUS,
    MIN_RATING,
    MIN_REVIEWS,
    REQUEST_DELAY,
    MAX_PLACES_PER_SEARCH,
    CSV_EXPORT_PATH,
    DEBUG_MODE,
    LOG_LEVEL,
)
from database import DatabaseManager


class Webomat:
    """Hlavní třída pro hledání podniků bez webu"""

    def __init__(self):
        self.setup_logging()
        self.db = DatabaseManager()
        self.gmaps = googlemaps.Client(key=GOOGLE_PLACES_API_KEY)
        self.geolocator = Nominatim(user_agent="Webomat/1.0")
        self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1)

        # Statistiky
        self.stats = {
            "places_searched": 0,
            "places_filtered": 0,
            "places_without_website": 0,
            "api_requests": 0,
        }

    def setup_logging(self):
        """Nastavení logování"""
        level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler("webomat.log"), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def get_coordinates(self, address: str) -> Tuple[float, float]:
        """Převede adresu na GPS souřadnice"""
        self.logger.info(f"Geocoding adresy: {address}")

        try:
            location = self.geocode(address)
            if location:
                self.logger.info(".4f")
                return location.latitude, location.longitude
            else:
                raise ValueError(f"Adresu '{address}' se nepodařilo najít")
        except Exception as e:
            self.logger.error(f"Chyba při geocodingu: {e}")
            raise

    def search_nearby_places(
        self, lat: float, lng: float, radius: int = SEARCH_RADIUS
    ) -> List[Dict]:
        """Hledá podniky v okolí souřadnic"""
        self.logger.info(".4f")

        places = []
        next_page_token = None

        while len(places) < MAX_PLACES_PER_SEARCH:
            try:
                # API request
                response = self.gmaps.places_nearby(
                    location=(lat, lng),
                    radius=radius,
                    type="establishment",  # Všechny typy podniků
                    page_token=next_page_token,
                )
                self.stats["api_requests"] += 1

                if "results" in response:
                    places.extend(response["results"])

                # Kontrola další stránky
                next_page_token = response.get("next_page_token")
                if not next_page_token:
                    break

                # Rate limiting - Google API potřebuje čas mezi stránkami
                time.sleep(REQUEST_DELAY)

            except Exception as e:
                self.logger.error(f"Chyba při vyhledávání míst: {e}")
                break

        self.logger.info(f"Nalezeno {len(places)} podniků")
        return places

    def filter_places(self, places: List[Dict]) -> List[Dict]:
        """Filtruje podniky podle kritérií"""
        filtered = []

        for place in places:
            self.stats["places_searched"] += 1

            rating = place.get("rating", 0)
            review_count = place.get("user_ratings_total", 0)

            # Kontrola kritérií
            if rating >= MIN_RATING and review_count >= MIN_REVIEWS:
                filtered.append(place)
                self.stats["places_filtered"] += 1

                if DEBUG_MODE:
                    self.logger.debug(".1f")

        self.logger.info(f"Po filtrování zbývá {len(filtered)} podniků")
        return filtered

    def get_place_details(self, place_id: str) -> Dict:
        """Získá detailní informace o podniku"""
        try:
            response = self.gmaps.place(
                place_id=place_id,
                fields=[
                    "name",
                    "formatted_address",
                    "formatted_phone_number",
                    "rating",
                    "user_ratings_total",
                    "website",
                    "geometry",
                ],
            )
            self.stats["api_requests"] += 1

            if "result" in response:
                result = response["result"]

                # Extrakce dat
                business_data = {
                    "place_id": place_id,
                    "name": result.get("name", ""),
                    "address": result.get("formatted_address", ""),
                    "phone": result.get("formatted_phone_number", ""),
                    "rating": result.get("rating", 0),
                    "review_count": result.get("user_ratings_total", 0),
                    "website": result.get("website", ""),
                    "lat": result.get("geometry", {}).get("location", {}).get("lat", 0),
                    "lng": result.get("geometry", {}).get("location", {}).get("lng", 0),
                    "email": "",  # Email zatím nevyplňujeme
                }

                return business_data

        except Exception as e:
            self.logger.error(f"Chyba při získávání detailů pro {place_id}: {e}")

        return {}

    def process_businesses(self, places: List[Dict]):
        """Zpracuje seznam podniků a uloží ty bez webu"""
        for place in places:
            place_id = place.get("place_id")

            if not place_id:
                continue

            # Kontrola, zda už podnik není v databázi
            if self.db.business_exists(place_id):
                self.logger.debug(f"Podnik {place.get('name')} už je v databázi")
                continue

            # Získání detailních informací
            business_data = self.get_place_details(place_id)

            if not business_data:
                continue

            # Kontrola webu
            website = business_data.get("website", "").strip()
            if not website:
                self.stats["places_without_website"] += 1
                business_data["status"] = "no_website"

                # Uložení do databáze
                if self.db.save_business(business_data):
                    self.logger.info(f"Uložen podnik bez webu: {business_data['name']}")
                else:
                    self.logger.error(f"Nepodařilo uložit: {business_data['name']}")

            # Rate limiting
            time.sleep(REQUEST_DELAY)

    def run(self):
        """Hlavní metoda pro spuštění Webomatu"""
        self.logger.info("=== Spuštění Webomatu ===")

        try:
            # 1. Geocoding startovní adresy
            lat, lng = self.get_coordinates(START_ADDRESS)

            # 2. Hledání podniků v okolí
            places = self.search_nearby_places(lat, lng)

            # 3. Filtrování podniků
            filtered_places = self.filter_places(places)

            # 4. Zpracování podniků
            self.process_businesses(filtered_places)

            # 5. Export výsledků
            self.export_results()

            # 6. Statistiky
            self.print_stats()

        except Exception as e:
            self.logger.error(f"Chyba při běhu Webomatu: {e}")
            raise

    def export_results(self):
        """Export výsledků do CSV"""
        self.logger.info("Export výsledků...")
        self.db.export_to_csv(CSV_EXPORT_PATH)

    def print_stats(self):
        """Vytiskne statistiky"""
        stats = self.db.get_stats()

        print("\n=== STATISTIKY WEBOMATU ===")
        print(f"Prohledáno podniků: {self.stats['places_searched']}")
        print(f"Po filtrování: {self.stats['places_filtered']}")
        print(f"Bez webu: {self.stats['places_without_website']}")
        print(f"API requestů: {self.stats['api_requests']}")
        print(f"\nDatabáze celkem: {stats['total_businesses']}")
        print(f"Bez webu v DB: {stats['without_website']}")
        print(f"S webem v DB: {stats['with_website']}")
        print(".2f")
        print(".1f")
        print(f"\nExport: {CSV_EXPORT_PATH}")


def main():
    """Hlavní funkce"""
    webomat = Webomat()
    webomat.run()


if __name__ == "__main__":
    main()
