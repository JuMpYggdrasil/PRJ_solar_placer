from __future__ import annotations
import json
import os
from typing import Optional
from .constants import Constants


class JsonRepository:
    """Read/write runtime configuration to parameter.json."""

    def __init__(self, filepath: str = Constants.JSON_FILE_PATH):
        self.filepath = filepath

    def _ensure_exists(self) -> dict:
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_lat_lng(self) -> tuple[float, float]:
        data = self._ensure_exists()
        lat = data.get("latitude", Constants.DEFAULT_LATITUDE)
        lng = data.get("longitude", Constants.DEFAULT_LONGITUDE)
        return float(lat), float(lng)

    def save_lat_lng(self, lat: float, lng: float) -> None:
        data = self._ensure_exists()
        data["latitude"] = lat
        data["longitude"] = lng
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_thai_pv_data(self) -> list[dict]:
        data = self._ensure_exists()
        return data.get("thai_pv_zipcode", [])

    def find_nearest_location(
        self, user_lat: float, user_lng: float, locations: list[dict]
    ) -> Optional[dict]:
        from ..services.geometry_service import GeometryService

        geo = GeometryService()
        min_dist = float("inf")
        nearest = None
        for loc in locations:
            d = geo.haversine(user_lat, user_lng, loc["lat"], loc["lng"])
            if d < min_dist:
                min_dist = d
                nearest = loc
        return nearest
