from __future__ import annotations
from typing import NamedTuple, Optional
import cv2
import numpy as np
from ..models.solar_array import SolarArray
from ..services.geometry_service import GeometryService


class ArrangementResult(NamedTuple):
    total_count: int
    horizontal_count: int
    vertical_count: int
    intersect_keepout_count: int
    kWp: float
    positions: list[tuple[float, float]]  # centers of placed panels


class PanelArranger:
    """Computes panel grid placement inside a rotated rectangle."""

    def __init__(self):
        self.geo = GeometryService()

    def arrange(
        self,
        solar_array: SolarArray,
        keepout_sets: list[list[tuple[float, float]]],
    ) -> ArrangementResult:
        if not solar_array.panel_type or len(solar_array.panel_points) < 4:
            return ArrangementResult(0, 0, 0, 0, 0, [])

        points = np.array(solar_array.panel_points[-4:], dtype=np.int32)
        rect = cv2.minAreaRect(points)
        center, size, angle = rect
        size = tuple(s - 2 * solar_array.setback_length for s in size)

        small_rect_size = solar_array.small_rect_size
        if small_rect_size is None:
            return ArrangementResult(0, 0, 0, 0, 0, [])

        gap_size = solar_array.gap_size
        if gap_size is None:
            return ArrangementResult(0, 0, 0, 0, 0, [])

        small_rect_width, small_rect_height = small_rect_size
        big_gap_width, big_gap_height, small_gap_width, small_gap_height, gap_width, gap_height = gap_size

        w, h = size

        num_h = int(w / (small_rect_width + gap_width))
        num_v = int(h / (small_rect_height + gap_height))

        if num_h <= 0 or num_v <= 0:
            return ArrangementResult(0, 0, 0, 0, 0, [])

        space_w = w - (num_h * (small_rect_width + gap_width) - gap_width)
        space_h = h - (num_v * (small_rect_height + gap_height) - gap_height)

        intersection_count = 0
        placed_centers: list[tuple[float, float]] = []

        for i in range(num_h):
            for j in range(num_v):
                if i % 2 == 0:
                    x_off = i * (small_rect_width + gap_width)
                else:
                    x_off = i * (small_rect_width + gap_width) + (small_gap_width - big_gap_width) / 2

                if j % 2 == 0:
                    y_off = j * (small_rect_height + gap_height)
                else:
                    y_off = j * (small_rect_height + gap_height) + (small_gap_height - big_gap_height) / 2

                rx, ry = self.geo.rotate_point(
                    center[0] - w / 2 + small_rect_width / 2 + gap_width / 2 + space_w / 2 + x_off,
                    center[1] - h / 2 + small_rect_height / 2 + gap_height / 2 + space_h / 2 + y_off,
                    center[0], center[1], angle,
                )

                each_center = (float(rx), float(ry))
                small_rect_data = (each_center, small_rect_size, angle)

                collides = False
                if keepout_sets:
                    for prohibited in keepout_sets:
                        if len(prohibited) < 4:
                            continue
                        prohibited_pts = np.array(prohibited[-4:], dtype=np.int32)
                        prohibited_rect = cv2.minAreaRect(prohibited_pts)
                        intersection = cv2.rotatedRectangleIntersection(small_rect_data, prohibited_rect)
                        if intersection[1] is not None:
                            intersection_count += 1
                            collides = True
                            break

                if not collides:
                    placed_centers.append(each_center)

        total_panels = num_h * num_v - intersection_count
        panel_power = solar_array.panel_type.power_W
        kWp = panel_power * total_panels / 1000.0

        return ArrangementResult(
            total_count=total_panels,
            horizontal_count=num_h,
            vertical_count=num_v,
            intersect_keepout_count=intersection_count,
            kWp=kWp,
            positions=placed_centers,
        )

    def get_bounding_rect(
        self, solar_array: SolarArray
    ) -> Optional[tuple[tuple[float, float], tuple[float, float], float]]:
        if len(solar_array.panel_points) < 4:
            return None
        pts = np.array(solar_array.panel_points[-4:], dtype=np.int32)
        rect = cv2.minAreaRect(pts)
        return rect  # (center, size, angle)

    def get_setback_rect(
        self, solar_array: SolarArray
    ) -> Optional[tuple[tuple[float, float], tuple[float, float], float]]:
        rect = self.get_bounding_rect(solar_array)
        if rect is None:
            return None
        center, size, angle = rect
        size = tuple(s - 2 * solar_array.setback_length for s in size)
        return (center, size, angle)
