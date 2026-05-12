from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class Toolbar(ttk.Frame):
    """Top toolbar with gap/setback entries, panel type, and action buttons."""

    def __init__(
        self,
        master,
        panel_type_names: list[str],
        on_entry_changed: Callable = lambda: None,
        on_panel_type_changed: Callable = lambda e: None,
        on_browse: Callable = lambda: None,
        on_calc_panel: Callable = lambda: None,
        on_save_panel: Callable = lambda: None,
        on_clear_panel: Callable = lambda: None,
        on_clear_all: Callable = lambda: None,
        on_keepout: Callable = lambda: None,
        on_toggle_panel_rotation: Callable = lambda: None,
        on_toggle_walk_gap_rotation: Callable = lambda: None,
        on_toggle_zoom: Callable = lambda: None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        # ── Row 1: Browse + Gap settings ──
        row1 = ttk.Frame(self)
        row1.pack(side=tk.TOP, fill=tk.X, pady=1)

        self.browse_btn = ttk.Button(row1, text="Browse Image", command=on_browse)
        self.browse_btn.pack(side=tk.LEFT, padx=2)

        gap_frame = ttk.LabelFrame(row1, text="Gap", padding=(4, 2))
        gap_frame.pack(side=tk.LEFT, padx=4)

        ttk.Label(gap_frame, text="W:").pack(side=tk.LEFT)
        self.gap_width_entry = ttk.Entry(gap_frame, width=5)
        self.gap_width_entry.insert(0, "0.2")
        self.gap_width_entry.pack(side=tk.LEFT)

        ttk.Label(gap_frame, text="H:").pack(side=tk.LEFT)
        self.gap_height_entry = ttk.Entry(gap_frame, width=5)
        self.gap_height_entry.insert(0, "0.2")
        self.gap_height_entry.pack(side=tk.LEFT)

        ttk.Label(gap_frame, text="Walk:").pack(side=tk.LEFT)
        self.walk_gap_entry = ttk.Entry(gap_frame, width=5)
        self.walk_gap_entry.insert(0, "0.7")
        self.walk_gap_entry.pack(side=tk.LEFT)

        ttk.Label(gap_frame, text="Setback:").pack(side=tk.LEFT)
        self.setback_entry = ttk.Entry(gap_frame, width=5)
        self.setback_entry.insert(0, "0.5")
        self.setback_entry.pack(side=tk.LEFT)

        for w in (self.gap_width_entry, self.gap_height_entry, self.walk_gap_entry, self.setback_entry):
            w.bind("<FocusOut>", lambda e: on_entry_changed())
            w.bind("<Return>", lambda e: on_entry_changed())

        rot_frame = ttk.Frame(row1)
        rot_frame.pack(side=tk.LEFT, padx=4)

        self.panel_rotate_var = tk.IntVar()
        self.walk_gap_rotate_var = tk.IntVar()

        ttk.Checkbutton(rot_frame, text="Panel↻", variable=self.panel_rotate_var,
                        command=on_toggle_panel_rotation).pack(side=tk.LEFT)
        ttk.Checkbutton(rot_frame, text="Walk↻", variable=self.walk_gap_rotate_var,
                        command=on_toggle_walk_gap_rotation).pack(side=tk.LEFT)

        self.zoom_var = tk.IntVar()
        ttk.Checkbutton(rot_frame, text="Zoom", variable=self.zoom_var,
                        command=on_toggle_zoom).pack(side=tk.LEFT)

        # ── Row 2: Panel type + Action buttons ──
        row2 = ttk.Frame(self)
        row2.pack(side=tk.TOP, fill=tk.X, pady=1)

        self.panel_type_var = tk.StringVar(value=panel_type_names[0] if panel_type_names else "")
        self.panel_type_cb = ttk.Combobox(row2, textvariable=self.panel_type_var,
                                          values=panel_type_names, width=18)
        self.panel_type_cb.pack(side=tk.LEFT, padx=2)
        self.panel_type_cb.bind("<<ComboboxSelected>>", on_panel_type_changed)

        action_frame = ttk.LabelFrame(row2, text="Actions", padding=(4, 2))
        action_frame.pack(side=tk.LEFT, padx=4)

        self.calc_panel_btn = ttk.Button(action_frame, text="PV Panel", command=on_calc_panel, state=tk.DISABLED)
        self.calc_panel_btn.pack(side=tk.LEFT, padx=1)

        self.save_panel_btn = ttk.Button(action_frame, text="Save Panel", command=on_save_panel, state=tk.DISABLED)
        self.save_panel_btn.pack(side=tk.LEFT, padx=1)

        self.clear_panel_btn = ttk.Button(action_frame, text="Clear Panel", command=on_clear_panel, state=tk.DISABLED)
        self.clear_panel_btn.pack(side=tk.LEFT, padx=1)

        self.keepout_btn = ttk.Button(action_frame, text="Keepout", command=on_keepout, state=tk.DISABLED)
        self.keepout_btn.pack(side=tk.LEFT, padx=1)

        self.clear_all_btn = ttk.Button(action_frame, text="Clear All", command=on_clear_all)
        self.clear_all_btn.pack(side=tk.LEFT, padx=1)

        # ── Row 3: Info labels ──
        row3 = ttk.Frame(self)
        row3.pack(side=tk.TOP, fill=tk.X, pady=1)

        self.area_label = ttk.Label(row3, text="Area: --")
        self.area_label.pack(side=tk.LEFT, padx=4)

        self.distance_label = ttk.Label(row3, text="Distance: --")
        self.distance_label.pack(side=tk.LEFT, padx=4)

        self.total_label = ttk.Label(row3, text="Total Panels: 0")
        self.total_label.pack(side=tk.LEFT, padx=4)

    def get_gap_settings(self) -> dict:
        return {
            "gap_width": self._safe_float(self.gap_width_entry.get(), 0.2),
            "gap_height": self._safe_float(self.gap_height_entry.get(), 0.2),
            "walk_gap": self._safe_float(self.walk_gap_entry.get(), 0.7),
            "setback": self._safe_float(self.setback_entry.get(), 0.5),
            "panel_rotation": self.panel_rotate_var.get(),
            "walk_gap_rotation": self.walk_gap_rotate_var.get(),
        }

    def set_setback(self, value: float) -> None:
        self.setback_entry.delete(0, tk.END)
        self.setback_entry.insert(0, f"{value:.1f}")

    def set_rotation_ticks(self, panel_rot: int, walk_rot: int) -> None:
        self.panel_rotate_var.set(panel_rot)
        self.walk_gap_rotate_var.set(walk_rot)

    def get_selected_panel_type(self) -> str:
        return self.panel_type_var.get()

    def set_panel_types(self, names: list[str]) -> None:
        self.panel_type_cb["values"] = names
        if names and self.panel_type_var.get() not in names:
            self.panel_type_var.set(names[0])

    def set_area(self, area: float) -> None:
        self.area_label.config(text=f"Area: {area:.2f} m²" if area else "Area: --")

    def set_distance(self, dist: float) -> None:
        self.distance_label.config(text=f"Distance: {dist:.2f} m" if dist else "Distance: --")

    def set_total_info(self, text: str) -> None:
        self.total_label.config(text=text)

    def enable_calc_panel(self, enabled: bool = True) -> None:
        self.calc_panel_btn["state"] = tk.NORMAL if enabled else tk.DISABLED

    def enable_save_panel(self, enabled: bool = True) -> None:
        self.save_panel_btn["state"] = tk.NORMAL if enabled else tk.DISABLED

    def enable_clear_panel(self, enabled: bool = True) -> None:
        self.clear_panel_btn["state"] = tk.NORMAL if enabled else tk.DISABLED

    def enable_keepout(self, enabled: bool = True) -> None:
        self.keepout_btn["state"] = tk.NORMAL if enabled else tk.DISABLED

    @staticmethod
    def _safe_float(val: str, default: float = 0.0) -> float:
        try:
            return float(val)
        except ValueError:
            return default
