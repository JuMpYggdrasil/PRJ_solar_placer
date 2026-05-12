from __future__ import annotations
from typing import NamedTuple


class PanelInfo(NamedTuple):
    power_W: int
    width_m: float
    height_m: float
    model_str: str

    def __str__(self) -> str:
        return f"{self.power_W}W ({self.model_str})"
