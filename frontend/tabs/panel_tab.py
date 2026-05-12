from __future__ import annotations
import tkinter as tk
from tkinter import ttk


class PanelTab(ttk.Frame):
    """Tab 1: Panel Layout — toolbar at top, sidebar at right, status bar at bottom."""

    def __init__(
        self,
        master,
        toolbar: ttk.Frame,
        sidebar: ttk.Frame,
        status_bar: ttk.Frame,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        toolbar.pack(in_=self, side=tk.TOP, fill=tk.X)
        sidebar.pack(in_=self, side=tk.RIGHT, fill=tk.Y)
        status_bar.pack(in_=self, side=tk.BOTTOM, fill=tk.X)
