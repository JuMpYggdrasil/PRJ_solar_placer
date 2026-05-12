from __future__ import annotations
import math
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from PIL import Image, ImageTk

from backend.services.geometry_service import GeometryService


class CanvasView(ttk.Frame):
    """Image canvas with zoom, drawing layers, and mouse event dispatch."""

    def __init__(
        self,
        master,
        on_click: Optional[Callable] = None,
        on_right_click: Optional[Callable] = None,
        on_motion: Optional[Callable] = None,
        on_enter: Optional[Callable] = None,
        on_leave: Optional[Callable] = None,
        on_wheel: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.geo = GeometryService()

        self.canvas = tk.Canvas(self, width=0, height=0, bg="gray25")
        self.canvas.pack()

        self.original_image: Optional[Image.Image] = None
        self.tk_image: Optional[ImageTk.PhotoImage] = None
        self.zoom_factor: float = 1.0
        self.zoom_enabled: bool = False

        self._bg_image_id: Optional[int] = None
        self._overlay_ids: list[int] = []

        if on_click:
            self.canvas.bind("<Button-1>", on_click)
        if on_right_click:
            self.canvas.bind("<Button-3>", on_right_click)
        if on_motion:
            self.canvas.bind("<Motion>", on_motion)
        if on_enter:
            self.canvas.bind("<Enter>", on_enter)
        if on_leave:
            self.canvas.bind("<Leave>", on_leave)
        if on_wheel:
            self.canvas.bind("<MouseWheel>", on_wheel)

    # ── Image management ──

    def load_image(self, image_path: str) -> None:
        self.original_image = Image.open(image_path)
        new_size = (int(self.original_image.width * 7 / 10), int(self.original_image.height * 7 / 10))
        self.original_image = self.original_image.resize(new_size, Image.Resampling.LANCZOS)
        self.zoom_factor = 1.0

    def set_cursor(self, cursor: str) -> None:
        self.master.config(cursor=cursor)

    # ── Main redraw ──

    def redraw(
        self,
        session,
        reference_points: list,
        points: list,
        prohibited_points: list,
        prohibited_sets: list,
        tree_sets: list,
        arrays: list,
        active_array,
        shadow_points: list,
        already_draw_panel: bool,
        already_draw_shadow: bool,
        show_zoom_roi: bool = False,
        mouse_pos: Optional[tuple[int, int]] = None,
    ) -> None:
        self.canvas.delete("all")
        self._overlay_ids.clear()

        if self.original_image is None:
            return

        w = int(self.original_image.width * self.zoom_factor)
        h = int(self.original_image.height * self.zoom_factor)
        resized = self.original_image.resize((w, h), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized)
        self.canvas.config(width=w, height=h)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        if not reference_points:
            self._draw_pre_calibration_ui(w, h, points, resized)
            return

        self._draw_prohibited(prohibited_points, prohibited_sets)
        self._draw_shadows(shadow_points, already_draw_shadow)
        self._draw_panels(arrays, active_array, prohibited_sets, already_draw_panel, already_draw_shadow)
        self._draw_trees(tree_sets)

        for pt in points:
            self._dot(pt, "yellow")
        for pt in reference_points:
            self._dot(pt, "purple")

        self._draw_active_area(active_array)

        if show_zoom_roi and mouse_pos:
            self._display_zoom(mouse_pos[0], mouse_pos[1], w, h)

    # ── Private drawing helpers ──

    def _draw_pre_calibration_ui(self, canvas_w: int, canvas_h: int, points: list, resized: Image.Image) -> None:
        self.set_cursor("circle")
        roi_w, roi_h = 300, 150
        zoom = 3
        roi = resized.crop((canvas_w - roi_w, canvas_h - roi_h, canvas_w, canvas_h))
        zoomed = roi.resize((roi_w * zoom, roi_h * zoom), Image.Resampling.LANCZOS)
        self.triple_roi = ImageTk.PhotoImage(zoomed)
        self.canvas.create_image(canvas_w, canvas_h, anchor=tk.SE, image=self.triple_roi)
        if len(points) == 1:
            self._dot(points[0], "purple")

    def _draw_prohibited(self, points: list, permanent_sets: list) -> None:
        for pt in points:
            self._dot(pt, "pink")
        for zone in permanent_sets:
            for pt in zone:
                self._dot(pt, "red")
            if len(zone) >= 4:
                coords = []
                for p in zone[:4]:
                    coords.extend(p)
                self.canvas.create_polygon(*coords, fill="red", stipple="gray50")

    def _draw_shadows(self, shadow_points: list, show: bool) -> None:
        if not show or not shadow_points:
            return
        from backend.services.shadow_service import ShadowService
        hull = ShadowService.convex_hull_points(shadow_points)
        if len(hull) > 2:
            flat = [c for pt in hull for c in pt]
            self.canvas.create_polygon(*flat, stipple="gray50")

    def _draw_panels(
        self, arrays: list, active_array, prohibited_sets: list,
        already_draw_panel: bool, already_draw_shadow: bool,
    ) -> None:
        from backend.services.panel_arranger import PanelArranger
        arranger = PanelArranger()

        all_arrays = list(arrays)
        if already_draw_panel and active_array.panel_points:
            all_arrays.append(active_array)

        for sa in all_arrays:
            is_active = (sa is active_array)
            if not is_active and already_draw_shadow:
                self._draw_skeleton(sa)
                self._draw_text_label(sa, arrays.index(sa) if sa in arrays else len(arrays))
                continue

            if not sa.panel_type or len(sa.panel_points) < 4:
                continue

            center, size, angle = arranger.get_setback_rect(sa) or ((0, 0), (0, 0), 0)
            self._draw_rotated_rect(center, size, angle, color="gold", stipple="gray50")
            self._draw_rotated_rect(center, size, angle, color="", stipple=None,
                                    outline="navy", width=2)
            self._draw_angle_label(center, size, angle)

            result = arranger.arrange(sa, prohibited_sets)
            sa.total_panel_count = result.total_count
            sa.horizontal_panel_count = result.horizontal_count
            sa.vertical_panel_count = result.vertical_count
            sa.intersect_keepout_count = result.intersect_keepout_count
            sa.kWp = result.kWp

            for cx, cy in result.positions:
                self._draw_rotated_rect((cx, cy), sa.small_rect_size, angle,
                                        color="midnight blue", stipple=None, scaled=0.98)

            self._dot(center, "green")
            if not is_active:
                self._draw_text_label(sa, arrays.index(sa) if sa in arrays else len(arrays))

    def _draw_skeleton(self, solar_array) -> None:
        from backend.services.panel_arranger import PanelArranger
        arranger = PanelArranger()
        rect = arranger.get_bounding_rect(solar_array)
        if rect:
            center, size, angle = rect
            self._draw_rotated_rect(center, size, angle, color="gold", stipple="gray50")
        sbrect = arranger.get_setback_rect(solar_array)
        if sbrect:
            center, size, angle = sbrect
            self._draw_rotated_rect(center, size, angle, color="", stipple=None,
                                    outline="navy", width=2)

    def _draw_text_label(self, solar_array, index: int) -> None:
        if len(solar_array.panel_points) < 4:
            return
        import cv2
        import numpy as np
        pts = np.array(solar_array.panel_points[-4:], dtype=np.int32)
        rect = cv2.minAreaRect(pts)
        cx, cy = rect[0]
        self.canvas.create_text(cx + 5, cy + 5, text=f"PV_{index + 1}", fill="yellow",
                                font=("Helvetica", 10, "bold"))

    def _draw_active_area(self, solar_array) -> None:
        pts = solar_array.panel_points
        for pt in pts:
            self._dot(pt, "blue")
        if len(pts) > 1:
            for i in range(len(pts) - 1):
                self.canvas.create_line(*pts[i], *pts[i + 1], fill="orange")
            self.canvas.create_line(*pts[0], *pts[-1], fill="orange")

    def _draw_trees(self, tree_sets: list) -> None:
        for tree in tree_sets:
            x0, y0 = tree[0]
            x1, y1 = tree[1]
            r = math.dist([x0, y0], [x1, y1])
            self._circle(x0, y0, r, fill="lawn green", outline="")
            self.canvas.create_text(x0, y0, text=f"{tree[2]:.1f} m",
                                    fill="black", font=("Helvetica", 10, "bold"))

    def _draw_rotated_rect(
        self, center, size, angle_deg,
        color="lightblue", stipple="gray50", scaled=1.0,
        outline="", width=1,
    ) -> None:
        corners = self.geo.compute_rotated_rect_corners(center, size, angle_deg, scaled)
        coords = [c for pt in corners for c in pt]
        kwargs = {"fill": color, "stipple": stipple, "outline": outline, "width": width}
        if not stipple:
            kwargs.pop("stipple")
        self.canvas.create_polygon(*coords, **kwargs)

    def _draw_angle_label(self, center, size, angle_deg) -> None:
        w, h = size
        cx, cy = center
        rad = math.radians(angle_deg)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        x2 = cx + w / 2 * cos_a - h / 2 * sin_a
        y2 = cy + w / 2 * sin_a + h / 2 * cos_a
        x3 = cx + w / 2 * cos_a + h / 2 * sin_a
        y3 = cy + w / 2 * sin_a - h / 2 * cos_a
        x1 = cx - w / 2 * cos_a - h / 2 * sin_a
        ymax = max(
            cy - w / 2 * sin_a + h / 2 * cos_a,
            cy + w / 2 * sin_a + h / 2 * cos_a,
            cy + w / 2 * sin_a - h / 2 * cos_a,
            cy - w / 2 * sin_a - h / 2 * cos_a,
        )

        self.canvas.create_line(x2, ymax, x3, ymax, fill="black")
        self.canvas.create_line(x2, ymax + 1, x3, ymax + 1, fill="white")
        self.canvas.create_line(x2, ymax, x1, ymax, fill="white")
        self.canvas.create_line(x2, ymax + 1, x1, ymax + 1, fill="black")
        self.canvas.create_text(
            (x2 + x3) / 2, ymax + 10,
            text=f"{90 - angle_deg:.1f} deg",
            fill="black", font=("Helvetica", 10, "bold"),
        )
        self.canvas.create_text(
            (x2 + x1) / 2, ymax + 10,
            text=f"{angle_deg:.1f} deg",
            fill="black", font=("Helvetica", 10, "bold"),
        )

    def _display_zoom(self, x: int, y: int, img_w: int, img_h: int) -> None:
        if self.original_image is None:
            return
        roi_dist = 100
        rx = min(min(x * 2, (img_w - x) * 2, roi_dist) if 0 < x < img_w else roi_dist, roi_dist)
        ry = min(min(y * 2, (img_h - y) * 2, roi_dist) if 0 < y < img_h else roi_dist, roi_dist)

        left, top = x - rx, y - ry
        right, bottom = x + rx, y + ry

        try:
            roi = self.original_image.crop((left, top, right, bottom))
            zoomed = roi.resize((rx * 5, ry * 5), Image.Resampling.LANCZOS)
            self._zoom_tk = ImageTk.PhotoImage(zoomed)
            self.canvas.create_image(
                int(x + rx * 5 / 2), int(y + ry * 5 / 2),
                anchor=tk.SE, image=self._zoom_tk,
            )
        except Exception:
            pass

    def _dot(self, pt: tuple[float, float], color: str, r: int = 3) -> None:
        x, y = pt
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="")

    def _circle(self, x: float, y: float, r: float, fill: str = "", outline: str = "black") -> None:
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline=outline)

    def draw_circle(self, x: float, y: float, r: float, fill: str = "", outline: str = "black") -> None:
        self._circle(x, y, r, fill, outline)

    def draw_2half_circle(self, x: float, y: float, r: float,
                          fill_left: str = "green2", fill_right: str = "red") -> None:
        self.canvas.create_arc(x - r, y - r, x + r, y + r, start=90, extent=180, fill=fill_left, outline="")
        self.canvas.create_arc(x - r, y - r, x + r, y + r, start=-90, extent=180, fill=fill_right, outline="")
