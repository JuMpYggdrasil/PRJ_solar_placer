from __future__ import annotations
import json
import os
from typing import Optional
from ..models.panel_info import PanelInfo
from .constants import Constants


class PanelRepository:
    """CRUD for solar panel type definitions."""

    def __init__(self, filepath: str = Constants.JSON_FILE_PATH):
        self.filepath = filepath
        self._panels: dict[str, PanelInfo] = {}
        self._load()

    def _load(self) -> None:
        default_panels = {
            "Jinko 615W": PanelInfo(615, 2.38, 1.134, "JKM-615N-66HL4M-BDV"),
            "Jinko 630W": PanelInfo(630, 2.465, 1.134, "JKM-630N-74HL4-BDV"),
        }

        if not os.path.exists(self.filepath):
            self._panels = default_panels
            return

        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        loaded = data.get("panel_info", {})
        for name, info in loaded.items():
            if isinstance(info, (list, tuple)) and len(info) >= 4:
                self._panels[name] = PanelInfo(int(info[0]), float(info[1]), float(info[2]), str(info[3]))
            elif isinstance(info, dict):
                self._panels[name] = PanelInfo(
                    int(info.get("power_W", 0)),
                    float(info.get("width_m", 0)),
                    float(info.get("height_m", 0)),
                    str(info.get("model_str", "")),
                )

        for name, panel in default_panels.items():
            if name not in self._panels:
                self._panels[name] = panel

    @property
    def names(self) -> list[str]:
        return list(self._panels.keys())

    def get(self, name: str) -> Optional[PanelInfo]:
        return self._panels.get(name)

    def get_all(self) -> dict[str, PanelInfo]:
        return dict(self._panels)

    def add(self, name: str, panel: PanelInfo) -> None:
        self._panels[name] = panel

    def update(self, name: str, panel: PanelInfo) -> None:
        if name in self._panels:
            self._panels[name] = panel

    def delete(self, name: str) -> bool:
        return self._panels.pop(name, None) is not None

    def save_to_json(self, filepath: Optional[str] = None) -> None:
        path = filepath or self.filepath
        data = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

        serialized = {}
        for name, p in self._panels.items():
            serialized[name] = [p.power_W, p.width_m, p.height_m, p.model_str]

        data["panel_info"] = serialized
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
