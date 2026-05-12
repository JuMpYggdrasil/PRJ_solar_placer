from __future__ import annotations
import math


class GeometryService:
    """Pure math utilities — no tkinter dependency."""

    @staticmethod
    def rotate_point(
        x: float, y: float,
        center_x: float, center_y: float,
        angle_deg: float
    ) -> tuple[float, float]:
        angle_rad = math.radians(angle_deg)
        rx = center_x + (x - center_x) * math.cos(angle_rad) - (y - center_y) * math.sin(angle_rad)
        ry = center_y + (x - center_x) * math.sin(angle_rad) + (y - center_y) * math.cos(angle_rad)
        return rx, ry

    @staticmethod
    def polygon_area(points: list[tuple[float, float]]) -> float:
        area = 0.0
        n = len(points)
        for i in range(n - 1):
            area += points[i][0] * points[i + 1][1] - points[i + 1][0] * points[i][1]
        area += points[-1][0] * points[0][1] - points[0][0] * points[-1][1]
        return abs(area) / 2.0

    @staticmethod
    def pixel_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    @staticmethod
    def distance_meters(
        p1: tuple[float, float],
        p2: tuple[float, float],
        scale_factor: float
    ) -> float:
        return GeometryService.pixel_distance(p1, p2) * scale_factor

    @staticmethod
    def area_square_meters(points: list[tuple[float, float]], scale_factor: float) -> float:
        return GeometryService.polygon_area(points) * (scale_factor ** 2)

    @staticmethod
    def haversine(
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2
             + math.cos(math.radians(lat1))
             * math.cos(math.radians(lat2))
             * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @staticmethod
    def bound(low: float, high: float, value: float) -> float:
        return max(low, min(high, value))

    @staticmethod
    def point_in_polygon(
        x: float, y: float,
        polygon: list[tuple[float, float]]
    ) -> bool:
        inside = False
        n = len(polygon)
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xints:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    @staticmethod
    def compute_rotated_rect_corners(
        center: tuple[float, float],
        size: tuple[float, float],
        angle_deg: float,
        scaled: float = 1.0
    ) -> list[tuple[float, float]]:
        w, h = size
        w *= scaled
        h *= scaled
        cx, cy = center
        rad = math.radians(angle_deg)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        x1 = cx - w / 2 * cos_a - h / 2 * sin_a
        y1 = cy - w / 2 * sin_a + h / 2 * cos_a
        x2 = cx + w / 2 * cos_a - h / 2 * sin_a
        y2 = cy + w / 2 * sin_a + h / 2 * cos_a
        x3 = cx + w / 2 * cos_a + h / 2 * sin_a
        y3 = cy + w / 2 * sin_a - h / 2 * cos_a
        x4 = cx - w / 2 * cos_a + h / 2 * sin_a
        y4 = cy - w / 2 * sin_a - h / 2 * cos_a

        return [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]
