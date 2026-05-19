# Solar Panel Estimation Tool — Agent Guide

## Project

Rooftop solar panel layout estimation from aerial imagery. Load image → calibrate scale → draw roof boundary → arrange panels → save array. Two frontends share the same backend.

## Architecture

```
main.py                          # Entry point (Tkinter default, --modern for web)
backend/
├── api/                         # FastAPI REST server on port 8765
├── models/                      # SolarArray, PanelInfo (pure data)
├── services/                    # PanelArranger (flood-fill), GeometryService
└── repositories/                # JSON read/write, panel type CRUD
frontend/                        # Tkinter UI (python main.py)
├── app.py, api_client.py, widgets/, tabs/
frontend_modern/                 # Next.js web UI (python main.py --modern)
├── src/app/page.tsx, components/, hooks/, services/, types/
```

**Rules:**
- `backend/` never imports tkinter.
- `frontend/` and `frontend_modern/` never import `backend/` directly — communicate solely via `ApiClient` (HTTP → FastAPI on `127.0.0.1:8765`).
- `main.py` starts FastAPI in daemon thread, then launches chosen frontend.

## Entrypoints

| Command | Frontend |
|---|---|
| `python main.py` | Tkinter |
| `python main.py --modern` | Next.js web (starts dev server + opens browser) |
| `npm run dev` (in `frontend_modern/`) | Next.js dev server standalone |
| `npm run build` (in `frontend_modern/`) | Production build |

## Dependencies

```
pip install -r requirements.txt   # Python (FastAPI, uvicorn, opencv, numpy, etc.)
cd frontend_modern && npm install  # Node (Next.js, React, Tailwind)
```

Python 3.10, node available at `D:\nodejs\npx.CMD`.

## Pysolar Gotcha

pysolar auto-detects numpy and switches to numpy math mode at import. The app forces `pysolar.use_math()` right after `import pysolar`. **Any agent adding pysolar imports must place `import pysolar; pysolar.use_math()` before `from pysolar.solar import ...`.**

## Config & Data

- **`parameter.json`** — runtime read-write config: latitude, longitude, panel specs (`[power_W, width_m, height_m, model_str]`), Thai PV zipcode data. Mutated by app.
- **`parameter_backup.json`** — backup copy.
- **`SolarPanelEstimation.py`** — legacy monolithic (1876 lines), kept for reference. Not used.
- **`sattahip_wind.csv`**, **`EDSR_x4.pb`**, **`standalone/`** — unused/unrelated files.

## API Endpoints (all served by FastAPI)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Backend alive check |
| GET | `/api/constants` | App constants (`REFERENCE_ZOOM_IN`: 3) |
| GET | `/api/panel-types` | List all panel model specs |
| POST | `/api/panel/get` | Get single panel type by name |
| POST | `/api/panel/arrange` | Flood-fill panel arrangement with keepout detection |
| POST | `/api/panel/setback-rect` | Setback inset rectangle (center, size, angle, corners) |
| POST | `/api/panel/bounding-rect` | Bounding rotated rectangle |
| POST | `/api/geometry/pixel-distance` | Euclidean distance between two points |
| POST | `/api/geometry/area` | Shoelace area in m² |
| POST | `/api/geometry/distance` | Real-world distance in m |
| POST | `/api/geometry/point-in-polygon` | Ray-casting point containment test |

## Workflow

1. Browse Image → load aerial photo (70% resize, LANCZOS)
2. Calibrate: click 2 reference points → enter real-world distance → scale factor computed
3. Click 4 boundary points → minAreaRect computed → PV Panel button enables
4. Select panel type, adjust gaps (GW/GH/Walk/Setback in meters), toggle rotations
5. PV Panel → backend arranges flood-fill grid, draws panels (midnight-blue rotated rects)
6. (Optional) Right-click 4 points → Keepout → red polygon zones, intersecting panels excluded
7. Save → array added to saved list with kWp summary
8. Edit/Delete saved arrays from sidebar list

## Key Code Locations

- `backend/api/server.py` — all 11 FastAPI endpoints
- `backend/api/schemas.py` — Pydantic models (PanelInfoData, SolarArrayData, RectResult, ArrangeResult)
- `backend/services/panel_arranger.py` — flood-fill grid with `cv2.rotatedRectangleIntersection`
- `frontend/app.py` — SolarPanelEstimationApp (Tkinter), session state as lightweight object
- `frontend_modern/src/hooks/useSession.tsx` — React context + state management for web frontend
- `frontend_modern/src/hooks/useCanvasDrawing.ts` — canvas redraw pipeline (panels, keepout, labels)
- `frontend_modern/src/components/CanvasView.tsx` — canvas with click/right-click handlers

## Files to Ignore

- `build/`, `dist/` — PyInstaller output (gitignored)
- `__pycache__/`, `.venv/`, `*.jpg`, `*.png`, `*.spec` — runtime/build artifacts
- `SolarPanelEstimation.py` — legacy monolith
- `frontend_modern/.next/`, `frontend_modern/node_modules/` — Next.js build artifacts
