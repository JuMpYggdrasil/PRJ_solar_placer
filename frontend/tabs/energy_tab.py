from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Callable


class EnergyTab(ttk.Frame):
    """Tab 3: PVOUT / Year energy summary."""

    def __init__(
        self,
        master,
        on_plot_monthly: Callable = lambda: None,
        on_toggle_pvout: Callable = lambda: None,
        default_pvout: float = 1433.2,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        row1 = ttk.Frame(self)
        row1.pack(side=tk.TOP, fill=tk.X, pady=8)

        ttk.Label(row1, text="Specific PV Power Output (kWh/kWp/yr):").pack(side=tk.LEFT, padx=4)

        self.pvout_entry = ttk.Entry(row1, width=10)
        self.pvout_entry.insert(0, str(default_pvout))
        self.pvout_entry.pack(side=tk.LEFT)

        self.pvout_en_var = tk.IntVar(value=1)
        self.pvout_en_cb = ttk.Checkbutton(row1, text="Auto", variable=self.pvout_en_var,
                                           command=on_toggle_pvout)
        self.pvout_en_cb.pack(side=tk.LEFT, padx=2)

        self.plot_btn = ttk.Button(row1, text="Monthly Plot", command=on_plot_monthly)
        self.plot_btn.pack(side=tk.LEFT, padx=8)

        # Summary frame
        summary_frame = ttk.LabelFrame(self, text="Project Summary", padding=(10, 5))
        summary_frame.pack(side=tk.TOP, fill=tk.X, padx=8, pady=8)

        self.kWp_label = ttk.Label(summary_frame, text="Total kWp: 0.00")
        self.kWp_label.pack(anchor=tk.W)

        self.kWh_label = ttk.Label(summary_frame, text="Annual Energy: 0.00 kWh")
        self.kWh_label.pack(anchor=tk.W)

        self.count_label = ttk.Label(summary_frame, text="Total Panels: 0")
        self.count_label.pack(anchor=tk.W)

    def get_pvout(self) -> float:
        try:
            return float(self.pvout_entry.get())
        except ValueError:
            return 0.0

    def set_pvout(self, value: float) -> None:
        self.pvout_entry.delete(0, tk.END)
        self.pvout_entry.insert(0, f"{value:.1f}")

    def is_auto_pvout(self) -> bool:
        return self.pvout_en_var.get() == 1

    def set_pvout_enabled(self, enabled: bool) -> None:
        self.pvout_entry["state"] = tk.NORMAL if enabled else tk.DISABLED

    def update_summary(self, total_kWp: float, annual_kWh: float, total_panels: int) -> None:
        self.kWp_label.config(text=f"Total kWp: {total_kWp:,.2f}")
        self.kWh_label.config(text=f"Annual Energy: {annual_kWh:,.2f} kWh")
        self.count_label.config(text=f"Total Panels: {total_panels}")
