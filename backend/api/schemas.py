from pydantic import BaseModel


class PanelInfoData(BaseModel):
    name: str
    power_W: int
    width_m: float
    height_m: float
    model_str: str


class SolarArrayData(BaseModel):
    panel_points: list[list[float]]
    setback_length: float = 0
    gap_size: list[float] | None = None
    small_rect_size: list[float] | None = None
    panel_rotation_tick: int = 0
    walk_gap_rotation_tick: int = 0
    panel_type: PanelInfoData | None = None


class RectResult(BaseModel):
    center: list[float]
    size: list[float]
    angle: float
    corners: list[list[float]]


class ArrangeResult(BaseModel):
    total_count: int
    horizontal_count: int
    vertical_count: int
    intersect_keepout_count: int
    kWp: float
    angle: float
    positions: list[list[float]]
    panel_corners: list[list[list[float]]]


class ConstantsData(BaseModel):
    REFERENCE_ZOOM_IN: int = 3
