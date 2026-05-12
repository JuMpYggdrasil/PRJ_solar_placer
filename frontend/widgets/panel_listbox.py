from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class PanelListbox(ttk.Frame):
    """Listbox of saved panel arrays with Edit/Delete/Duplicate buttons."""

    def __init__(
        self,
        master,
        on_select: Optional[Callable] = None,
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        on_duplicate: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        main_frame = ttk.LabelFrame(self, text="Saved Arrays")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(list_frame, width=40, height=12)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=2)

        self.edit_btn = ttk.Button(btn_frame, text="Edit", command=on_edit if on_edit else self._noop, width=10)
        self.edit_btn.pack(side=tk.LEFT, padx=1)

        self.delete_btn = ttk.Button(btn_frame, text="Delete", command=on_delete if on_delete else self._noop, width=10)
        self.delete_btn.pack(side=tk.LEFT, padx=1)

        self.dup_btn = ttk.Button(btn_frame, text="Duplicate", command=on_duplicate if on_duplicate else self._noop, width=10)
        self.dup_btn.pack(side=tk.LEFT, padx=1)

        if on_select:
            self.listbox.bind("<<ListboxSelect>>", lambda e: on_select())

    def update(self, items: list[str]) -> None:
        self.listbox.delete(0, tk.END)
        for item in items:
            self.listbox.insert(tk.END, item)

    def selected_index(self) -> Optional[int]:
        sel = self.listbox.curselection()
        return sel[0] if sel else None

    def enable_buttons(self, has_selection: bool = True) -> None:
        state = tk.NORMAL if has_selection else tk.DISABLED
        self.edit_btn["state"] = state
        self.delete_btn["state"] = state
        self.dup_btn["state"] = state

    @staticmethod
    def _noop() -> None:
        pass
