#!/usr/bin/env python3
"""
Test script for grid initialization
"""

from grid_manager import GridManager
from database import DatabaseManager

if __name__ == "__main__":
    print("Testing grid initialization...")

    # Check if grid already exists
    db = DatabaseManager()
    existing_cells = db.get_all_grid_cells()
    if existing_cells:
        print(f"Grid already exists with {len(existing_cells)} cells")
        stats = db.get_grid_coverage_stats()
        print("Stats:", stats)
    else:
        print("Initializing grid...")
        gm = GridManager(db)
        stats = gm.get_coverage_stats()
        print("Stats:", stats)
