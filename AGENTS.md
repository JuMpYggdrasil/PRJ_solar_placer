# Solar Panel Estimation Tool — Agent Guide

## Project

Tkinter desktop app for rooftop solar panel layout estimation from aerial imagery. Users load an image, calibrate scale, draw roof boundaries, and get panel counts, kWp, and energy estimates with shadow analysis.

## Entrypoints

- **`SolarPanelEstimation.py`** — main app (1876 lines, single file). Run: `python SolarPanelEstimation.py`
- **`main_tkinter.py`** — referenced by `main_tkinter.spec` but source absent from repo; `SolarPanelEstimation.py` is the real entrypoint.
- **`plot_solar.py`** — standalone sun-path (analemma) plot via `pvlib`. Used by app's "Sun-Path Plot" button.
- **`weibull_wind.py`** — standalone wind-speed Weibull analysis script.

## Dependencies

- **`requirements.txt`** exists; install with: `pip install -r requirements.txt`
- Python 3.10 (`.venv` points to `Python310`)
- Virtual env activate: `.venv\Scripts\Activate.ps1`

## Building EXE

Uses PyInstaller via `.spec` files:

```
pyinstaller SolarPanelEstimation.spec
pyinstaller main_tkinter.spec
```

Build outputs go to `build/` and `dist/` (gitignored). `dist/SolarPanelEstimation.exe` is the distributable.

## Pysolar Gotcha

pysolar auto-detects numpy and switches to `numpy` math mode at import, which triggers numpy 2.x warnings (`UserWarning: no explicit representation of timezones available for np.datetime64`). The app forces `pysolar.use_math()` right after `import pysolar` to use the built-in `math` module instead (scalar datetime inputs only, so no functional impact). **Any agent adding pysolar imports must place `import pysolar; pysolar.use_math()` before `from pysolar.solar import ...`.**

## Config & Data

- **`parameter.json`** — runtime read-write config: latitude, longitude, panel_info (model specs as `[power_W, width_m, height_m, model_str]`), Thai PV zipcode data. The app mutates this file.
- **`parameter_backup.json`** — backup of the above.
- **`sattahip_wind.csv`** — wind data for `weibull_wind.py`.
- **`EDSR_x4.pb`** — TensorFlow upscaling model (unused in current code).

## Key Architecture Notes

- **`SolarArray`** class manages one panel array (points, panel type, gaps, setback, tilt, shadow). Stored in `panel_permanent_sets` list.
- **`SolarPanelEstimationApp`** drives the tkinter GUI with 3 tabs: Panel Layout, Shadow, PVOUT/Year.
- Workflow: load image → click 2 reference points (calibrate scale) → click 4 boundary points → "PV Panel" → adjust gaps/setback → "Save Panel" → repeat → "Calculate Shadow" → read kWp/kWh totals.
- Shadow calculation uses `pysolar` for solar position + `cv2` convex hull polygon drawing at 8 datetime samples per year.
- Keepout zones: right-click 4 points → "Keepout". Trees: checkbox "Tree" mode → click center + radius edge → enter height.
- Panel arrangment algorithm: flood-fill grid with alternating walk gaps inside rotated rectangle with `cv2.rotatedRectangleIntersection` keepout detection.
- Data held in memory only; no serialization of sessions besides lat/lng in `parameter.json`.

## Files to ignore

- `test_*.py` — exploratory/historical, not a test suite.
- `build/`, `dist/` — PyInstaller artifacts (gitignored).
- `__pycache__/`, `.venv/`, `*.jpg`, `*.png`, `*.spec` — runtime/build artifacts.

## Style

- No tests, linter, typechecker, or CI configured.
- Mixed camelCase method names (not PEP8).
- Single module, no package structure.
- Comments are sparse; dead code has been cleaned up.
