from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class ShadowTab(ttk.Frame):
    """Tab 2: Shadow analysis controls."""

    def __init__(
        self,
        master,
        on_entry_changed: Callable = lambda: None,
        on_calc_shadow: Callable = lambda: None,
        on_hide_shadow: Callable = lambda: None,
        on_clear_trees: Callable = lambda: None,
        on_sun_path: Callable = lambda: None,
        on_toggle_tree: Callable = lambda: None,
        default_lat: float = 13.7657,
        default_lon: float = 100.5026,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        # ── Row 1: Lat/Lon / Elevation / Tilt ──
        row1 = ttk.Frame(self)
        row1.pack(side=tk.TOP, fill=tk.X, pady=4)

        geo_frame = ttk.LabelFrame(row1, text="Location & Panel", padding=(6, 3))
        geo_frame.pack(side=tk.LEFT, padx=4)

        ttk.Label(geo_frame, text="Lat:").pack(side=tk.LEFT)
        self.lat_entry = ttk.Entry(geo_frame, width=12)
        self.lat_entry.insert(0, str(default_lat))
        self.lat_entry.pack(side=tk.LEFT)

        ttk.Label(geo_frame, text="Lon:").pack(side=tk.LEFT)
        self.lon_entry = ttk.Entry(geo_frame, width=12)
        self.lon_entry.insert(0, str(default_lon))
        self.lon_entry.pack(side=tk.LEFT)

        ttk.Label(geo_frame, text="Elev (m):").pack(side=tk.LEFT)
        self.elevation_entry = ttk.Entry(geo_frame, width=6)
        self.elevation_entry.insert(0, "0")
        self.elevation_entry.pack(side=tk.LEFT)

        ttk.Label(geo_frame, text="Tilt:").pack(side=tk.LEFT)
        self.tilt_entry = ttk.Entry(geo_frame, width=6)
        self.tilt_entry.insert(0, "10")
        self.tilt_entry.pack(side=tk.LEFT)

        for w in (self.lat_entry, self.lon_entry, self.elevation_entry, self.tilt_entry):
            w.bind("<FocusOut>", lambda e: on_entry_changed())
            w.bind("<Return>", lambda e: on_entry_changed())

        self.tree_var = tk.IntVar()
        self.tree_cb = ttk.Checkbutton(row1, text="Tree", variable=self.tree_var,
                                       command=on_toggle_tree, state=tk.DISABLED)
        self.tree_cb.pack(side=tk.LEFT, padx=4)

        # ── Row 2: Buttons ──
        row2 = ttk.Frame(self)
        row2.pack(side=tk.TOP, fill=tk.X, pady=4)

        action_frame = ttk.LabelFrame(row2, text="Actions", padding=(6, 3))
        action_frame.pack(side=tk.LEFT, padx=4)

        self.calc_btn = ttk.Button(action_frame, text="Calculate Shadow", command=on_calc_shadow, state=tk.DISABLED)
        self.calc_btn.pack(side=tk.LEFT, padx=1)

        self.hide_btn = ttk.Button(action_frame, text="Hide Shadow", command=on_hide_shadow, state=tk.DISABLED)
        self.hide_btn.pack(side=tk.LEFT, padx=1)

        self.clear_trees_btn = ttk.Button(action_frame, text="Clear Trees", command=on_clear_trees, state=tk.DISABLED)
        self.clear_trees_btn.pack(side=tk.LEFT, padx=1)

        self.sun_path_btn = ttk.Button(action_frame, text="Sun-Path Plot", command=on_sun_path)
        self.sun_path_btn.pack(side=tk.LEFT, padx=1)

        # ── Row 3: Province info ──
        row3 = ttk.Frame(self)
        row3.pack(side=tk.TOP, fill=tk.X, pady=2)
        self.province_label = ttk.Label(row3, text="Province: --")
        self.province_label.pack(side=tk.LEFT, padx=4)

    def get_lat_lng_elev_tilt(self) -> tuple[float, float, float, float]:
        lat = self._safe_float(self.lat_entry.get(), 0)
        lon = self._safe_float(self.lon_entry.get(), 0)
        elev = self._safe_float(self.elevation_entry.get(), 0)
        tilt = self._safe_float(self.tilt_entry.get(), 10)
        return lat, lon, elev, tilt

    def set_lat_lng(self, lat: float, lon: float) -> None:
        self.lat_entry.delete(0, tk.END)
        self.lat_entry.insert(0, str(lat))
        self.lon_entry.delete(0, tk.END)
        self.lon_entry.insert(0, str(lon))

    def set_province(self, name: str) -> None:
        self.province_label.config(text=f"Province: {name}")

    def enable_calc_shadow(self, enabled: bool = True) -> None:
        self.calc_btn["state"] = tk.NORMAL if enabled else tk.DISABLED

    def enable_hide_shadow(self, enabled: bool = True) -> None:
        self.hide_btn["state"] = tk.NORMAL if enabled else tk.DISABLED

    def enable_tree(self, enabled: bool = True) -> None:
        self.tree_cb["state"] = tk.NORMAL if enabled else tk.DISABLED

    def enable_clear_trees(self, enabled: bool = True) -> None:
        self.clear_trees_btn["state"] = tk.NORMAL if enabled else tk.DISABLED

    def is_tree_mode(self) -> bool:
        return self.tree_var.get() == 1

    def set_tree_mode(self, val: bool) -> None:
        self.tree_var.set(1 if val else 0)

    @staticmethod
    def _safe_float(val: str, default: float = 0.0) -> float:
        try:
            return float(val)
        except ValueError:
            return default
