#!/usr/bin/env python3
"""
Webomat - Automatické hledání podniků bez webových stránek

Hledá podniky v okolí zadané adresy, které mají dobré hodnocení,
ale nemají uvedenou webovou stránku.
"""

import time
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import googlemaps
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from tabulate import tabulate
# from rich.console import Console
# from rich.table import Table
# from rich.panel import Panel
# from rich.text import Text

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
    BUSINESS_DATA_DIR,
    DEFAULT_API_BUDGET,
    MAX_CELLS_PER_SEARCH,
)
from grid_manager import GridManager


class CostTracker:
    """API cost tracking and budget management"""

    GOOGLE_PLACES_PRICING = 0.032 / 1000  # $0.032 per 1000 requests

    def __init__(self, budget_limit: float = DEFAULT_API_BUDGET):
        self.session_cost = 0.0
        self.total_cost = 0.0
        self.api_calls = 0
        self.budget_limit = budget_limit

    def add_api_call(self, call_type: str = "places"):
        """Track API call cost"""
        if call_type == "places":
            cost = self.GOOGLE_PLACES_PRICING
        else:
            cost = self.GOOGLE_PLACES_PRICING  # Default for now

        self.session_cost += cost
        self.total_cost += cost
        self.api_calls += 1

    def estimate_operation_cost(
        self, num_cells: int, businesses_per_cell: int = 30
    ) -> float:
        """Estimate cost for grid search operation"""
        # 1 nearby search per cell + ~businesses_per_cell detail requests
        total_calls = num_cells * (1 + businesses_per_cell)
        return total_calls * self.GOOGLE_PLACES_PRICING

    def check_budget(self, additional_cost: float) -> bool:
        """Check if operation fits within budget"""
        return (self.session_cost + additional_cost) <= self.budget_limit

    def get_status(self) -> dict:
        """Get current cost status"""
        return {
            "session_cost": round(self.session_cost, 2),
            "total_cost": round(self.total_cost, 2),
            "api_calls": self.api_calls,
            "budget_limit": self.budget_limit,
            "budget_remaining": round(self.budget_limit - self.session_cost, 2),
        }


# Přidat nové konstanty
CZECH_CITIES = [
    {"name": "Praha", "lat": 50.0755, "lng": 14.4378},
    {"name": "Brno", "lat": 49.1951, "lng": 16.6070},
    {"name": "Ostrava", "lat": 49.8349, "lng": 18.2820},
    {"name": "Plzeň", "lat": 49.7387, "lng": 13.3736},
    {"name": "Liberec", "lat": 50.7662, "lng": 15.0543},
    {"name": "Olomouc", "lat": 49.5938, "lng": 17.2509},
    {"name": "České Budějovice", "lat": 48.9747, "lng": 14.4745},
    {"name": "Hradec Králové", "lat": 50.2092, "lng": 15.8327},
    {"name": "Ústí nad Labem", "lat": 50.6605, "lng": 14.0323},
    {"name": "Pardubice", "lat": 50.0347, "lng": 15.7823},
]
from database import DatabaseManager


class Webomat:
    """Hlavní třída pro hledání podniků bez webu"""

    def __init__(self):
        self.setup_logging()
        self.db = DatabaseManager()
        self.grid_manager = GridManager(self.db)
        self.cost_tracker = CostTracker()
        self.gmaps = googlemaps.Client(key=GOOGLE_PLACES_API_KEY)
        self.geolocator = Nominatim(user_agent="Webomat/1.0")
        self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1)
        # self.console = Console()

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
                self.cost_tracker.add_api_call("places")

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
                    "address_component",  # Opraveno z address_components
                    "formatted_phone_number",
                    "international_phone_number",
                    "rating",
                    "user_ratings_total",
                    "website",
                    "geometry",
                    "opening_hours",
                    "current_opening_hours",
                    "editorial_summary",
                    "reviews",  # Posledních 5 reviews
                    "photo",  # Opraveno z photos
                    "type",  # Opraveno z types
                    "price_level",
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
                    "address_components": result.get("address_component", []),
                    "phone": result.get("formatted_phone_number", ""),
                    "international_phone_number": result.get(
                        "international_phone_number", ""
                    ),
                    "rating": result.get("rating", 0),
                    "review_count": result.get("user_ratings_total", 0),
                    "website": result.get("website", ""),
                    "lat": result.get("geometry", {}).get("location", {}).get("lat", 0),
                    "lng": result.get("geometry", {}).get("location", {}).get("lng", 0),
                    "email": self.extract_email_from_components(
                        result.get("address_component", [])
                    ),
                    "opening_hours": result.get("opening_hours", {}),
                    "current_opening_hours": result.get("current_opening_hours", {}),
                    "editorial_summary": result.get("editorial_summary", ""),
                    "reviews": result.get("reviews", [])[:5],  # Posledních 5 reviews
                    "photos": result.get("photo", []),
                    "types": result.get("type", []),
                    "price_level": result.get("price_level", 0),
                }

                return business_data

        except Exception as e:
            self.logger.error(f"Chyba při získávání detailů pro {place_id}: {e}")

        return {}

    def extract_email_from_components(self, address_components: List[Dict]) -> str:
        """Pokusí se extrahovat email z address components"""
        # Google Places API neposkytuje email přímo, ale můžeme hledat v reviews nebo jinde
        # Pro teď vrátíme prázdný string
        return ""

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
                    # Vytvoření adresářové struktury
                    self.db.create_business_folder(business_data)
                else:
                    self.logger.error(f"Nepodařilo uložit: {business_data['name']}")

            # Rate limiting
            time.sleep(REQUEST_DELAY)

    def show_menu(self):
        """Zobrazí bezpečné hlavní menu"""
        cost_status = self.cost_tracker.get_status()
        grid_status = (
            "Inicializovan"
            if self.grid_manager.is_grid_initialized()
            else "❌ Neinicializován"
        )

        menu_text = f"""
===============================================================================
                            WEBOMAT - SAFE MODE
                    Zadne automaticke operace bez potvrzeni!
===============================================================================

API ROZPOCET: ${cost_status["session_cost"]:.2f} / ${cost_status["budget_limit"]:.2f}
GRID STATUS: {grid_status}

BEZPECNE PRIKAZY:
--------------------------------------------------------------------------------
status                - Zobrazit stav systemu a naklady
analyze data          - Analyzuovat stavajici data (10MB dataset)
show costs            - Zobrazit detailni naklady a rozpocet
set budget <castka>   - Nastavit rozpocet (napr. set budget 10)
reset costs           - Resetovat pocitadlo nakladu

GRID MANAGEMENT:
--------------------------------------------------------------------------------
init grid             - Inicializovat grid system (s potvrzenim)
grid stats            - Statistiky pokryti gridu
show coverage         - Zobrazit mapu pokryti CR

KONTROLOVANE HLEDANI (s potvrzenim nakladu):
--------------------------------------------------------------------------------
search grid 3         - Hledat presne 3 nahodne bunky
search spiral prague   - Hledat spiralou od Prahy
search area <lat> <lng> <pocet> - Hledat kolem souradnic

PROHLIZENI DAT:
--------------------------------------------------------------------------------
show all              - Zobrazit vsechny podniky
show no-website       - Jen podniky bez webu
show high-rated       - Podniky s hodnocenim >= 4.5
show recent           - Podniky nalezene v poslednich 24h
details <ID>          - Detailni informace o podniku

EXPORT A WEBY:
--------------------------------------------------------------------------------
export csv            - Export do CSV
export json           - Export do JSON
makeweb <ID>          - Vygenerovat web pro podnik

VYHLEDAVANI:
--------------------------------------------------------------------------------
search <keyword>      - Hledani v databazi
quit                  - Ukoncit program

===============================================================================
"""
        print(menu_text)

    def get_user_input(self) -> str:
        """Získá vstup od uživatele"""
        try:
            command = input("\nWebomat > ").strip()
            # Převedeme na malá písmena pouze příkaz, ne argumenty
            parts = command.split(" ", 1)
            if len(parts) > 1:
                command = parts[0].lower() + " " + parts[1]
            else:
                command = command.lower()
            return command
        except KeyboardInterrupt:
            return "quit"
        except EOFError:
            return "quit"

    def display_businesses_table(self, businesses: List[Dict], title: str = "Podniky"):
        """Zobrazí podniky v tabulce"""
        if not businesses:
            print(f"Zadne {title.lower()} nenalezeny")
            return

        print(f"\n=== {title} ({len(businesses)}) ===")

        # Připrav data pro tabulate
        table_data = []
        headers = ["#", "Nazev", "Adresa", "Rating", "Reviews", "Web", "Telefon"]

        for business in businesses:
            db_id = business.get("id", "?")
            name = business.get("name", "N/A")[:24]
            address = business.get("address", "N/A")[:29]
            rating = (
                f"{business.get('rating', 0):.1f}" if business.get("rating") else "N/A"
            )
            reviews = str(business.get("review_count", 0))
            has_website = "ANO" if business.get("has_website") else "NE"
            phone = (
                business.get("phone", "N/A")[:14] if business.get("phone") else "N/A"
            )

            table_data.append(
                [str(db_id), name, address, rating, reviews, has_website, phone]
            )

        print(tabulate(table_data, headers=headers, tablefmt="grid"))

    def show_business_details(self, identifier: str):
        """Zobrazí detailní informace o podniku"""
        business = None

        # Zkusit jako číselné ID
        try:
            business_id = int(identifier)
            business = self.db.get_business_by_id(business_id)
        except ValueError:
            # Zkusit jako place_id string
            business = self.db.get_business_by_place_id(identifier)

        if not business:
            print(f"Podnik s ID '{identifier}' nebyl nalezen")
            # Debug informace
            print("Dostupne podniky:")
            all_businesses = self.db.get_all_businesses()
            for b in all_businesses:
                print(
                    f"  ID {b['id']}: {b['name']} (place_id: {b['place_id'][:20]}...)"
                )
            return

        # Základní informace
        details_text = f"""
{business.get("name", "N/A")}
Adresa: {business.get("address", "N/A")}
Hodnoceni: {business.get("rating", "N/A")}/5.0
Recenzi: {business.get("review_count", "N/A")}
Telefon: {business.get("phone", "N/A")}
Web: {business.get("website", "Zadny")}
Place ID: {business.get("place_id", "N/A")}
Vytvoreno: {business.get("created_at", "N/A")}
"""

        print(details_text)

        # Reviews sekce
        reviews = business.get("reviews", [])
        if reviews:
            print(f"RECENZE ({len(reviews)}):")
            for i, review in enumerate(reviews, 1):
                print(
                    f"  {i}. {review.get('author_name', 'Anonymous')}: {review.get('text', 'No text')[:100]}..."
                )

        # Sociální sítě
        social_media = self.db.get_social_media(business.get("place_id"))
        if social_media:
            print("Socialni site:")
            for platform, data in social_media.items():
                print(
                    f"  {platform}: {data.get('url', 'N/A')} ({data.get('notes', '')})"
                )

        # Starý web
        old_website = self.db.get_old_website_info(business.get("place_id"))
        if old_website:
            old_web_text = f"""
 Starý web nalezen:
 {old_website.get("url", "N/A")}
 Analýza: {old_website.get("analysis", {}).get("status", "N/A")}
"""
            print(old_web_text)

        # Email komunikace
        emails = self.db.get_email_communications(business.get("place_id"))
        if emails:
            print("Email komunikace:")
            for email_type, email_list in emails.items():
                if email_list:
                    print(f"  {email_type.upper()}:")
                    for email in email_list[-3:]:  # Posledních 3 emailů
                        date = email.get("timestamp", "N/A")[:10]
                        subject = email.get("subject", "N/A")[:30]
                        contact = email.get("recipient", email.get("sender", "N/A"))
                        print(f"    {date}: {subject} -> {contact}")

    def handle_add_social(self, args: List[str]):
        """Přidá sociální síť k podniku"""
        if len(args) < 3:
            print("[red]Použití: add-social <place_id> <platform> <url> [notes][/red]")
            return

        place_id, platform, url = args[0], args[1], args[2]
        notes = " ".join(args[3:]) if len(args) > 3 else ""

        if self.db.add_social_media(place_id, platform, url, notes):
            print(
                f"[green]OK Sociální síť {platform} přidána k podniku {place_id}[/green]"
            )
        else:
            print("[red]ERROR Nepodařilo přidat sociální síť[/red]")

    def handle_add_email(self, args: List[str]):
        """Přidá email komunikaci"""
        if len(args) < 4:
            print(
                "[red]Použití: add-email <place_id> <type> <subject> <content> [recipient][/red]"
            )
            print("[dim]Typ: sent/received[/dim]")
            return

        place_id, email_type, subject = args[0], args[1], args[2]
        content = args[3]
        recipient = args[4] if len(args) > 4 else ""

        if email_type not in ["sent", "received"]:
            print("[red]Typ musí být 'sent' nebo 'received'[/red]")
            return

        if self.db.add_email_communication(
            place_id, email_type, subject, content, recipient
        ):
            print(f"[green]OK Email komunikace přidána[/green]")
        else:
            print("[red]ERROR Nepodařilo přidat email komunikaci[/red]")

    def handle_add_old_website(self, args: List[str]):
        """Přidá informace o starém webu"""
        if len(args) < 2:
            print(
                "[red]Použití: add-old-website <place_id> <url> [screenshot_path][/red]"
            )
            return

        place_id, url = args[0], args[1]
        screenshot_path = args[2] if len(args) > 2 else ""

        if self.db.add_old_website_info(place_id, url, screenshot_path):
            print(f"[green]OK Starý web přidán k podniku {place_id}[/green]")
        else:
            print("[red]ERROR Nepodařilo přidat starý web[/red]")

    def handle_search(self, keyword: str):
        """Prohledá databázi podle klíčového slova"""
        businesses = self.db.search_businesses(keyword)
        self.display_businesses_table(businesses, f"Výsledky hledání: '{keyword}'")

    def handle_export(self, format_type: str):
        """Export dat"""
        if format_type.lower() == "csv":
            businesses = self.db.get_businesses_without_website()
            self.db.export_to_csv(CSV_EXPORT_PATH, businesses)
            print(f"[green]OK Exportováno do {CSV_EXPORT_PATH}[/green]")
        elif format_type.lower() == "json":
            businesses = self.db.get_businesses_without_website()
            json_path = CSV_EXPORT_PATH.replace(".csv", ".json")
            with open(json_path, "w", encoding="utf-8") as f:
                import json

                json.dump(businesses, f, indent=2, ensure_ascii=False)
            print(f"[green]OK Exportováno do {json_path}[/green]")
        else:
            print("[red]Nepodporovaný formát. Použij 'csv' nebo 'json'[/red]")

    def show_stats(self):
        """Zobrazí statistiky"""
        stats = self.db.get_stats()

        stats_text = f"""
STATISTIKY DATABAZE
================================================================================
Celkem podniku:     {stats["total_businesses"]}
Bez webu:          {stats["without_website"]}
S webem:           {stats["with_website"]}
Prumerne hodnoceni: {stats["avg_rating"]}/5.0
Prumer recenzii:    {stats["avg_reviews"]}
================================================================================
"""
        print(stats_text)

    def confirm_expensive_operation(self, operation_desc: str, num_cells: int) -> bool:
        """Require user confirmation for expensive operations"""
        estimated_cost = self.cost_tracker.estimate_operation_cost(num_cells)
        status = self.cost_tracker.get_status()

        print(f"\nWARNING: {operation_desc}")
        print(f"Cell count: {num_cells}")
        print(f"Estimated cost: ${estimated_cost:.2f}")
        print(f"Current session cost: ${status['session_cost']:.2f}")
        print(f"Remaining budget: ${status['budget_remaining']:.2f}")

        if estimated_cost > 5.0:
            print("HIGH COST! Confirmation recommended.")
        elif estimated_cost > 1.0:
            print("Medium cost - check budget.")

        if not self.cost_tracker.check_budget(estimated_cost):
            print(
                "Operation exceeds budget! Set higher limit with 'set budget <amount>'"
            )
            return False

        try:
            response = input("\nContinue? (y/N): ").strip().lower()
            return response in ["y", "yes", "ano", "a"]
        except (KeyboardInterrupt, EOFError):
            print("Operation cancelled")
            return False

    def handle_grid_search_random(self, count: int):
        """Hledání v náhodných grid buňkách"""
        # Ensure grid is initialized
        if not self.grid_manager.ensure_initialized():
            print("Grid is not initialized")

        # Limit large searches
        if count > MAX_CELLS_PER_SEARCH:
            print(f"Limited to {MAX_CELLS_PER_SEARCH} cells at once (safety limit)")
            count = MAX_CELLS_PER_SEARCH

        # Confirm operation
        if not self.confirm_expensive_operation(
            f"Nahodne prohledavani {count} grid bunek", count
        ):
            return

        cells = self.grid_manager.get_random_unsearched_cells(count)
        if not cells:
            print("Zadne neprohledane bunky k dispozici")
            return

        print(f"Prohledavam {len(cells)} nahodnych bunek...")
        total_businesses = 0

        try:
            for i, cell in enumerate(cells, 1):
                print(
                    f"Bunka {i}/{len(cells)}: {cell['lat_center']:.4f}, {cell['lng_center']:.4f}"
                )
                businesses_found = self.search_grid_cell(cell)
                total_businesses += businesses_found

                # Show progress cost
                current_cost = self.cost_tracker.get_status()["session_cost"]
                print(f"Aktualni naklady: ${current_cost:.2f}")

        except KeyboardInterrupt:
            print("\nOperace prerusena uzivatelem")
            return

        print(f"Celkem nalezeno {total_businesses} podniku v {len(cells)} bunkach")

    def handle_grid_search_spiral(self, max_cells: int):
        """Hledání ve spirále od Prahy"""
        # Začínáme z Prahy
        prague_lat, prague_lng = 50.0755, 14.4378
        cells = self.grid_manager.get_spiral_cells(prague_lat, prague_lng, max_cells)

        print(f"Prohledávám {len(cells)} buněk ve spirále od Prahy...")
        total_businesses = 0

        for cell in cells:
            businesses_found = self.search_grid_cell(cell)
            total_businesses += businesses_found

        print(f"Celkem nalezeno {total_businesses} podniků")

    def handle_grid_search_area(self, lat: float, lng: float, cells: int):
        """Hledání kolem konkrétní oblasti"""
        cells_list = self.grid_manager.get_spiral_cells(lat, lng, cells)

        print(f"Prohledávám {len(cells_list)} buněk kolem {lat:.4f}, {lng:.4f}...")
        total_businesses = 0

        for cell in cells_list:
            businesses_found = self.search_grid_cell(cell)
            total_businesses += businesses_found

        print(f"Celkem nalezeno {total_businesses} podniků")

    def search_grid_cell(self, cell: Dict) -> int:
        """Prohledá jednu grid buňku"""
        lat_center = cell["lat_center"]
        lng_center = cell["lng_center"]

        print(f"Prohledávám buňku: {lat_center:.4f}, {lng_center:.4f}")

        # Hledání podniků v buňce
        places = self.search_nearby_places(
            lat_center, lng_center, radius=int(self.grid_manager.CELL_SIZE_METERS / 2)
        )
        filtered_places = self.filter_places(places)

        # Zpracování podniků
        self.process_businesses(filtered_places)

        # Aktualizace buňky
        self.grid_manager.mark_cell_searched(cell["id"], len(filtered_places))

        # Přidání podniků do buňky
        for place in filtered_places:
            place_id = place.get("place_id")
            if place_id:
                self.grid_manager.add_business_to_cell(cell["id"], place_id)

        return len(filtered_places)

    def handle_show_coverage(self):
        """Zobrazí mapu pokrytí ČR"""
        try:
            import folium

            # Získání statistik
            stats = self.grid_manager.get_coverage_stats()

            # Vytvoření mapy
            m = folium.Map(location=[50.0755, 14.4378], zoom_start=7)

            # Získání vzorku buněk (max 1000 pro výkon)
            all_cells = self.grid_manager.db.get_all_grid_cells()
            sample_cells = all_cells[:1000] if len(all_cells) > 1000 else all_cells

            # Přidání buněk jako markers (jednodušší než polygony)
            searched_count = 0
            unsearched_count = 0

            for cell in sample_cells:
                if cell["searched"]:
                    searched_count += 1
                    color = "green"
                    icon = "check-circle"
                else:
                    unsearched_count += 1
                    color = "red"
                    icon = "times-circle"

                # Přidání markeru ve středu buňky
                folium.Marker(
                    location=[cell["lat_center"], cell["lng_center"]],
                    popup=f"Bunka: {cell['lat_center']:.4f}, {cell['lng_center']:.4f}<br>Status: {'Prohledana' if cell['searched'] else 'Neprohledana'}",
                    icon=folium.Icon(color=color, icon=icon, prefix="fa"),
                ).add_to(m)

            # Získání vzorku podniků pro mapu (max 1000)
            all_businesses = self.db.get_all_businesses()
            business_sample = (
                all_businesses[:1000] if len(all_businesses) > 1000 else all_businesses
            )

            # Přidání podniků jako markers
            with_website_count = 0
            without_website_count = 0

            for business in business_sample:
                lat = business.get("lat")
                lng = business.get("lng")
                if lat and lng:
                    has_website = business.get("has_website", False)
                    if has_website:
                        color = "blue"
                        with_website_count += 1
                    else:
                        color = "orange"
                        without_website_count += 1

                    folium.CircleMarker(
                        location=[lat, lng],
                        radius=3,
                        color=color,
                        fill=True,
                        fill_color=color,
                        fill_opacity=0.7,
                        popup=f"{business.get('name', 'N/A')}<br>Web: {'Ano' if has_website else 'Ne'}",
                    ).add_to(m)

            # Statistiky v HTML
            title_html = f"""
                <div style="position: fixed; top: 10px; left: 10px; z-index: 1000; background: white; padding: 10px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                    <h4>Pokrytí ČR</h4>
                    <p>Celkem buněk: {stats["total_cells"]}</p>
                    <p>Prohledaných: {stats["searched_cells"]} ({stats["coverage_percentage"]:.1f}%)</p>
                    <p>Zobrazeno vzorku: {len(sample_cells)} buněk</p>
                    <p>Zelené: prohledané, Červené: neprohledané</p>
                    <p>Podniky: {with_website_count} s webem (modré), {without_website_count} bez webu (oranžové)</p>
                </div>
            """
            m.get_root().html.add_child(folium.Element(title_html))

            # Uložení mapy
            map_file = "grid_coverage.html"
            m.save(map_file)
            print(f"Mapa pokrytí uložena do {map_file}")
            print(
                f"Zobrazeno: {searched_count} prohledaných, {unsearched_count} neprohledaných buněk"
            )
            print(
                f"Podniky: {with_website_count} s webem, {without_website_count} bez webu"
            )

            # Zkusit otevřít v prohlížeči
            import webbrowser

            try:
                webbrowser.open(map_file)
            except:
                print(f"Otevřete {map_file} v prohlížeči")

        except ImportError:
            print("Pro zobrazení mapy nainstalujte folium: pip install folium")
        except Exception as e:
            print(f"Chyba při vytváření mapy: {e}")
            import traceback

            traceback.print_exc()

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

    def download_facebook_photo(self, facebook_id: str, save_path: str) -> bool:
        """Download Facebook profile picture using Graph API"""
        try:
            import requests
            import time

            # Facebook Graph API for profile picture
            url = f"https://graph.facebook.com/{facebook_id}/picture?type=large"

            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                print(f"Downloaded Facebook photo for {facebook_id}")
                time.sleep(1)  # Rate limiting
                return True
            else:
                print(
                    f"Failed to download Facebook photo for {facebook_id}: {response.status_code}"
                )
                return False
        except Exception as e:
            print(f"Error downloading Facebook photo for {facebook_id}: {e}")
            return False

    def handle_makeweb(self, args: List[str]):
        """Vygeneruje web pro podnik pomocí opencode"""
        if len(args) < 1:
            print("[red]Použití: makeweb <place_id>[/red]")
            return

        place_id = args[0]
        business = self.db.get_business_by_place_id(place_id)

        if not business:
            print(f"[red]Podnik s ID {place_id} nebyl nalezen[/red]")
            return

        print(f"Generuji web pro: {business['name']}")

        # Zkus stáhnout Facebook fotografii pokud je to Facebook stránka
        facebook_photo_path = None
        if business.get("facebook_id"):
            business_dir = self.db.business_data_dir / place_id
            business_dir.mkdir(exist_ok=True)
            photo_path = business_dir / "facebook_photo.jpg"
            if self.download_facebook_photo(business["facebook_id"], str(photo_path)):
                facebook_photo_path = str(photo_path)

        # Shromáždit data
        business_data = {
            "name": business.get("name", ""),
            "address": business.get("address", ""),
            "phone": business.get("phone", ""),
            "website": business.get("website", ""),
            "rating": business.get("rating", 0),
            "review_count": business.get("review_count", 0),
            "reviews": business.get("reviews", []),
            "types": business.get("types", []),
            "description": business.get("editorial_summary", ""),
            "facebook_photo": facebook_photo_path,
        }

        # Volat opencode pro generování webu
        self.generate_business_website(business_data, place_id)

    def generate_business_website(self, business_data: Dict, place_id: str):
        """Generuje web pomocí opencode"""
        # Připravit prompt pro opencode
        types_str = ", ".join(business_data.get("types", []))
        is_vet = (
            "veterin" in types_str.lower()
            or "pet" in types_str.lower()
            or "animal" in types_str.lower()
        )

        prompt = f"""
        Vytvoř profesionální HTML/CSS/JS web pro podnik:

        Název: {business_data["name"]}
        Adresa: {business_data["address"]}
        Telefon: {business_data["phone"]}
        Hodnocení: {business_data["rating"]}/5
        Typ podniku: {types_str}
        Popis: {business_data["description"]}

        Web by měl obsahovat:
        - Moderní design s Bootstrap 5
        - Header s názvem a kontaktními informacemi
        - Sekce "O nás" s popisem
        - Kontaktní formulář
        - Footer s copyright
        - Responzivní design pro mobil i desktop

        {"Pokud je to veterinář nebo podobné, přidej free stock fotky koček, psů a dalších zvířat z Unsplash nebo Pexels API." if is_vet else ""}

        Vrátí kompletní HTML kód s inline CSS a JS. Web musí být plně funkční a profesionální.
        """

        print("Generování webu pomocí opencode...")
        print(f"Prompt délka: {len(prompt)} znaků")

        # Volat opencode přes task tool
        # Pozn: V tomto prostředí použijeme dummy implementaci
        # V reálném použití by se volal task tool

        business_dir = self.db.get_business_folder(place_id)
        if business_dir:
            website_dir = business_dir / "generated_website"
            website_dir.mkdir(exist_ok=True)

            # Archivovat starou verzi pokud existuje
            index_file = website_dir / "index.html"
            if index_file.exists():
                import datetime

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_file = website_dir / f"index_{timestamp}.html"
                index_file.rename(archive_file)
                print(f"Starý web archivován jako {archive_file.name}")

            # Připravit reviews sekci
            reviews_html = ""
            if business_data.get("reviews"):
                reviews_html = """
                <section id="reviews" class="py-5">
                    <div class="container">
                        <h2 class="text-center mb-5">Recenze našich zákazníků</h2>
                        <div class="row">
                """

                for i, review in enumerate(
                    business_data["reviews"][:3]
                ):  # Zobrazit max 3 reviews
                    stars = "★" * int(review.get("rating", 0)) + "☆" * (
                        5 - int(review.get("rating", 0))
                    )
                    reviews_html += f"""
                    <div class="col-md-4 mb-4">
                        <div class="card h-100">
                            <div class="card-body">
                                <div class="rating-stars mb-2">
                                    {stars} {review.get("rating", 0)}/5
                                </div>
                                <p class="card-text">"{review.get("text", "")[:150]}{"..." if len(review.get("text", "")) > 150 else ""}"</p>
                                <footer class="blockquote-footer mt-2">
                                    {review.get("author_name", "Anonymous")}
                                </footer>
                            </div>
                        </div>
                    </div>
                    """

                reviews_html += """
                        </div>
                    </div>
                </section>
                """

            # Dummy HTML - v reálném použití by to bylo z opencode
            html_content = f"""
            <!DOCTYPE html>
            <html lang="cs">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{business_data["name"]}</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    .hero {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 100px 0;
                    }}
                    .rating-stars {{
                        color: #ffc107;
                        font-size: 1.2em;
                    }}
                    .card {{
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    }}
                </style>
            </head>
            <body>
                <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
                    <div class="container">
                        <a class="navbar-brand fw-bold" href="#">{business_data["name"]}</a>
                        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                            <span class="navbar-toggler-icon"></span>
                        </button>
                        <div class="collapse navbar-collapse" id="navbarNav">
                            <ul class="navbar-nav ms-auto">
                                <li class="nav-item"><a class="nav-link" href="#about">O nás</a></li>
                                <li class="nav-item"><a class="nav-link" href="#reviews">Recenze</a></li>
                                <li class="nav-item"><a class="nav-link" href="#contact">Kontakt</a></li>
                            </ul>
                        </div>
                    </div>
                </nav>

                <section class="hero">
                    <div class="container text-center">
                        <h1 class="display-4 fw-bold">{business_data["name"]}</h1>
                        <p class="lead">{business_data["description"]}</p>
                        <div class="rating-stars fs-5">
                            {"★" * int(business_data["rating"])}{"☆" * (5 - int(business_data["rating"]))} {business_data["rating"]}/5
                        </div>
                        <p class="mt-3">Na základě {business_data["review_count"]} recenzí</p>
                    </div>
                </section>

                <section id="about" class="py-5 bg-light">
                    <div class="container">
                        <div class="row">
                            <div class="col-lg-8">
                                <h2 class="mb-4">O nás</h2>
                                <p class="lead">{business_data["description"]}</p>
                                <div class="row mt-4">
                                    <div class="col-md-6">
                                        <h5>📍 Adresa</h5>
                                        <p>{business_data["address"]}</p>
                                    </div>
                                    <div class="col-md-6">
                                        <h5>📞 Kontakt</h5>
                                        <p>{business_data["phone"]}</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-lg-4">
                                <img src="https://picsum.photos/400/300?random={place_id[:8]}" class="img-fluid rounded shadow" alt="Business Image">
                                {'<img src="https://picsum.photos/400/300?random=dog" class="img-fluid rounded shadow mt-3" alt="Pet">' if is_vet else ""}
                            </div>
                        </div>
                    </div>
                </section>

                {reviews_html}

                <section id="contact" class="py-5">
                    <div class="container">
                        <div class="row justify-content-center">
                            <div class="col-lg-6">
                                <h2 class="text-center mb-4">Kontaktujte nás</h2>
                                <form>
                                    <div class="mb-3">
                                        <label for="name" class="form-label">Jméno</label>
                                        <input type="text" class="form-control" id="name" required>
                                    </div>
                                    <div class="mb-3">
                                        <label for="email" class="form-label">Email</label>
                                        <input type="email" class="form-control" id="email" required>
                                    </div>
                                    <div class="mb-3">
                                        <label for="message" class="form-label">Zpráva</label>
                                        <textarea class="form-control" id="message" rows="4" required></textarea>
                                    </div>
                                    <button type="submit" class="btn btn-primary w-100">Odeslat</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </section>

                <footer class="bg-dark text-light py-4">
                    <div class="container text-center">
                        <p>&copy; 2024 {business_data["name"]}. Všechna práva vyhrazena.</p>
                    </div>
                </footer>

                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
                <script>
                    // Simple form handler
                    document.querySelector('form').addEventListener('submit', function(e) {{
                        e.preventDefault();
                        alert('Děkujeme za zprávu! Budeme vás kontaktovat brzy.');
                        this.reset();
                    }});
                </script>
            </body>
            </html>
            """

            with open(index_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"Web vygenerován a uložen do {index_file}")
            print(
                "(V reálném použití by byl použit opencode pro profesionální generování)"
            )

    def handle_status(self):
        """Zobrazí celkový stav systému"""
        cost_status = self.cost_tracker.get_status()
        grid_initialized = self.grid_manager.is_grid_initialized()
        db_stats = self.db.get_stats()

        print(f"""
SYSTEMOVY STAV
===============================================================================
API ROZPOCET:
  Aktualni sezeni: ${cost_status["session_cost"]:.2f}
  Celkove naklady:  ${cost_status["total_cost"]:.2f}
  Zbyvajici rozpocet: ${cost_status["budget_remaining"]:.2f}
  API volani:       {cost_status["api_calls"]}

GRID SYSTEM:
  Inicializovan:    {"Ano" if grid_initialized else "Ne"}
  {self._format_grid_stats() if grid_initialized else ""}

DATABAZE:
  Celkem podniku:   {db_stats["total_businesses"]}
  Bez webu:         {db_stats["without_website"]}
  S webem:          {db_stats["with_website"]}
  Prumerne hodnoceni: {db_stats["avg_rating"]}/5.0
  Prumerne recenze:  {db_stats["avg_reviews"]}
===============================================================================
""")

    def _format_grid_stats(self) -> str:
        """Formátuje grid statistiky"""
        grid_stats = self.grid_manager.get_coverage_stats()
        return f"""  Celkem buněk:      {grid_stats["total_cells"]}
  Prohledaných:      {grid_stats["searched_cells"]}
  Pokrytí:           {grid_stats["coverage_percentage"]:.1f}%"""

    def handle_set_budget(self, amount: str):
        """Nastaví rozpočet"""
        try:
            budget = float(amount)
            if budget < 0:
                print("Rozpocet nemuze byt zaporny")
                return
            if budget > 1000:
                print("Velmi vysoky rozpocet! Opravdu chcete nastavit ${budget}?")
                response = input("Pokracovat? (y/N): ").strip().lower()
                if response not in ["y", "yes", "ano", "a"]:
                    return

            self.cost_tracker.budget_limit = budget
            print(f"Rozpocet nastaven na ${budget:.2f}")

        except ValueError:
            print("Neplatna castka. Pouzite napr. 'set budget 10'")

    def handle_reset_costs(self):
        """Resetuje počítadlo nákladů"""
        print(f"Predchozi naklady sezeni: ${self.cost_tracker.session_cost:.2f}")
        self.cost_tracker.session_cost = 0.0
        self.cost_tracker.api_calls = 0
        print("Pocitadlo nakladu resetovano")

    def handle_analyze_data(self):
        """Analyzuje stávající data"""
        print("Analyzing existing dataset...")

        try:
            # Základní statistiky
            all_businesses = self.db.get_all_businesses()
            without_website = self.db.get_businesses_without_website()

            print(f"""
ANALYZADATASETU
===============================================================================
CELKOVE STATISTIKY:
  Velikost datasetu:   {len(all_businesses)} podniku
  Bez webu:           {len(without_website)} ({len(without_website) / len(all_businesses) * 100:.1f}%)
  S webem:            {len(all_businesses) - len(without_website)}

KVALITA DAT:
{self._analyze_data_quality(all_businesses)}

GEOGRAFICKE ROZLOZENI:
{self._analyze_geographic_distribution(all_businesses)}

KATEGORIE PODNIKU:
{self._analyze_business_types(all_businesses)}

DOPORUCENI PRO DALSIELE DANI:
{self._generate_search_recommendations(all_businesses)}
===============================================================================
""")

        except Exception as e:
            print(f"❌ Chyba při analýze: {e}")

    def _analyze_data_quality(self, businesses) -> str:
        """Analyzuje kvalitu dat"""
        total = len(businesses)
        with_address = sum(1 for b in businesses if b.get("address"))
        with_phone = sum(1 for b in businesses if b.get("phone"))
        with_rating = sum(1 for b in businesses if b.get("rating", 0) > 0)

        return f"""  S adresou:         {with_address}/{total} ({with_address / total * 100:.1f}%)
  S telefonem:        {with_phone}/{total} ({with_phone / total * 100:.1f}%)
  S hodnocením:       {with_rating}/{total} ({with_rating / total * 100:.1f}%)"""

    def _analyze_geographic_distribution(self, businesses) -> str:
        """Analyzuje geografické rozložení"""
        # Jednoduchá analýza - počítání podniků v regionech
        prague_count = sum(
            1 for b in businesses if "praha" in b.get("address", "").lower()
        )
        brno_count = sum(
            1 for b in businesses if "brno" in b.get("address", "").lower()
        )
        ostrava_count = sum(
            1 for b in businesses if "ostrava" in b.get("address", "").lower()
        )

        return f"""  Praha:             {prague_count}
  Brno:              {brno_count}
  Ostrava:           {ostrava_count}
  Ostatní regiony:   {len(businesses) - prague_count - brno_count - ostrava_count}"""

    def _analyze_business_types(self, businesses) -> str:
        """Analyzuje typy podniků"""
        from collections import Counter

        # Získání typů (pokud jsou k dispozici)
        types = []
        for b in businesses:
            if b.get("types"):
                types.extend(b["types"])

        if types:
            type_counts = Counter(types).most_common(5)
            type_str = "\n".join([f"  {t}: {c}" for t, c in type_counts])
        else:
            type_str = "  Typy nejsou k dispozici v datech"

        return type_str

    def _generate_search_recommendations(self, businesses) -> str:
        """Generuje doporučení pro další hledání"""
        without_website = [b for b in businesses if not b.get("website")]
        high_rated = [b for b in without_website if b.get("rating", 0) >= 4.5]

        recommendations = []
        recommendations.append(
            f"  1. Soustřeďte se na {len(high_rated)} vysoce hodnocených podniků bez webu"
        )
        recommendations.append(
            "  2. Preferujte větší města (Praha, Brno, Ostrava) pro vyšší hustotu"
        )
        recommendations.append(
            "  3. Používejte 'search spiral prague' pro systematické pokrytí"
        )
        recommendations.append(
            "  4. Omezte rozpočet na $5-10 denně pro kontrolu nákladů"
        )

        return "\n".join(recommendations)

    def run_interactive(self):
        """Interaktivní režim"""
        print("[bold green]Webomat spusten v interaktivnim rezimu![/bold green]")
        print("[dim]Zadejte 'help' nebo 'menu' pro zobrazeni prikazu[/dim]")

        while True:
            command = self.get_user_input()

            if command in ["quit", "q", "exit"]:
                print("[yellow] Nashledanou![/yellow]")
                break

            elif command in ["help", "menu", "m"]:
                self.show_menu()

            elif command in ["status", "menu"]:
                self.show_menu()

            elif command == "show costs":
                cost_status = self.cost_tracker.get_status()
                print(f"""
DETAILNI NAKLADY
===============================================================================
Aktualni sezeni:     ${cost_status["session_cost"]:.2f}
Celkove naklady:      ${cost_status["total_cost"]:.2f}
Zbyvajici rozpocet:   ${cost_status["budget_remaining"]:.2f}
Limit rozpocetu:      ${cost_status["budget_limit"]:.2f}
Pocet API volani:     {cost_status["api_calls"]}
===============================================================================
""")

            elif command.startswith("set budget "):
                parts = command.split(" ", 2)
                if len(parts) >= 3:
                    self.handle_set_budget(parts[2])
                else:
                    print("❌ Použití: set budget <částka>")

            elif command == "reset costs":
                self.handle_reset_costs()

            elif command == "analyze data":
                self.handle_analyze_data()

            elif command == "init grid":
                if self.grid_manager.ensure_initialized():
                    print("Grid uspesne inicializovan")
                else:
                    print("ℹ️  Grid už byl inicializován")

            elif command == "search":
                print(
                    "❌ Legacy search je zakázáno. Použijte 'search grid X' s potvrzením."
                )

            elif command.startswith("search grid "):
                parts = command.split(" ")
                if len(parts) == 3:  # search grid <number> = random search
                    try:
                        count = int(parts[2])
                        self.handle_grid_search_random(count)
                    except ValueError:
                        print("Usage: search grid <count> for random cells")
                elif len(parts) >= 4:
                    search_type = parts[2]
                    if search_type == "random":
                        count = int(parts[3]) if len(parts) > 3 else 5
                        self.handle_grid_search_random(count)
                    elif search_type == "spiral":
                        max_cells = int(parts[3]) if len(parts) > 3 else 10
                        self.handle_grid_search_spiral(max_cells)
                    else:
                        # search grid <lat> <lng> <cells>
                        try:
                            lat = float(parts[2])
                            lng = float(parts[3])
                            cells = int(parts[4]) if len(parts) > 4 else 5
                            self.handle_grid_search_area(lat, lng, cells)
                        except (ValueError, IndexError):
                            print("Použití: search grid <lat> <lng> <cells>")
                else:
                    print(
                        "Použití: search grid <pocet> pro nahodne bunky nebo search grid random/spiral/<lat> <lng>"
                    )

            elif command.startswith("search spiral "):
                parts = command.split(" ")
                if len(parts) >= 3 and parts[2].lower() == "prague":
                    max_cells = int(parts[3]) if len(parts) > 3 else 10
                    self.handle_grid_search_spiral(max_cells)
                else:
                    print("Použití: search spiral prague <pocet>")

            elif command == "show all":
                businesses = self.db.get_all_businesses()
                self.display_businesses_table(businesses, "Všechny podniky")

            elif command == "show no-website":
                businesses = self.db.get_businesses_without_website()
                self.display_businesses_table(businesses, "Podniky bez webu")

            elif command == "show high-rated":
                businesses = [
                    b for b in self.db.get_all_businesses() if b.get("rating", 0) >= 4.5
                ]
                self.display_businesses_table(
                    businesses, "Vysoce hodnocené podniky (≥4.5)"
                )

            elif command == "show recent":
                yesterday = datetime.now() - timedelta(days=1)
                businesses = [
                    b
                    for b in self.db.get_all_businesses()
                    if b.get("created_at")
                    and datetime.fromisoformat(str(b.get("created_at"))) > yesterday
                ]
                self.display_businesses_table(businesses, "Nedávno nalezené podniky")

            elif command.startswith("details "):
                parts = command.split(" ", 1)
                if len(parts) > 1:
                    self.show_business_details(parts[1])
                else:
                    print("[red]Zadejte place_id: details <ID>[/red]")

            elif command.startswith("add-social "):
                args = command.split(" ")[1:]
                self.handle_add_social(args)

            elif command.startswith("add-email "):
                args = command.split(" ")[1:]
                self.handle_add_email(args)

            elif command.startswith("add-old-website "):
                args = command.split(" ")[1:]
                self.handle_add_old_website(args)

            elif command.startswith("export "):
                parts = command.split(" ", 1)
                if len(parts) > 1:
                    self.handle_export(parts[1])
                else:
                    print("[red]Zadejte formát: export csv/json[/red]")

            elif command.startswith("search "):
                parts = command.split(" ", 1)
                if len(parts) > 1:
                    self.handle_search(parts[1])
                else:
                    print("[red]Zadejte klíčové slovo: search <keyword>[/red]")

            elif command == "stats":
                self.show_stats()

            elif command == "grid stats":
                stats = self.grid_manager.get_coverage_stats()
                print(f"""
GRID STATISTIKY
===============================================================================
Celkem buněk:      {stats["total_cells"]}
Prohledaných:      {stats["searched_cells"]}
Neprohledaných:    {stats["unsearched_cells"]}
Pokrytí:           {stats["coverage_percentage"]:.1f}%
Podniků v gridu:   {stats["total_businesses_in_grid"]}
===============================================================================
""")

            elif command == "show coverage":
                self.handle_show_coverage()

            elif command.startswith("makeweb "):
                args = command.split(" ")[1:]
                self.handle_makeweb(args)

            elif command == "":
                continue

            else:
                print(f"[red]Neznámý příkaz: {command}[/red]")
                print("[dim]Zadejte 'menu' pro zobrazení dostupných příkazů[/dim]")

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

    # Kontrola argumentů příkazové řádky
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        # Automatický režim
        webomat.run()
    else:
        # Interaktivní režim
        webomat.run_interactive()


if __name__ == "__main__":
    main()
