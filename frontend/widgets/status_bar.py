from __future__ import annotations
import tkinter as tk
from tkinter import ttk


class StatusBar(ttk.Frame):
    """Bottom status bar showing scale, coordinates, and info."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.scale_var = tk.StringVar(value="Scale: --")
        self.coord_var = tk.StringVar(value="X: --  Y: --")
        self.info_var = tk.StringVar(value="Ready")
        self.panel_var = tk.StringVar(value="Panels: 0")

        scale_lbl = ttk.Label(self, textvariable=self.scale_var, relief=tk.SUNKEN, padding=(4, 1))
        coord_lbl = ttk.Label(self, textvariable=self.coord_var, relief=tk.SUNKEN, padding=(4, 1), width=22)
        info_lbl = ttk.Label(self, textvariable=self.info_var, relief=tk.SUNKEN, padding=(4, 1))
        panel_lbl = ttk.Label(self, textvariable=self.panel_var, relief=tk.SUNKEN, padding=(4, 1))

        scale_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
        coord_lbl.pack(side=tk.LEFT, padx=1)
        panel_lbl.pack(side=tk.LEFT, padx=1)
        info_lbl.pack(side=tk.LEFT, padx=1, fill=tk.X, expand=True)

    def set_scale(self, scale: float) -> None:
        if scale:
            self.scale_var.set(f"Scale: {scale:.4f} m/px")
        else:
            self.scale_var.set("Scale: --")

    def set_coords(self, x: float, y: float) -> None:
        self.coord_var.set(f"X: {x:.0f}  Y: {y:.0f}")

    def set_info(self, text: str) -> None:
        self.info_var.set(text)

    def set_panel_count(self, count: int) -> None:
        self.panel_var.set(f"Panels: {count}")
