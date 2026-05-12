from __future__ import annotations
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog

from backend.models import SolarArray, PanelInfo, ProjectSession
from backend.repositories import Constants, JsonRepository, PanelRepository
from backend.services import GeometryService, PanelArranger, ShadowService, EnergyService

from frontend.widgets import CanvasView
from frontend.tabs import ShadowTab, EnergyTab


class SolarPanelEstimationApp:
    """Main application — orchestrates backend services and frontend widgets."""

    def __init__(self, master: tk.Tk):
        self.master = master
        master.title("Solar Panel Estimation Tool")
        width = master.winfo_screenwidth()
        height = master.winfo_screenheight()
        master.geometry(f"{width}x{height}")

        # ── Services (backend) ──
        self.geo = GeometryService()
        self.arranger = PanelArranger()
        self.shadow_svc = ShadowService(timezone=Constants.DEFAULT_TZ)
        self.energy_svc = EnergyService(timezone=Constants.DEFAULT_TZ)

        # ── Repositories (backend) ──
        self.json_repo = JsonRepository()
        self.panel_repo = PanelRepository()

        # ── Session (backend model) ──
        self.session = ProjectSession()
        self.latitude = Constants.DEFAULT_LATITUDE
        self.longitude = Constants.DEFAULT_LONGITUDE
        self.tz = Constants.DEFAULT_TZ
        self.monthly_percent = list(Constants.MONTHLY_PERCENT_DEFAULT)
        self.kWh_total = 0.0

        # Load saved lat/lng
        lat, lng = self.json_repo.get_lat_lng()
        self.latitude = lat
        self.longitude = lng

        # ── Build UI ──
        self._build_ui()

    # ══════════════════════════════════════════════
    #  UI Construction
    # ══════════════════════════════════════════════

    def _build_ui(self) -> None:
        style = ttk.Style()
        current_theme = style.theme_use()

        # ── Canvas (top, natural size) ──
        self.canvas_view = CanvasView(self.master,
                                       on_click=self._on_canvas_click,
                                       on_right_click=self._on_canvas_right_click,
                                       on_motion=self._on_canvas_motion,
                                       on_enter=self._on_canvas_enter,
                                       on_leave=self._on_canvas_leave)
        if current_theme == "equilux":
            self.canvas_view.canvas.config(bg="gray25")
        self.canvas_view.pack()

        # ── Notebook (fills remaining space) ──
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # ══════════════════════════════════════
        # Tab 1: Panel Layout  (plain layout like original)
        # ══════════════════════════════════════
        self.panel_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.panel_tab, text="Panel Layout")

        superframe = ttk.Frame(self.panel_tab)
        superframe.pack(side=tk.TOP, fill=tk.X)

        left_frame = ttk.Frame(superframe)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(superframe)
        right_frame.pack(side=tk.RIGHT)

        # ── Row 1: Browse + Gap entries ──
        row1 = ttk.Frame(left_frame)
        row1.pack(side=tk.TOP)

        self.browse_btn = ttk.Button(row1, text="Browse Image", command=self._browse_image)
        self.browse_btn.pack(side=tk.LEFT)

        entries = [
            ("GW", "0.2"), ("GH", "0.2"), ("Walk", "0.7"), ("Setback", "0.5")
        ]
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

        # ── Row 2: Area + Distance labels ──
        row2 = ttk.Frame(left_frame)
        row2.pack(side=tk.TOP)

        self.area_label = ttk.Label(row2, text="Area: --")
        self.area_label.pack(side=tk.LEFT)

        self.dist_label = ttk.Label(row2, text="Distance: --")
        self.dist_label.pack(side=tk.LEFT, padx=8)

        # ── Row 3: Panel type + Action buttons ──
        row3 = ttk.Frame(left_frame)
        row3.pack(side=tk.TOP)

        self.panel_type_var = tk.StringVar(value=self.panel_repo.names[0] if self.panel_repo.names else "")
        self.panel_type_cb = ttk.Combobox(row3, textvariable=self.panel_type_var,
                                           values=self.panel_repo.names, width=16)
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

        # ── Row 4: Total info ──
        row4 = ttk.Frame(left_frame)
        row4.pack(side=tk.TOP)

        self.total_label = ttk.Label(row4, text="Total Panels: 0")
        self.total_label.pack(side=tk.LEFT)

        # ── Right: Listbox + buttons ──
        self.arrays_listbox = tk.Listbox(right_frame, width=30, height=12)
        self.arrays_listbox.pack(side=tk.LEFT)

        list_btn_frame = ttk.Frame(right_frame)
        list_btn_frame.pack(side=tk.LEFT, padx=2)

        ttk.Button(list_btn_frame, text="Edit", command=self._edit_panel, width=8).pack(pady=1)
        ttk.Button(list_btn_frame, text="Delete", command=self._delete_panel, width=8).pack(pady=1)
        # ══════════════════════════════════════
        # Tab 2: Shadow
        # ══════════════════════════════════════
        self.shadow_tab = ShadowTab(
            self.notebook,
            on_entry_changed=self._on_shadow_entry_changed,
            on_calc_shadow=self._calculate_shadows,
            on_hide_shadow=self._hide_shadows,
            on_clear_trees=self._clear_trees,
            on_sun_path=self._sun_path_plot,
            on_toggle_tree=self._on_toggle_tree,
            default_lat=self.latitude,
            default_lon=self.longitude,
        )
        self.notebook.add(self.shadow_tab, text="Shadow")

        # ══════════════════════════════════════
        # Tab 3: Energy
        # ══════════════════════════════════════
        self.energy_tab = EnergyTab(
            self.notebook,
            on_plot_monthly=self._monthly_plot,
            on_toggle_pvout=self._on_toggle_pvout,
        )
        self.notebook.add(self.energy_tab, text="PVOUT/Year")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_selected)

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
            tree_sets=self.session.tree_permanent_sets,
            arrays=self.session.arrays,
            active_array=self.session.active_array,
            shadow_points=self.session.shadow_points,
            already_draw_panel=self.session.already_draw_panel,
            already_draw_shadow=self.session.already_draw_shadow,
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
        total_kWp = self.session.total_kWp
        total_panels = sum(a.total_panel_count for a in self.session.arrays)
        total_panels += self.session.active_array.total_panel_count

        try:
            pvout = float(self.energy_tab.pvout_entry.get())
        except ValueError:
            pvout = 0

        tilt_factor = self.energy_svc.tilt_factor(
            self.session.active_array.tilt_angle,
            self.latitude, self.longitude,
        )
        self.kWh_total = total_kWp * pvout * Constants.PVSYST_RATIO * tilt_factor

        self.energy_tab.update_summary(total_kWp, self.kWh_total, total_panels)

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
                 f"kWp: {total_kWp:,.2f} | "
                 f"Annual: {self.kWh_total:,.2f} kWh"
        )

    # ══════════════════════════════════════════════
    #  Tab Events
    # ══════════════════════════════════════════════

    def _on_tab_selected(self, event=None) -> None:
        self._update_panel_settings()
        self._update_lat_lng()
        self._redraw()

    # ══════════════════════════════════════════════
    #  Settings helpers
    # ══════════════════════════════════════════════

    def _update_panel_settings(self) -> None:
        sa = self.session.active_array
        if not sa.panel_points:
            return

        gaps = self._get_gap_settings()
        panel_name = self.panel_type_var.get()
        panel = self.panel_repo.get(panel_name)
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
            sw = panel.width_m / self.session.scale_factor
            sh = panel.height_m / self.session.scale_factor
        else:
            sw = panel.height_m / self.session.scale_factor
            sh = panel.width_m / self.session.scale_factor
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

        lat, lon, elev, tilt = self.shadow_tab.get_lat_lng_elev_tilt()
        sa.tilt_angle = tilt
        sa.elevation = elev

    def _update_lat_lng(self) -> None:
        lat, lon, _, _ = self.shadow_tab.get_lat_lng_elev_tilt()

        if self.latitude == lat and self.longitude == lon:
            pass
        else:
            self.latitude = lat
            self.longitude = lon
            self.json_repo.save_lat_lng(lat, lon)

        pvout, province = self._get_pvout(lat, lon)
        if province:
            self.shadow_tab.set_province(province)
        if pvout and self.energy_tab.is_auto_pvout():
            self.energy_tab.set_pvout(pvout)

        monthly = self.energy_svc.get_monthly_percent(2023, lat, lon)
        self.monthly_percent = [(x + y) / 2 for x, y in zip(monthly, Constants.MONTHLY_PERCENT_DEFAULT)]

    def _get_pvout(self, lat: float, lon: float) -> tuple:
        locations = self.json_repo.get_thai_pv_data()
        nearest = self.json_repo.find_nearest_location(lat, lon, locations)
        if nearest is None:
            return None, None
        for loc in locations:
            if loc.get("province") == nearest.get("province"):
                pvout = loc.get("pvout", Constants.DEFAULT_PVOUT)
                return float(pvout), str(loc.get("province", ""))
        return None, None

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

    def _on_shadow_entry_changed(self, event=None) -> None:
        self._update_lat_lng()
        self._update_panel_settings()
        self._redraw()

    def _on_panel_type_changed(self, event=None) -> None:
        self._update_panel_settings()
        self._redraw()

    def _on_toggle_tree(self) -> None:
        pass

    def _on_toggle_pvout(self) -> None:
        if self.energy_tab.is_auto_pvout():
            self.energy_tab.set_pvout_enabled(True)
        else:
            self.energy_tab.set_pvout_enabled(False)

    # ══════════════════════════════════════════════
    #  Canvas Mouse Events
    # ══════════════════════════════════════════════

    _last_mouse_x: int = 0
    _last_mouse_y: int = 0

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

        # Check if clicking inside any existing panel
        for sa in [self.session.active_array] + self.session.arrays:
            if sa.panel_points and self.geo.point_in_polygon(x, y, sa.panel_points):
                return

        self.session.points.append((x, y))

        # ── Calibration (first 2 points) ──
        if not self.session.reference_points:
            if len(self.session.points) >= 2:
                self.session.reference_points = list(self.session.points)
                self.session.points.clear()

                p1 = self.session.reference_points[-2]
                p2 = self.session.reference_points[-1]
                px_dist = self.geo.pixel_distance(p1, p2) / Constants.REFERENCE_ZOOM_IN
                d_val = simpledialog.askfloat("Scale Factor",
                                              "Enter the scale factor (pixels to meters):")
                if d_val is not None:
                    self.session.scale_factor = d_val / px_dist
                    w = self.canvas_view.original_image.width
                    h = self.canvas_view.original_image.height
                    self.session.reference_points = [
                        (int((x + 2 * w) / Constants.REFERENCE_ZOOM_IN),
                         int((y + 2 * h) / Constants.REFERENCE_ZOOM_IN))
                        for x, y in self.session.reference_points
                    ]
                else:
                    self._clear_all()
                    return
            self._redraw()
            return

        # ── Tree mode ──
        if self.shadow_tab.is_tree_mode():
            self.session.tree_points.append((x, y))
            self.session.points.clear()
            if len(self.session.tree_points) == 2:
                h_val = simpledialog.askfloat("Tree Height", "Enter tree height (meters):")
                if h_val is not None:
                    center = self.session.tree_points[0]
                    edge = self.session.tree_points[1]
                    self.session.tree_permanent_sets.append((center, edge, h_val))
                    self.session.tree_points.clear()
                    self.shadow_tab.enable_clear_trees(True)
                    self.shadow_tab.enable_calc_shadow(True)
                else:
                    self.session.tree_points.clear()
            self._redraw()
            return

        # ── Maintain max 4 points ──
        if len(self.session.points) > 4:
            self.session.points.pop(0)

        # ── Area / Distance ──
        if len(self.session.points) > 2 and self.session.scale_factor:
            area = self.geo.area_square_meters(self.session.points, self.session.scale_factor)
            self.area_label.config(text=f"Area: {area:.2f} m²")
        else:
            self.area_label.config(text="Area: --")

        if len(self.session.points) > 1 and self.session.scale_factor:
            d = self.geo.distance_meters(self.session.points[-2], self.session.points[-1],
                                          self.session.scale_factor)
            self.dist_label.config(text=f"Distance: {d:.2f} m")
            self.clr_btn["state"] = tk.NORMAL
        else:
            self.dist_label.config(text="Distance: --")

        # ── Auto-detect panel when 4 points ──
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

        if self.shadow_tab.is_tree_mode():
            self.session.tree_points.clear()
            self.shadow_tab.set_tree_mode(False)
            self._redraw()
            return

        self.session.prohibited_points.append((x, y))
        if len(self.session.prohibited_points) > 4:
            self.session.prohibited_points.pop(0)
        if len(self.session.prohibited_points) == 4:
            self.keepout_btn["state"] = tk.NORMAL
        self.session.already_draw_panel = False
        self._update_panel_settings()
        self._redraw()

    def _on_canvas_motion(self, event) -> None:
        self._last_mouse_x = event.x
        self._last_mouse_y = event.y

        self._redraw()

        if self.shadow_tab.is_tree_mode():
            x, y = event.x, event.y
            cv = self.canvas_view.canvas
            cv.create_oval(x - 3, y - 3, x + 3, y + 3, fill="lawn green", outline="", width=1)
            cv.create_text(x, y, text="draw trees", fill="black", font=("Helvetica", 10, "bold"))
            if len(self.session.tree_points) == 1:
                x0, y0 = self.session.tree_points[0]
                r = self.geo.pixel_distance((x0, y0), (x, y))
                self.canvas_view.draw_circle(x0, y0, r, fill="lawn green", outline="white")

    # ══════════════════════════════════════════════
    #  Button Actions
    # ══════════════════════════════════════════════

    def _calculate_panel(self) -> None:
        self.session.already_draw_panel = True
        self.shadow_tab.enable_calc_shadow(True)
        self.shadow_tab.enable_tree(True)
        self.save_btn["state"] = tk.NORMAL
        self._update_panel_settings()
        self._redraw()

    def _save_panel(self) -> None:
        self.session.already_draw_panel = False
        self._update_panel_settings()
        self.session.add_array(self.session.active_array.copy())
        self.session.active_array.reset_to_initial_state()
        self.save_btn["state"] = tk.DISABLED
        self.calc_btn["state"] = tk.DISABLED
        self.clr_btn["state"] = tk.DISABLED
        self.shadow_tab.enable_calc_shadow(True)
        self.shadow_tab.enable_hide_shadow(False)
        self._update_listbox()
        self._redraw()

    def _clear_panel(self) -> None:
        self.session.points.clear()
        self.session.active_array.reset_to_initial_state()
        self.session.already_draw_panel = False
        self.session.already_draw_shadow = False
        self.calc_btn["state"] = tk.DISABLED
        self.save_btn["state"] = tk.DISABLED
        self.clr_btn["state"] = tk.DISABLED
        if not self.session.has_arrays:
            self.shadow_tab.enable_calc_shadow(False)
        self.shadow_tab.set_tree_mode(False)
        self.shadow_tab.enable_tree(False)
        self._redraw()

    def _clear_all(self) -> None:
        self.session.clear_all()
        self.calc_btn["state"] = tk.DISABLED
        self.save_btn["state"] = tk.DISABLED
        self.clr_btn["state"] = tk.DISABLED
        self.keepout_btn["state"] = tk.DISABLED
        self.shadow_tab.enable_calc_shadow(False)
        self.shadow_tab.enable_hide_shadow(False)
        self.shadow_tab.set_tree_mode(False)
        self.shadow_tab.enable_tree(False)
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

    def _calculate_shadows(self) -> None:
        self.session.already_draw_shadow = True
        self.shadow_tab.enable_calc_shadow(False)
        self.shadow_tab.enable_hide_shadow(True)
        self._update_panel_settings()
        self._compute_all_shadows()
        self._redraw()

    def _hide_shadows(self) -> None:
        self.session.already_draw_shadow = False
        self.session.shadow_points.clear()
        self.shadow_tab.enable_hide_shadow(False)
        self.shadow_tab.enable_calc_shadow(True)
        self._update_panel_settings()
        self._redraw()

    def _clear_trees(self) -> None:
        self.session.tree_points.clear()
        self.session.tree_permanent_sets.clear()
        self.shadow_tab.enable_clear_trees(False)
        self._update_panel_settings()
        self._redraw()

    def _sun_path_plot(self) -> None:
        lat, lon, _, _ = self.shadow_tab.get_lat_lng_elev_tilt()
        from standalone.plot_solar import plot_solar_analemma
        plot_solar_analemma(lat=lat, lon=lon,
                            start_date="2021-01-01 00:00:00",
                            end_date="2022-01-01",
                            timezone=self.tz)

    def _monthly_plot(self) -> None:
        import calendar
        import matplotlib.pyplot as plt
        annual = self.kWh_total
        monthly = [annual * (p / 100) for p in self.monthly_percent]
        names = [calendar.month_abbr[i] for i in range(1, 13)]

        for m, p in zip(names, monthly):
            plt.text(m, p + 10, f"{p:,.0f}", ha="center", va="bottom")

        plt.bar(names, monthly, color="blue")
        plt.xlabel("Month")
        plt.ylabel("Power Production (kWh)")
        plt.title(f"Monthly Power Production (Total: {annual:,.0f} kWh)")
        plt.show()

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
        sa = self.session.remove_array(idx)
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
        self.shadow_tab.tilt_entry.delete(0, tk.END)
        self.shadow_tab.tilt_entry.insert(0, str(sa.tilt_angle))
        self.shadow_tab.elevation_entry.delete(0, tk.END)
        self.shadow_tab.elevation_entry.insert(0, str(sa.elevation))

        self._update_listbox()
        self._update_panel_settings()
        self._redraw()

    def _delete_panel(self) -> None:
        idx = self._selected_array_idx()
        if idx is None:
            return
        self.session.remove_array(idx)
        self._update_listbox()
        if not self.session.has_arrays:
            self.shadow_tab.enable_calc_shadow(False)
        self._redraw()

    # ══════════════════════════════════════════════
    #  Shadow computation
    # ══════════════════════════════════════════════

    def _compute_all_shadows(self) -> None:
        if not self.session.already_draw_shadow:
            return

        all_points: list = []

        for sa in [self.session.active_array] + self.session.arrays:
            for dt_str in Constants.SHADOW_DATETIMES:
                pts = self.shadow_svc.compute_panel_shadow_points(
                    dt_str, sa, self.latitude, self.longitude,
                    self.session.scale_factor,
                )
                all_points.extend(pts)

        hull = ShadowService.convex_hull_points(all_points)
        self.session.shadow_points = hull

        for dt_str in Constants.SHADOW_DATETIMES:
            for tree in self.session.tree_permanent_sets:
                center, edge, height = tree
                r = self.geo.pixel_distance(center, edge)
                elev, _, _, _ = self.shadow_tab.get_lat_lng_elev_tilt()
                sx, sy, sr = self.shadow_svc.compute_tree_shadow(
                    dt_str, center, r, height, elev,
                    self.latitude, self.longitude,
                    self.session.scale_factor,
                )
                self.canvas_view.draw_circle(sx, sy, sr, fill="black")

    # ══════════════════════════════════════════════
    #  Lat/Lng parse helper
    # ══════════════════════════════════════════════

    def update_lat_lng(self) -> None:
        self._update_lat_lng()


def main():
    root = tk.Tk()
    app = SolarPanelEstimationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
