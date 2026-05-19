import type { PanelTypeData, RectResult, ArrangeResult, ConstantsData, Point, ActiveArrayData } from "@/types";

const BASE_URL = "http://127.0.0.1:8765";

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: body !== undefined ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  const data = await res.json();
  return data as T;
}

export const api = {
  health: () => post<{ status: string }>("/api/health"),

  getConstants: () => post<ConstantsData>("/api/constants"),

  getPanelTypes: () => post<PanelTypeData[]>("/api/panel-types"),

  getPanel: (name: string) => post<PanelTypeData>("/api/panel/get", { name }),

  arrange: (solarArray: Record<string, unknown>, prohibitedSets: Point[][]) =>
    post<ArrangeResult>("/api/panel/arrange", {
      solar_array: solarArray,
      prohibited_sets: prohibitedSets,
    }),

  setbackRect: (solarArray: Record<string, unknown>) =>
    post<RectResult | null>("/api/panel/setback-rect", { solar_array: solarArray }),

  boundingRect: (solarArray: Record<string, unknown>) =>
    post<RectResult | null>("/api/panel/bounding-rect", { solar_array: solarArray }),

  pixelDistance: (p1: Point, p2: Point) =>
    post<{ distance: number }>("/api/geometry/pixel-distance", { p1: [p1.x, p1.y], p2: [p2.x, p2.y] }),

  areaSquareMeters: (points: Point[], scaleFactor: number) =>
    post<{ area: number }>("/api/geometry/area", {
      points: points.map((p) => [p.x, p.y]),
      scale_factor: scaleFactor,
    }),

  distanceMeters: (p1: Point, p2: Point, scaleFactor: number) =>
    post<{ distance: number }>("/api/geometry/distance", {
      p1: [p1.x, p1.y],
      p2: [p2.x, p2.y],
      scale_factor: scaleFactor,
    }),

  pointInPolygon: (x: number, y: number, polygon: Point[]) =>
    post<{ inside: boolean }>("/api/geometry/point-in-polygon", {
      x,
      y,
      polygon: polygon.map((p) => [p.x, p.y]),
    }),
};

export function buildSolarArrayPayload(active: ActiveArrayData): Record<string, unknown> {
  return {
    panel_points: active.panelPoints.map((p) => [p.x, p.y]),
    panel_type: active.panelType,
    setback_length: active.setbackLength,
    gap_size: active.gapSize,
    small_rect_size: active.smallRectSize,
    panel_rotation_tick: active.panelRotationTick,
    walk_gap_rotation_tick: active.walkGapRotationTick,
  };
}
