from fastapi import FastAPI, HTTPException

from .schemas import (
    PanelInfoData, SolarArrayData, RectResult, ArrangeResult, ConstantsData,
)
from ..repositories.panel_repository import PanelRepository
from ..repositories.constants import Constants as C
from ..services.panel_arranger import PanelArranger
from ..services.geometry_service import GeometryService
from ..models.solar_array import SolarArray
from ..models.panel_info import PanelInfo

app = FastAPI(title="Solar Panel Backend API")

panel_repo = PanelRepository()
arranger = PanelArranger()
geo = GeometryService()


# ── helpers ──

def _to_solar_array(data: SolarArrayData) -> SolarArray:
    sa = SolarArray(data.panel_points)
    if data.panel_type:
        sa.panel_type = PanelInfo(
            power_W=data.panel_type.power_W,
            width_m=data.panel_type.width_m,
            height_m=data.panel_type.height_m,
            model_str=data.panel_type.model_str,
        )
    sa.setback_length = data.setback_length
    sa.gap_size = tuple(data.gap_size) if data.gap_size else None
    sa.small_rect_size = tuple(data.small_rect_size) if data.small_rect_size else None
    sa.panel_rotation_tick = data.panel_rotation_tick
    sa.walk_gap_rotation_tick = data.walk_gap_rotation_tick
    return sa


def _compute_corners(center, size, angle_deg, scaled=1.0):
    return [
        list(pt) for pt in GeometryService.compute_rotated_rect_corners(
            (center[0], center[1]), (size[0], size[1]), angle_deg, scaled,
        )
    ]


# ── endpoints ──

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/constants")
def get_constants():
    return ConstantsData(REFERENCE_ZOOM_IN=C.REFERENCE_ZOOM_IN)


@app.get("/api/panel-types")
def get_panel_types():
    return [
        PanelInfoData(name=name, power_W=p.power_W, width_m=p.width_m,
                      height_m=p.height_m, model_str=p.model_str)
        for name, p in panel_repo.get_all().items()
    ]


@app.post("/api/panel/get")
def get_panel(body: dict):
    name = body.get("name", "")
    p = panel_repo.get(name)
    if not p:
        raise HTTPException(404, f"panel '{name}' not found")
    return PanelInfoData(name=name, power_W=p.power_W, width_m=p.width_m,
                         height_m=p.height_m, model_str=p.model_str)


@app.post("/api/panel/arrange")
def arrange(body: dict):
    sa_data = SolarArrayData(**body["solar_array"])
    prohibited_sets = body.get("prohibited_sets", [])
    sa = _to_solar_array(sa_data)

    result = arranger.arrange(sa, prohibited_sets)

    rect = arranger.get_setback_rect(sa)
    angle = rect[2] if rect else 0

    panel_corners = []
    if sa.small_rect_size:
        for cx, cy in result.positions:
            corners = _compute_corners([cx, cy], list(sa.small_rect_size), angle, 0.98)
            panel_corners.append(corners)

    return ArrangeResult(
        total_count=result.total_count,
        horizontal_count=result.horizontal_count,
        vertical_count=result.vertical_count,
        intersect_keepout_count=result.intersect_keepout_count,
        kWp=result.kWp,
        angle=angle,
        positions=[list(p) for p in result.positions],
        panel_corners=panel_corners,
    )


@app.post("/api/panel/setback-rect")
def setback_rect(body: dict):
    sa_data = SolarArrayData(**body["solar_array"])
    sa = _to_solar_array(sa_data)
    rect = arranger.get_setback_rect(sa)
    if rect is None:
        return None
    center, size, angle = rect
    corners = _compute_corners(list(center), list(size), angle)
    return RectResult(center=list(center), size=list(size),
                      angle=angle, corners=corners)


@app.post("/api/panel/bounding-rect")
def bounding_rect(body: dict):
    sa_data = SolarArrayData(**body["solar_array"])
    sa = _to_solar_array(sa_data)
    rect = arranger.get_bounding_rect(sa)
    if rect is None:
        return None
    center, size, angle = rect
    corners = _compute_corners(list(center), list(size), angle)
    return RectResult(center=list(center), size=list(size),
                      angle=angle, corners=corners)


@app.post("/api/geometry/pixel-distance")
def pixel_distance(body: dict):
    return {"distance": geo.pixel_distance(
        (body["p1"][0], body["p1"][1]),
        (body["p2"][0], body["p2"][1]),
    )}


@app.post("/api/geometry/area")
def area(body: dict):
    return {"area": geo.area_square_meters(body["points"], body["scale_factor"])}


@app.post("/api/geometry/distance")
def distance(body: dict):
    return {"distance": geo.distance_meters(
        (body["p1"][0], body["p1"][1]),
        (body["p2"][0], body["p2"][1]),
        body["scale_factor"],
    )}


@app.post("/api/geometry/point-in-polygon")
def point_in_polygon(body: dict):
    return {"inside": geo.point_in_polygon(
        body["x"], body["y"], body["polygon"],
    )}
