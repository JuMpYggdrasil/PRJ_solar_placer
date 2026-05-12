from __future__ import annotations
import requests


class ApiClient:
    """HTTP client for the backend API — no direct backend imports."""

    def __init__(self, base_url: str = "http://127.0.0.1:8765"):
        self.base_url = base_url
        self._session = requests.Session()

    def _post(self, path: str, body: dict = None) -> dict:
        r = self._session.post(f"{self.base_url}{path}", json=body or {}, timeout=10)
        r.raise_for_status()
        return r.json()

    def _get(self, path: str) -> dict:
        r = self._session.get(f"{self.base_url}{path}", timeout=10)
        r.raise_for_status()
        return r.json()

    # ── Health ──

    def health(self) -> dict:
        return self._get("/api/health")

    # ── Constants ──

    def get_constants(self) -> dict:
        return self._get("/api/constants")

    # ── Panel types ──

    def get_panel_types(self) -> list[dict]:
        return self._get("/api/panel-types")

    def get_panel(self, name: str) -> dict:
        return self._post("/api/panel/get", {"name": name})

    # ── Panel arrangement ──

    def arrange(self, solar_array: dict, prohibited_sets: list) -> dict:
        return self._post("/api/panel/arrange", {
            "solar_array": solar_array,
            "prohibited_sets": prohibited_sets,
        })

    def setback_rect(self, solar_array: dict) -> dict | None:
        return self._post("/api/panel/setback-rect", {"solar_array": solar_array})

    def bounding_rect(self, solar_array: dict) -> dict | None:
        return self._post("/api/panel/bounding-rect", {"solar_array": solar_array})

    # ── Geometry ──

    def pixel_distance(self, p1: tuple, p2: tuple) -> float:
        return self._post("/api/geometry/pixel-distance", {
            "p1": list(p1), "p2": list(p2),
        })["distance"]

    def area_square_meters(self, points: list, scale_factor: float) -> float:
        return self._post("/api/geometry/area", {
            "points": points, "scale_factor": scale_factor,
        })["area"]

    def distance_meters(self, p1: tuple, p2: tuple, scale_factor: float) -> float:
        return self._post("/api/geometry/distance", {
            "p1": list(p1), "p2": list(p2), "scale_factor": scale_factor,
        })["distance"]

    def point_in_polygon(self, x: float, y: float, polygon: list) -> bool:
        return self._post("/api/geometry/point-in-polygon", {
            "x": x, "y": y, "polygon": polygon,
        })["inside"]
