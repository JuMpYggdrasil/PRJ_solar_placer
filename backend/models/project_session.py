from __future__ import annotations
from typing import Optional
from .solar_array import SolarArray


class ProjectSession:
    """Holds all mutable state for the current project."""

    def __init__(self):
        self.original_image_path: Optional[str] = None
        self.scale_factor: Optional[float] = None

        self.points: list = []                     # current drawing points (pre-calibration)
        self.reference_points: list = []           # calibration reference points
        self.prohibited_points: list = []          # current keepout drawing points
        self.tree_points: list = []                # current tree drawing points
        self.shadow_points: list = []              # computed shadow hull points

        self.active_array: SolarArray = SolarArray([])

        self.arrays: list[SolarArray] = []          # saved panel arrays
        self.prohibited_permanent_sets: list = []   # saved keepout zones
        self.tree_permanent_sets: list = []         # saved trees

        self.already_draw_panel: bool = False
        self.already_draw_shadow: bool = False

    @property
    def has_arrays(self) -> bool:
        return len(self.arrays) > 0

    @property
    def total_kWp(self) -> float:
        return sum(a.kWp for a in self.arrays) + self.active_array.kWp

    def add_array(self, array: SolarArray) -> None:
        self.arrays.append(array)

    def remove_array(self, index: int) -> SolarArray:
        return self.arrays.pop(index)

    def clear_all(self) -> None:
        self.points.clear()
        self.reference_points.clear()
        self.prohibited_points.clear()
        self.tree_points.clear()
        self.shadow_points.clear()
        self.active_array = SolarArray([])
        self.arrays.clear()
        self.prohibited_permanent_sets.clear()
        self.tree_permanent_sets.clear()
        self.already_draw_panel = False
        self.already_draw_shadow = False
