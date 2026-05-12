from __future__ import annotations
import datetime
import math
import pytz
import numpy as np
import cv2
import pysolar
pysolar.use_math()
from pysolar.solar import get_altitude, get_azimuth
from ..models.solar_array import SolarArray
from .geometry_service import GeometryService


class ShadowService:
    """Computes shadow geometry using pysolar."""

    def __init__(self, timezone: str = "Asia/Bangkok"):
        self.tz = timezone
        self.geo = GeometryService()

    def compute_panel_shadow_points(
        self,
        date_input_str: str,
        solar_array: SolarArray,
        latitude: float,
        longitude: float,
        scale_factor: float,
    ) -> list[tuple[float, float]]:
        if len(solar_array.panel_points) < 4:
            return []

        elevation = solar_array.elevation
        local_dt = datetime.datetime.strptime(date_input_str, "%Y/%m/%d %H:%M:%S")
        utc_dt = local_dt.astimezone(pytz.utc)

        altitude = get_altitude(latitude, longitude, utc_dt)
        azimuth = get_azimuth(latitude, longitude, utc_dt)
        shadow_azimuth = azimuth + 90

        phi = math.radians(altitude) % (2 * math.pi)
        if abs(math.tan(phi)) < 1e-10:
            shadow_length = 0
        else:
            shadow_length = (elevation / math.tan(phi)) / scale_factor

        dx = shadow_length * math.cos(math.radians(shadow_azimuth))
        dy = shadow_length * math.sin(math.radians(shadow_azimuth))

        pts = solar_array.panel_points[-4:]
        return [
            (pts[0][0] + dx, pts[0][1] + dy),
            (pts[1][0] + dx, pts[1][1] + dy),
            (pts[2][0] + dx, pts[2][1] + dy),
            (pts[3][0] + dx, pts[3][1] + dy),
        ]

    def compute_tree_shadow(
        self,
        date_input_str: str,
        tree_center: tuple[float, float],
        tree_radius: float,
        tree_height: float,
        elevation: float,
        latitude: float,
        longitude: float,
        scale_factor: float,
    ) -> tuple[float, float, float]:
        local_dt = datetime.datetime.strptime(date_input_str, "%Y/%m/%d %H:%M:%S")
        utc_dt = local_dt.astimezone(pytz.utc)

        altitude = get_altitude(latitude, longitude, utc_dt)
        azimuth = get_azimuth(latitude, longitude, utc_dt)
        shadow_azimuth = azimuth + 90

        phi = math.radians(altitude) % (2 * math.pi)
        dh = self.geo.bound(0, 100, tree_height - elevation)

        if abs(math.tan(phi)) < 1e-10:
            shadow_length = 0
        else:
            shadow_length = (dh / math.tan(phi)) / scale_factor

        dx = shadow_length * math.cos(math.radians(shadow_azimuth))
        dy = shadow_length * math.sin(math.radians(shadow_azimuth))

        return (tree_center[0] + dx, tree_center[1] + dy, tree_radius)

    @staticmethod
    def convex_hull_points(
        shadow_points: list[tuple[float, float]]
    ) -> list[tuple[float, float]]:
        if len(shadow_points) <= 2:
            return []
        pts = np.array(shadow_points, dtype=np.int32)
        hull = cv2.convexHull(pts)
        return [(float(p[0][0]), float(p[0][1])) for p in hull]
