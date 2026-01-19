"""
Grid Manager pro systematické pokrytí ČR
"""

import math
import sqlite3
from typing import List, Dict, Tuple, Optional
from shapely.geometry import Point, Polygon
from pyproj import Transformer
import random
from database import DatabaseManager


class GridManager:
    """Správce grid systému pro pokrytí ČR"""

    # Hranice ČR (přibližné)
    CZ_BOUNDS = {"west": 12.09, "east": 18.85, "north": 51.06, "south": 48.55}

    # Velikost buňky v metrech
    CELL_SIZE_METERS = 2000

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.transformer_to_metric = Transformer.from_crs(
            "EPSG:4326", "EPSG:3857", always_xy=True
        )
        self.transformer_to_latlon = Transformer.from_crs(
            "EPSG:3857", "EPSG:4326", always_xy=True
        )

        # NO auto-initialization - only when explicitly requested

    def is_grid_initialized(self) -> bool:
        """Check if grid has been initialized"""
        cells = self.db.get_all_grid_cells()
        return len(cells) > 0

    def ensure_initialized(self, force: bool = False) -> bool:
        """Initialize grid only if needed"""
        if not self.is_grid_initialized() or force:
            print("🔄 Initializing grid system for ČR...")
            self.initialize_grid()
            print(
                f"Grid initialized with {self.get_coverage_stats()['total_cells']} cells"
            )
            return True
        else:
            print("Grid already initialized")
            return False

    def latlon_to_metric(self, lng: float, lat: float) -> Tuple[float, float]:
        """Převede lat/lon na metrické souřadnice"""
        return self.transformer_to_metric.transform(lng, lat)

    def metric_to_latlon(self, x: float, y: float) -> Tuple[float, float]:
        """Převede metrické souřadnice na lat/lon"""
        lng, lat = self.transformer_to_latlon.transform(x, y)
        return lat, lng

    def get_grid_cell_bounds(
        self, center_lat: float, center_lng: float
    ) -> Dict[str, float]:
        """Vrátí hranice grid buňky pro dané centrum"""
        # Převod na metrické
        center_x, center_y = self.latlon_to_metric(center_lng, center_lat)

        # Velikost buňky
        half_size = self.CELL_SIZE_METERS / 2

        # Hranice v metrických
        min_x = center_x - half_size
        max_x = center_x + half_size
        min_y = center_y - half_size
        max_y = center_y + half_size

        # Převod zpět na lat/lon
        lat_min, lng_min = self.metric_to_latlon(min_x, min_y)
        lat_max, lng_max = self.metric_to_latlon(max_x, max_y)

        return {
            "lat_min": lat_min,
            "lng_min": lng_min,
            "lat_max": lat_max,
            "lng_max": lng_max,
            "lat_center": center_lat,
            "lng_center": center_lng,
        }

    def initialize_grid(self):
        """Inicializuje grid buňky pro celou ČR"""
        print("Inicializace grid systému pro ČR...")

        # Vypočítání počtu buněk
        west_x, south_y = self.latlon_to_metric(
            self.CZ_BOUNDS["west"], self.CZ_BOUNDS["south"]
        )
        east_x, north_y = self.latlon_to_metric(
            self.CZ_BOUNDS["east"], self.CZ_BOUNDS["north"]
        )

        # Počet buněk ve směru X a Y
        num_cells_x = math.ceil((east_x - west_x) / self.CELL_SIZE_METERS)
        num_cells_y = math.ceil((north_y - south_y) / self.CELL_SIZE_METERS)

        print(f"Grid rozměry: {num_cells_x} x {num_cells_y} buněk")

        # Generování buněk s batch operations
        cells_created = 0
        batch_size = 1000
        batch_data = []

        for i in range(num_cells_x):
            if i % 20 == 0:
                print(f"Processing row {i}/{num_cells_x}...")

            for j in range(num_cells_y):
                # Střed buňky v metrických
                center_x = (
                    west_x + i * self.CELL_SIZE_METERS + self.CELL_SIZE_METERS / 2
                )
                center_y = (
                    south_y + j * self.CELL_SIZE_METERS + self.CELL_SIZE_METERS / 2
                )

                # Převod na lat/lon
                center_lat, center_lng = self.metric_to_latlon(center_x, center_y)

                # Získání hranic buňky
                bounds = self.get_grid_cell_bounds(center_lat, center_lng)

                # Přidat do batch
                batch_data.append(
                    (
                        bounds["lat_center"],
                        bounds["lng_center"],
                        bounds["lat_min"],
                        bounds["lng_min"],
                        bounds["lat_max"],
                        bounds["lng_max"],
                    )
                )

                # Commit batch každých 1000 buněk
                if len(batch_data) >= batch_size:
                    self._commit_batch(batch_data)
                    cells_created += len(batch_data)
                    print(
                        f"Committed {cells_created}/{num_cells_x * num_cells_y} cells"
                    )
                    batch_data = []

        # Commit zbývající data
        if batch_data:
            self._commit_batch(batch_data)
            cells_created += len(batch_data)

        print(f"Vytvoreno {cells_created} grid bunek")

    def _commit_batch(self, batch_data):
        """Batch insert pro rychlejší operace"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    """
                    INSERT OR IGNORE INTO grid_cells
                    (lat_center, lng_center, lat_min, lng_min, lat_max, lng_max)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    batch_data,
                )
                conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def get_random_unsearched_cells(self, count: int = 5) -> List[Dict]:
        """Vrátí náhodné neprohledané buňky"""
        return self.db.get_unsearched_grid_cells(count)

    def get_spiral_cells(
        self, center_lat: float, center_lng: float, max_cells: int = 20
    ) -> List[Dict]:
        """Vrátí buňky ve spirále od centra"""
        # Najdi nejbližší grid buňku k centru
        center_cell = self.get_cell_at_location(center_lat, center_lng)
        if not center_cell:
            return []

        # Získaj všechny buňky
        all_cells = self.db.get_all_grid_cells()

        # Spočítej vzdálenosti a seřaď
        cells_with_distance = []
        for cell in all_cells:
            distance = self.haversine_distance(
                center_lat, center_lng, cell["lat_center"], cell["lng_center"]
            )
            cells_with_distance.append((cell, distance))

        # Seřaď podle vzdálenosti
        cells_with_distance.sort(key=lambda x: x[1])

        # Vrátí prvních max_cells
        return [cell for cell, dist in cells_with_distance[:max_cells]]

    def get_cell_at_location(self, lat: float, lng: float) -> Optional[Dict]:
        """Najde grid buňku pro danou lokaci"""
        # Najdi nejbližší buňku
        all_cells = self.db.get_all_grid_cells()
        if not all_cells:
            return None

        min_distance = float("inf")
        closest_cell = None

        for cell in all_cells:
            distance = self.haversine_distance(
                lat, lng, cell["lat_center"], cell["lng_center"]
            )
            if distance < min_distance:
                min_distance = distance
                closest_cell = cell

        return closest_cell

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Vypočítá Haversine vzdálenost v kilometrech"""
        R = 6371  # Radius Země v km

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def mark_cell_searched(self, cell_id: int, business_count: int) -> None:
        """Označí buňku jako prohledanou"""
        self.db.update_grid_cell_searched(cell_id, business_count)

    def add_business_to_cell(self, cell_id: int, place_id: str) -> None:
        """Přidá podnik do buňky"""
        self.db.add_business_to_grid_cell(cell_id, place_id)

    def get_coverage_stats(self):
        """Vrátí statistiky pokrytí"""
        return self.db.get_grid_coverage_stats()
