"""
Statistics utility functions for Streamlit app
"""

import pandas as pd
from typing import Dict, List
from utils.database import db, grid_manager


def get_dashboard_stats() -> Dict:
    """Get comprehensive dashboard statistics"""
    try:
        # Business statistics
        all_businesses = db.get_all_businesses()
        businesses_with_website = [
            b for b in all_businesses if b.get("has_website", False)
        ]
        businesses_without_website = [
            b for b in all_businesses if not b.get("has_website", False)
        ]

        # Calculate rating statistics
        ratings = [b.get("rating", 0) for b in all_businesses if b.get("rating")]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0

        # Grid coverage statistics
        grid_stats = grid_manager.get_coverage_stats()

        # Recent activity (last 24 hours)
        # This would require timestamp analysis, simplified for now
        recent_businesses = len(all_businesses)  # Placeholder

        return {
            "total_businesses": len(all_businesses),
            "businesses_with_website": len(businesses_with_website),
            "businesses_without_website": len(businesses_without_website),
            "avg_rating": round(avg_rating, 1),
            "coverage_percentage": grid_stats.get("coverage_percentage", 0),
            "total_cells": grid_stats.get("total_cells", 0),
            "searched_cells": grid_stats.get("searched_cells", 0),
            "recent_businesses": recent_businesses,
        }
    except Exception as e:
        # Return default values if there's an error
        return {
            "total_businesses": 0,
            "businesses_with_website": 0,
            "businesses_without_website": 0,
            "avg_rating": 0,
            "coverage_percentage": 0,
            "total_cells": 0,
            "searched_cells": 0,
            "recent_businesses": 0,
        }


def get_business_dataframe(businesses: List[Dict]) -> pd.DataFrame:
    """Convert businesses list to pandas DataFrame for display"""
    if not businesses:
        return pd.DataFrame()

    df = pd.DataFrame(businesses)

    # Select and rename columns
    columns_mapping = {
        "id": "ID",
        "name": "Name",
        "address": "Address",
        "rating": "Rating",
        "review_count": "Reviews",
        "has_website": "Has Website",
        "phone": "Phone",
        "website": "Website",
        "facebook_id": "Facebook ID",
        "created_at": "Created At",
    }

    # Filter for available columns
    available_columns = {k: v for k, v in columns_mapping.items() if k in df.columns}

    if available_columns:
        df = df[available_columns.keys()]
        df.columns = available_columns.values()

    # Format values
    if "Rating" in df.columns:
        df["Rating"] = df["Rating"].round(1)

    if "Has Website" in df.columns:
        df["Has Website"] = df["Has Website"].map({True: "Yes", False: "No"})

    return df


def get_facebook_businesses() -> List[Dict]:
    """Get businesses that have Facebook pages"""
    all_businesses = db.get_all_businesses()
    return [
        b
        for b in all_businesses
        if b.get("facebook_id")
        or (b.get("website") and "facebook.com" in b.get("website", "").lower())
    ]


def get_high_rated_businesses(min_rating: float = 4.5) -> List[Dict]:
    """Get businesses with ratings above threshold"""
    all_businesses = db.get_all_businesses()
    return [b for b in all_businesses if b.get("rating", 0) >= min_rating]
