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
                    # Vytvoření adresářové struktury
                    self.db.create_business_folder(business_data)
                else:
                    self.logger.error(f"Nepodařilo uložit: {business_data['name']}")

            # Rate limiting
            time.sleep(REQUEST_DELAY)

    def show_menu(self):
        """Zobrazí hlavní menu"""
        menu_text = """
================================================================================
                           WEBOMAT - Console Interface
               Automaticke hledani podniku bez webovych stranek
================================================================================

Priklady:
--------------------------------------------------------------------------------
search                - Spusti hledani novych podniku
show all              - Zobrazi vsechny podniky
show no-website       - Jen podniky bez webu
show high-rated       - Podniky s hodnocenim >= 4.5
show recent           - Podniky nalezene v poslednich 24h
details <ID>          - Detailni informace o podniku
add-email <ID>        - Pridat email komunikaci
add-social <ID>       - Pridat socialni sit
add-old-website <ID>  - Oznacit stary web
export csv            - Export do CSV
export json           - Export do JSON
stats                 - Statistiky databaze
search <keyword>      - Hledani v databazi
quit                  - Ukoncit program

================================================================================
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

        for i, business in enumerate(businesses, 1):
            name = business.get("name", "N/A")[:24]
            address = business.get("address", "N/A")[:29]
            rating = (
                f"{business.get('rating', 0):.1f}" if business.get("rating") else "N/A"
            )
            reviews = str(business.get("review_count", 0))
            has_website = "ANO" if business.get("website") else "NE"
            phone = (
                business.get("phone", "N/A")[:14] if business.get("phone") else "N/A"
            )

            table_data.append(
                [str(i), name, address, rating, reviews, has_website, phone]
            )

        print(tabulate(table_data, headers=headers, tablefmt="grid"))

    def show_business_details(self, place_id: str):
        """Zobrazí detailní informace o podniku"""
        business = self.db.get_business_by_place_id(place_id)
        if not business:
            print(f"[red]Podnik s ID {place_id} nebyl nalezen[/red]")
            return

        # Základní informace
        details_text = f"""
{business.get("name", "N/A")}
Adresa: {business.get("address", "N/A")}
Hodnoceni: {business.get("rating", "N/A")}/5.0
Recenzi: {business.get("review_count", "N/A")}
Telefon: {business.get("phone", "N/A")}
Web: {business.get("website", "Zadny")}
Place ID: {place_id}
Vytvoreno: {business.get("created_at", "N/A")}
"""

        print(details_text)

        # Sociální sítě
        social_media = self.db.get_social_media(place_id)
        if social_media:
            print("Socialni site:")
            for platform, data in social_media.items():
                print(
                    f"  {platform}: {data.get('url', 'N/A')} ({data.get('notes', '')})"
                )

        # Starý web
        old_website = self.db.get_old_website_info(place_id)
        if old_website:
            old_web_text = f"""
 [bold red]Starý web nalezen:[/bold red]
 {old_website.get("url", "N/A")}
 Analýza: {old_website.get("analysis", {}).get("status", "N/A")}
"""
            print(old_web_text)

        # Email komunikace
        emails = self.db.get_email_communications(place_id)
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

            elif command == "search":
                self.run()

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
