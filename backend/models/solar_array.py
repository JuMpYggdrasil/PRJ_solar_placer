from __future__ import annotations
import copy
from typing import Optional
from .panel_info import PanelInfo


class SolarArray:
    """Pure data model representing one solar panel array."""

    def __init__(self, panel_points: list):
        self.panel_points: list = panel_points
        self.total_panel_count: int = 0
        self.horizontal_panel_count: int = 0
        self.vertical_panel_count: int = 0
        self.intersect_keepout_count: int = 0
        self.kWp: float = 0
        self.azimuth_angle: float = 0

        self.panel_type: Optional[PanelInfo] = None
        self.tilt_angle: float = 0
        self.elevation: float = 0
        self.panel_rotation_tick: int = 0
        self.walk_gap_rotation_tick: int = 0
        self.setback_length: float = 0

        self.gap_size: Optional[tuple] = None
        self.small_rect_size: Optional[tuple] = None

        self._initial_state = (
            copy.deepcopy(panel_points), 0, 0, 0, 0, 0, 0,
            None, 0, 0, 0, 0, 0, None, None
        )

    def copy(self) -> SolarArray:
        return copy.deepcopy(self)

    def reset_to_initial_state(self) -> None:
        (self.panel_points, self.total_panel_count,
         self.horizontal_panel_count, self.vertical_panel_count,
         self.intersect_keepout_count, self.kWp,
         self.azimuth_angle, self.panel_type, self.tilt_angle,
         self.elevation, self.panel_rotation_tick,
         self.walk_gap_rotation_tick, self.setback_length,
         self.gap_size, self.small_rect_size) = copy.deepcopy(self._initial_state)
