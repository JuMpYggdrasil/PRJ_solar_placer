# Solar Panel Estimation Tool — Agent Guide

## Project

Tkinter desktop app for rooftop solar panel layout estimation from aerial imagery. Users load an image, calibrate scale, draw roof boundaries, and get panel counts, kWp, and energy estimates with shadow analysis.

## Architecture

Structured as **backend/frontend** layers:

```
main.py                          # Entry point: python main.py
backend/
├── models/                      # Pure data classes (SolarArray, PanelInfo, ProjectSession)
├── services/                    # Business logic (PanelArranger, ShadowService, EnergyService, GeometryService)
└── repositories/                # Data access (JSON, Panel types, Constants)
frontend/
├── app.py                       # SolarPanelEstimationApp — orchestrator
├── widgets/                     # Reusable widgets (CanvasView, Toolbar, PanelListbox, StatusBar)
└── tabs/                        # Tab panels (PanelTab, ShadowTab, EnergyTab)
standalone/
├── plot_solar.py                # Sun-path (analemma) plot via pvlib
└── weibull_wind.py              # Wind-speed Weibull analysis
```

**Key rule:** `backend/` never imports tkinter. `frontend/` imports `backend/`.

## Entrypoints

- **`main.py`** — run `python main.py`
- **`SolarPanelEstimation.py`** — legacy monolithic version (1876 lines, single file). Run: `python SolarPanelEstimation.py`

## Dependencies

- **`requirements.txt`** — install with: `pip install -r requirements.txt`
- Python 3.10 (.venv points to `Python310`)
- Virtual env activate: `.venv\Scripts\Activate.ps1`

## Building EXE

Uses PyInstaller via `.spec` files:
```
pyinstaller SolarPanelEstimation.spec
```
Build outputs go to `build/` and `dist/` (gitignored). `dist/SolarPanelEstimation.exe` is the distributable.

## Pysolar Gotcha

pysolar auto-detects numpy and switches to `numpy` math mode at import, which triggers numpy 2.x warnings. The app forces `pysolar.use_math()` right after `import pysolar` to use the built-in `math` module instead (scalar datetime inputs only, no functional impact). **Any agent adding pysolar imports must place `import pysolar; pysolar.use_math()` before `from pysolar.solar import ...`.**

## Config & Data

- **`parameter.json`** — runtime read-write config: latitude, longitude, panel_info (model specs as `[power_W, width_m, height_m, model_str]`), Thai PV zipcode data. The app mutates this file.
- **`parameter_backup.json`** — backup of the above.
- **`sattahip_wind.csv`** — wind data for `weibull_wind.py`.
- **`EDSR_x4.pb`** — TensorFlow upscaling model (unused in current code).

## Key Architecture Notes

- **`SolarArray`** (`backend/models/solar_array.py`) — pure data class; no drawing logic.
- **`PanelArranger`** (`backend/services/panel_arranger.py`) — flood-fill grid placement with `cv2.rotatedRectangleIntersection` keepout detection.
- **`ShadowService`** (`backend/services/shadow_service.py`) — shadow geometry using `pysolar` + convex hull.
- **`ProjectSession`** (`backend/models/project_session.py`) — holds all mutable project state in memory; no serialization.
- **Workflow**: load image → click 2 reference points (calibrate scale) → click 4 boundary points → "PV Panel" → adjust gaps/setback → "Save Panel" → repeat → "Calculate Shadow" → read kWp/kWh totals.
- Keepout zones: right-click 4 points → "Keepout". Trees: checkbox "Tree" mode → click center + radius edge → enter height.

## Style

- No tests, linter, typechecker, or CI configured.
- Snake_case method names in `backend/`; mixed naming in legacy `frontend/` (migrating).
- `backend/` has type hints; `frontend/` in progress.

## Files to ignore

- `build/`, `dist/` — PyInstaller artifacts (gitignored).
- `__pycache__/`, `.venv/`, `*.jpg`, `*.png`, `*.spec` — runtime/build artifacts.
- `SolarPanelEstimation.py` — legacy monolithic file (kept for reference).
