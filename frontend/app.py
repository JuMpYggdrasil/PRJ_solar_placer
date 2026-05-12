from __future__ import annotations
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog

from frontend.widgets import CanvasView
from frontend.api_client import ApiClient


class SolarPanelEstimationApp:
    """Main application — communicates with backend through ApiClient."""

    def __init__(self, master: tk.Tk, api: ApiClient):
        self.master = master
        self.api = api

        master.title("Solar Panel Estimation Tool")
        width = master.winfo_screenwidth()
        height = master.winfo_screenheight()
        master.geometry(f"{width}x{height}")

        self.constants = self.api.get_constants()
        self.panel_types = self.api.get_panel_types()
        self.panel_type_names = [p["name"] for p in self.panel_types]

        self.session = type("Session", (), {})()
        self.session.scale_factor = None
        self.session.points = []
        self.session.reference_points = []
        self.session.prohibited_points = []
        self.session.prohibited_permanent_sets = []
        self.session.active_array = type("ActiveArray", (), {})()
        self._reset_active()

        self.session.arrays = []
        self.session.already_draw_panel = False

        self._build_ui()

    def _reset_active(self):
        sa = self.session.active_array
        sa.panel_points = []
        sa.panel_type = None
        sa.setback_length = 0
        sa.gap_size = None
        sa.small_rect_size = None
        sa.panel_rotation_tick = 0
        sa.walk_gap_rotation_tick = 0
        sa.total_panel_count = 0
        sa.horizontal_panel_count = 0
        sa.vertical_panel_count = 0
        sa.intersect_keepout_count = 0
        sa.kWp = 0
        sa.azimuth_angle = 0

    def _build_solar_array_data(self, sa=None) -> dict:
        if sa is None:
            sa = self.session.active_array
        data = {
            "panel_points": sa.panel_points if sa.panel_points else [],
            "panel_type": sa.panel_type,
            "setback_length": sa.setback_length,
            "gap_size": list(sa.gap_size) if sa.gap_size else None,
            "small_rect_size": list(sa.small_rect_size) if sa.small_rect_size else None,
            "panel_rotation_tick": sa.panel_rotation_tick,
            "walk_gap_rotation_tick": sa.walk_gap_rotation_tick,
        }
        return data

    # ══════════════════════════════════════════════
    #  UI Construction
    # ══════════════════════════════════════════════

    def _build_ui(self) -> None:
        style = ttk.Style()
        current_theme = style.theme_use()

        self.canvas_view = CanvasView(self.master,
                                       api=self.api,
                                       on_click=self._on_canvas_click,
                                       on_right_click=self._on_canvas_right_click,
                                       on_motion=self._on_canvas_motion,
                                       on_enter=self._on_canvas_enter,
                                       on_leave=self._on_canvas_leave)
        if current_theme == "equilux":
            self.canvas_view.canvas.config(bg="gray25")
        self.canvas_view.pack()

        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.panel_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.panel_tab, text="Panel Layout")

        superframe = ttk.Frame(self.panel_tab)
        superframe.pack(side=tk.TOP, fill=tk.X)

        left_frame = ttk.Frame(superframe)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(superframe)
        right_frame.pack(side=tk.RIGHT)

        row1 = ttk.Frame(left_frame)
        row1.pack(side=tk.TOP)

        self.browse_btn = ttk.Button(row1, text="Browse Image", command=self._browse_image)
        self.browse_btn.pack(side=tk.LEFT)

        entries = [("GW", "0.2"), ("GH", "0.2"), ("Walk", "0.7"), ("Setback", "0.5")]
        self.gap_entries = {}
        for label, default in entries:
            ttk.Label(row1, text=f"{label}:").pack(side=tk.LEFT)
            e = ttk.Entry(row1, width=5)
            e.insert(0, default)
            e.pack(side=tk.LEFT)
            e.bind("<FocusOut>", lambda ev: self._on_entry_changed())
            e.bind("<Return>", lambda ev: self._on_entry_changed())
            self.gap_entries[label] = e

        self.panel_rot_var = tk.IntVar()
        ttk.Checkbutton(row1, text="P↻", variable=self.panel_rot_var,
                        command=self._on_entry_changed).pack(side=tk.LEFT)

        self.walk_rot_var = tk.IntVar()
        ttk.Checkbutton(row1, text="W↻", variable=self.walk_rot_var,
                        command=self._on_entry_changed).pack(side=tk.LEFT)

        row2 = ttk.Frame(left_frame)
        row2.pack(side=tk.TOP)

        self.area_label = ttk.Label(row2, text="Area: --")
        self.area_label.pack(side=tk.LEFT)

        self.dist_label = ttk.Label(row2, text="Distance: --")
        self.dist_label.pack(side=tk.LEFT, padx=8)

        row3 = ttk.Frame(left_frame)
        row3.pack(side=tk.TOP)

        self.panel_type_var = tk.StringVar(value=self.panel_type_names[0] if self.panel_type_names else "")
        self.panel_type_cb = ttk.Combobox(row3, textvariable=self.panel_type_var,
                                           values=self.panel_type_names, width=16)
        self.panel_type_cb.pack(side=tk.LEFT)
        self.panel_type_cb.bind("<<ComboboxSelected>>", lambda e: self._on_entry_changed())

        self.calc_btn = ttk.Button(row3, text="PV Panel", command=self._calculate_panel, state=tk.DISABLED)
        self.calc_btn.pack(side=tk.LEFT, padx=1)

        self.save_btn = ttk.Button(row3, text="Save", command=self._save_panel, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=1)

        self.clr_btn = ttk.Button(row3, text="Clear", command=self._clear_panel, state=tk.DISABLED)
        self.clr_btn.pack(side=tk.LEFT, padx=1)

        self.keepout_btn = ttk.Button(row3, text="Keepout", command=self._add_keepout, state=tk.DISABLED)
        self.keepout_btn.pack(side=tk.LEFT, padx=1)

        self.clrall_btn = ttk.Button(row3, text="Clear All", command=self._clear_all)
        self.clrall_btn.pack(side=tk.LEFT, padx=1)

        row4 = ttk.Frame(left_frame)
        row4.pack(side=tk.TOP)

        self.total_label = ttk.Label(row4, text="Total Panels: 0")
        self.total_label.pack(side=tk.LEFT)

        self.arrays_listbox = tk.Listbox(right_frame, width=30, height=12)
        self.arrays_listbox.pack(side=tk.LEFT)

        list_btn_frame = ttk.Frame(right_frame)
        list_btn_frame.pack(side=tk.LEFT, padx=2)

        ttk.Button(list_btn_frame, text="Edit", command=self._edit_panel, width=8).pack(pady=1)
        ttk.Button(list_btn_frame, text="Delete", command=self._delete_panel, width=8).pack(pady=1)

    # ══════════════════════════════════════════════
    #  Core redraw
    # ══════════════════════════════════════════════

    def _redraw(self) -> None:
        if self.canvas_view.original_image is None:
            return

        self.canvas_view.redraw(
            session=self.session,
            reference_points=self.session.reference_points,
            points=self.session.points,
            prohibited_points=self.session.prohibited_points,
            prohibited_sets=self.session.prohibited_permanent_sets,
            arrays=self.session.arrays,
            active_array=self.session.active_array,
            already_draw_panel=self.session.already_draw_panel,
        )

        self._update_info_labels()

    def _get_gap_settings(self) -> dict:
        def sf(val, default=0.0):
            try:
                return float(val)
            except ValueError:
                return default
        return {
            "gap_width": sf(self.gap_entries["GW"].get(), 0.2),
            "gap_height": sf(self.gap_entries["GH"].get(), 0.2),
            "walk_gap": sf(self.gap_entries["Walk"].get(), 0.7),
            "setback": sf(self.gap_entries["Setback"].get(), 0.5),
            "panel_rotation": self.panel_rot_var.get(),
            "walk_gap_rotation": self.walk_rot_var.get(),
        }

    def _update_info_labels(self) -> None:
        total_kWp = sum(a.kWp for a in self.session.arrays) + self.session.active_array.kWp
        total_panels = sum(a.total_panel_count for a in self.session.arrays)
        total_panels += self.session.active_array.total_panel_count

        try:
            angle = min(self.session.active_array.azimuth_angle,
                        90 - self.session.active_array.azimuth_angle)
        except Exception:
            angle = 0

        try:
            h = self.session.active_array.horizontal_panel_count
            v = self.session.active_array.vertical_panel_count
            rect_text = f"{h} x {v} panels"
        except Exception:
            rect_text = ""

        self.total_label.config(
            text=f"Azimuth: {angle:.2f} deg, {rect_text} | "
                 f"kWp: {total_kWp:,.2f}"
        )

    # ══════════════════════════════════════════════
    #  Settings helpers
    # ══════════════════════════════════════════════

    def _update_panel_settings(self) -> None:
        sa = self.session.active_array
        if not sa.panel_points:
            return

        gaps = self._get_gap_settings()
        panel_name = self.panel_type_var.get()
        panel = next((p for p in self.panel_types if p["name"] == panel_name), None)
        if panel is None:
            return

        sa.panel_type = panel
        try:
            sa.setback_length = gaps["setback"] / self.session.scale_factor
        except (TypeError, ZeroDivisionError):
            sa.setback_length = 0

        sa.panel_rotation_tick = gaps["panel_rotation"]
        sa.walk_gap_rotation_tick = gaps["walk_gap_rotation"]

        if sa.panel_rotation_tick == 1:
            sw = panel["width_m"] / self.session.scale_factor
            sh = panel["height_m"] / self.session.scale_factor
        else:
            sw = panel["height_m"] / self.session.scale_factor
            sh = panel["width_m"] / self.session.scale_factor
        sa.small_rect_size = (sw, sh)

        try:
            sf = self.session.scale_factor
            if sa.walk_gap_rotation_tick == 1:
                bg_w = gaps["walk_gap"] / sf
                sg_w = gaps["gap_width"] / sf
                gw = bg_w * 0.5 + sg_w * 0.5
                sg_h = gaps["gap_height"] / sf
                bg_h = sg_h
                gh = sg_h
            else:
                sg_w = gaps["gap_width"] / sf
                bg_w = sg_w
                gw = sg_w
                bg_h = gaps["walk_gap"] / sf
                sg_h = gaps["gap_height"] / sf
                gh = bg_h * 0.5 + sg_h * 0.5
            sa.gap_size = (bg_w, bg_h, sg_w, sg_h, gw, gh)
        except (TypeError, ZeroDivisionError):
            pass

    # ══════════════════════════════════════════════
    #  Event: Browse Image
    # ══════════════════════════════════════════════

    def _browse_image(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])
        if not path:
            return
        self.canvas_view.load_image(path)
        self.browse_btn.pack_forget()
        self._redraw()

    # ══════════════════════════════════════════════
    #  Event: Entry changed
    # ══════════════════════════════════════════════

    def _on_entry_changed(self, event=None) -> None:
        self._update_panel_settings()
        self._redraw()

    # ══════════════════════════════════════════════
    #  Canvas Mouse Events
    # ══════════════════════════════════════════════

    def _on_canvas_enter(self, event) -> None:
        self.master.config(cursor="tcross")
        self._update_panel_settings()
        self._redraw()

    def _on_canvas_leave(self, event) -> None:
        self.master.config(cursor="arrow")
        self._update_panel_settings()
        self._redraw()

    def _on_canvas_click(self, event) -> None:
        x, y = event.x, event.y

        for sa in [self.session.active_array] + self.session.arrays:
            if sa.panel_points and self.api.point_in_polygon(x, y, sa.panel_points):
                return

        self.session.points.append((x, y))

        if not self.session.reference_points:
            if len(self.session.points) >= 2:
                self.session.reference_points = list(self.session.points)
                self.session.points.clear()

                p1 = self.session.reference_points[-2]
                p2 = self.session.reference_points[-1]
                px_dist = self.api.pixel_distance(p1, p2) / self.constants["REFERENCE_ZOOM_IN"]
                d_val = simpledialog.askfloat("Scale Factor",
                                              "Enter the scale factor (pixels to meters):")
                if d_val is not None:
                    self.session.scale_factor = d_val / px_dist
                    w = self.canvas_view.original_image.width
                    h = self.canvas_view.original_image.height
                    z = self.constants["REFERENCE_ZOOM_IN"]
                    self.session.reference_points = [
                        (int((x + 2 * w) / z), int((y + 2 * h) / z))
                        for x, y in self.session.reference_points
                    ]
                else:
                    self._clear_all()
                    return
            self._redraw()
            return

        if len(self.session.points) > 4:
            self.session.points.pop(0)

        if len(self.session.points) > 2 and self.session.scale_factor:
            area = self.api.area_square_meters(self.session.points, self.session.scale_factor)
            self.area_label.config(text=f"Area: {area:.2f} m²")
        else:
            self.area_label.config(text="Area: --")

        if len(self.session.points) > 1 and self.session.scale_factor:
            d = self.api.distance_meters(self.session.points[-2], self.session.points[-1],
                                          self.session.scale_factor)
            self.dist_label.config(text=f"Distance: {d:.2f} m")
            self.clr_btn["state"] = tk.NORMAL
        else:
            self.dist_label.config(text="Distance: --")

        if len(self.session.points) == 4:
            import cv2
            import numpy as np
            pts = np.array(self.session.points[-4:], dtype=np.int32)
            rect = cv2.minAreaRect(pts)
            box = cv2.boxPoints(rect)
            box = np.int_(box)
            self.session.active_array.panel_points = box.tolist()
            self.session.points.clear()
            self.calc_btn["state"] = tk.NORMAL
            self.clr_btn["state"] = tk.NORMAL

        self._update_panel_settings()
        self._redraw()

    def _on_canvas_right_click(self, event) -> None:
        x, y = event.x, event.y

        self.session.prohibited_points.append((x, y))
        if len(self.session.prohibited_points) > 4:
            self.session.prohibited_points.pop(0)
        if len(self.session.prohibited_points) == 4:
            self.keepout_btn["state"] = tk.NORMAL
        self.session.already_draw_panel = False
        self._update_panel_settings()
        self._redraw()

    def _on_canvas_motion(self, event) -> None:
        pass

    # ══════════════════════════════════════════════
    #  Button Actions
    # ══════════════════════════════════════════════

    def _calculate_panel(self) -> None:
        self.session.already_draw_panel = True
        self.save_btn["state"] = tk.NORMAL
        self._update_panel_settings()
        self._redraw()

    def _save_panel(self) -> None:
        self.session.already_draw_panel = False
        self._update_panel_settings()

        arr_data = self._build_solar_array_data()
        dup = type("SavedArray", (), {})()
        dup.panel_points = list(arr_data["panel_points"])
        dup.panel_type = arr_data["panel_type"]
        dup.setback_length = arr_data["setback_length"]
        dup.gap_size = arr_data["gap_size"]
        dup.small_rect_size = arr_data["small_rect_size"]
        dup.panel_rotation_tick = arr_data["panel_rotation_tick"]
        dup.walk_gap_rotation_tick = arr_data["walk_gap_rotation_tick"]
        dup.total_panel_count = self.session.active_array.total_panel_count
        dup.horizontal_panel_count = self.session.active_array.horizontal_panel_count
        dup.vertical_panel_count = self.session.active_array.vertical_panel_count
        dup.intersect_keepout_count = self.session.active_array.intersect_keepout_count
        dup.kWp = self.session.active_array.kWp
        dup.azimuth_angle = self.session.active_array.azimuth_angle

        self.session.arrays.append(dup)
        self._reset_active()
        self.save_btn["state"] = tk.DISABLED
        self.calc_btn["state"] = tk.DISABLED
        self.clr_btn["state"] = tk.DISABLED
        self._update_listbox()
        self._redraw()

    def _clear_panel(self) -> None:
        self.session.points.clear()
        self._reset_active()
        self.calc_btn["state"] = tk.DISABLED
        self.save_btn["state"] = tk.DISABLED
        self.clr_btn["state"] = tk.DISABLED
        self._redraw()

    def _clear_all(self) -> None:
        self.session.points.clear()
        self.session.reference_points.clear()
        self.session.prohibited_points.clear()
        self.session.prohibited_permanent_sets.clear()
        self.session.arrays.clear()
        self._reset_active()
        self.session.already_draw_panel = False
        self.session.scale_factor = None
        self.calc_btn["state"] = tk.DISABLED
        self.save_btn["state"] = tk.DISABLED
        self.clr_btn["state"] = tk.DISABLED
        self.keepout_btn["state"] = tk.DISABLED
        self.area_label.config(text="Area: --")
        self.dist_label.config(text="Distance: --")
        self._update_listbox()
        self._redraw()

    def _add_keepout(self) -> None:
        self.session.prohibited_permanent_sets.append(list(self.session.prohibited_points))
        self.session.prohibited_points.clear()
        self.keepout_btn["state"] = tk.DISABLED
        self._update_panel_settings()
        self._redraw()

    # ══════════════════════════════════════════════
    #  Panel Listbox Actions
    # ══════════════════════════════════════════════

    def _update_listbox(self) -> None:
        self.arrays_listbox.delete(0, tk.END)
        for n, sa in enumerate(self.session.arrays):
            self.arrays_listbox.insert(tk.END, f"PV_{n + 1}: {sa.kWp:.1f} kW")

    def _selected_array_idx(self):
        sel = self.arrays_listbox.curselection()
        return sel[0] if sel else None

    def _edit_panel(self) -> None:
        idx = self._selected_array_idx()
        if idx is None:
            return
        sa = self.session.arrays.pop(idx)
        self.session.active_array = sa
        self.session.already_draw_panel = True
        self.calc_btn["state"] = tk.NORMAL
        self.save_btn["state"] = tk.NORMAL
        self.clr_btn["state"] = tk.NORMAL

        sb = sa.setback_length * self.session.scale_factor if self.session.scale_factor else 0
        self.gap_entries["Setback"].delete(0, tk.END)
        self.gap_entries["Setback"].insert(0, f"{sb:.1f}")
        self.panel_rot_var.set(sa.panel_rotation_tick)
        self.walk_rot_var.set(sa.walk_gap_rotation_tick)

        self._update_listbox()
        self._update_panel_settings()
        self._redraw()

    def _delete_panel(self) -> None:
        idx = self._selected_array_idx()
        if idx is None:
            return
        self.session.arrays.pop(idx)
        self._update_listbox()
        self._redraw()


def main():
    print("This module is meant to be run via main.py")

