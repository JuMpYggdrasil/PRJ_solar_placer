import { useCallback, useRef } from "react";
import type { Point, SessionState, ActiveArrayData, SavedArrayData } from "@/types";
import { api, buildSolarArrayPayload } from "@/services/apiClient";

const DOT_RADIUS = 3;
const BIG_DOT_RADIUS = 5;
const REFERENCE_ZOOM = 3;
const ZOOM_CROP_W = 300;
const ZOOM_CROP_H = 150;
const COLOR_PURPLE = "#9b59b6";
const COLOR_YELLOW = "#f1c40f";
const COLOR_ORANGE = "#e67e22";
const COLOR_BLUE = "#3498db";
const COLOR_GOLD = "#f39c12";
const COLOR_NAVY = "#2c3e50";
const COLOR_PANEL = "#1a237e";
const COLOR_GREEN = "#27ae60";
const COLOR_KEEPOUT_DOT = "#e91e63";
const COLOR_KEEPOUT_FILL = "rgba(231, 76, 60, 0.3)";
const COLOR_KEEPOUT_OUTLINE = "#c0392b";
const COLOR_WHITE = "#ffffff";
const COLOR_ANGLE_TEXT = "#2c3e50";
const COLOR_CALIBRATION = "#9b59b6";

function drawDot(ctx: CanvasRenderingContext2D, pt: Point, color: string, r = DOT_RADIUS) {
  ctx.beginPath();
  ctx.arc(pt.x, pt.y, r, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.fill();
}

function drawCircle(ctx: CanvasRenderingContext2D, x: number, y: number, r: number, fill: string, outline: string) {
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.strokeStyle = outline;
  ctx.lineWidth = 1;
  ctx.stroke();
}

interface DrawRectCorners {
  corners: [number, number][];
  fill: string;
  stroke: string;
  lineWidth?: number;
  stipple?: boolean;
}

function drawPolygon(ctx: CanvasRenderingContext2D, opts: DrawRectCorners) {
  const { corners, fill, stroke, lineWidth = 2, stipple } = opts;
  ctx.beginPath();
  ctx.moveTo(corners[0][0], corners[0][1]);
  for (let i = 1; i < corners.length; i++) {
    ctx.lineTo(corners[i][0], corners[i][1]);
  }
  ctx.closePath();
  if (stipple) {
    ctx.save();
    ctx.clip();
    ctx.fillStyle = fill;
    ctx.fill();
    ctx.restore();
  } else {
    ctx.fillStyle = fill;
    ctx.fill();
  }
  ctx.strokeStyle = stroke;
  ctx.lineWidth = lineWidth;
  ctx.stroke();
}

function drawAngleLabel(
  ctx: CanvasRenderingContext2D,
  center: [number, number],
  size: [number, number],
  angleDeg: number
) {
  const cx = center[0];
  const cy = center[1];
  const h = size[1];
  const labelY = cy + h / 2 + 30;
  const angle1 = angleDeg;
  const angle2 = 90 - angleDeg;

  ctx.save();
  ctx.strokeStyle = COLOR_NAVY;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(cx - 40, labelY);
  ctx.lineTo(cx + 40, labelY);
  ctx.stroke();

  ctx.font = "12px sans-serif";
  ctx.fillStyle = COLOR_ANGLE_TEXT;
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  ctx.fillText(`${angle1.toFixed(1)}° | ${angle2.toFixed(1)}°`, cx, labelY + 4);
  ctx.restore();
}

function drawTextLabel(ctx: CanvasRenderingContext2D, points: Point[], label: string) {
  if (points.length < 4) return;
  let cx = 0, cy = 0;
  for (const p of points) { cx += p.x; cy += p.y; }
  cx /= points.length;
  cy /= points.length;

  ctx.save();
  ctx.font = "bold 14px sans-serif";
  ctx.fillStyle = COLOR_WHITE;
  ctx.strokeStyle = COLOR_NAVY;
  ctx.lineWidth = 3;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.strokeText(label, cx, cy);
  ctx.fillText(label, cx, cy);
  ctx.restore();
}

function computeMinAreaRect(points: Point[]): Point[] {
  if (points.length < 4) return [];
  const pts = points.map((p) => [p.x, p.y]);
  const meanX = pts.reduce((s, p) => s + p[0], 0) / pts.length;
  const meanY = pts.reduce((s, p) => s + p[1], 0) / pts.length;
  const centered = pts.map(([x, y]) => [x - meanX, y - meanY]);

  let bestAngle = 0;
  let minArea = Infinity;
  let bestBox: Point[] = [];

  for (let angle = 0; angle < 90; angle += 1) {
    const rad = (angle * Math.PI) / 180;
    const cosA = Math.cos(rad);
    const sinA = Math.sin(rad);

    let minPx = Infinity, maxPx = -Infinity;
    let minPy = Infinity, maxPy = -Infinity;

    for (const [x, y] of centered) {
      const px = x * cosA + y * sinA;
      const py = -x * sinA + y * cosA;
      if (px < minPx) minPx = px;
      if (px > maxPx) maxPx = px;
      if (py < minPy) minPy = py;
      if (py > maxPy) maxPy = py;
    }

    const area = (maxPx - minPx) * (maxPy - minPy);
    if (area < minArea) {
      minArea = area;
      bestAngle = angle;
      const radB = (angle * Math.PI) / 180;
      const cosB = Math.cos(radB);
      const sinB = Math.sin(radB);

      const corners: Point[] = [
        { x: minPx, y: minPy },
        { x: maxPx, y: minPy },
        { x: maxPx, y: maxPy },
        { x: minPx, y: maxPy },
      ];
      bestBox = corners.map((p) => ({
        x: p.x * cosB - p.y * sinB + meanX,
        y: p.x * sinB + p.y * cosB + meanY,
      }));
    }
  }
  return bestBox;
}

function pointDistance(a: Point, b: Point): number {
  return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);
}

function polygonArea(points: Point[]): number {
  if (points.length < 3) return 0;
  let area = 0;
  for (let i = 0; i < points.length; i++) {
    const j = (i + 1) % points.length;
    area += points[i].x * points[j].y;
    area -= points[j].x * points[i].y;
  }
  return Math.abs(area) / 2;
}

export function useCanvasDrawing() {
  const redrawRef = useRef<((ctx: CanvasRenderingContext2D, state: SessionState) => void) | null>(null);

  const redraw = useCallback(async (
    ctx: CanvasRenderingContext2D,
    state: SessionState,
    activeArray: ActiveArrayData | null
  ) => {
    const img = state.imageElement;
    if (!img) return;

    const dw = state.displayWidth;
    const dh = state.displayHeight;

    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    ctx.drawImage(img, 0, 0, dw, dh);

    const refZoom = state.constants?.REFERENCE_ZOOM_IN ?? REFERENCE_ZOOM;

    if (!state.referencePoints && state.scaleFactor == null) {
      const sx = img.width - ZOOM_CROP_W;
      const sy = img.height - ZOOM_CROP_H;
      const zoomW = ZOOM_CROP_W * refZoom;
      const zoomH = ZOOM_CROP_H * refZoom;
      ctx.drawImage(
        img,
        sx, sy, ZOOM_CROP_W, ZOOM_CROP_H,
        dw - zoomW, dh - zoomH, zoomW, zoomH
      );
      ctx.strokeStyle = COLOR_CALIBRATION;
      ctx.lineWidth = 2;
      ctx.strokeRect(dw - zoomW, dh - zoomH, zoomW, zoomH);

      if (state.points.length > 0) {
        const last = state.points[state.points.length - 1];
        drawCircle(ctx, last.x, last.y, BIG_DOT_RADIUS, COLOR_PURPLE, COLOR_WHITE);
      }
      return;
    }

    for (const set of state.prohibitedPermanentSets) {
      if (set.length >= 3) {
        drawPolygon(ctx, {
          corners: set.map((p) => [p.x, p.y] as [number, number]),
          fill: COLOR_KEEPOUT_FILL,
          stroke: COLOR_KEEPOUT_OUTLINE,
          stipple: true,
        });
      }
    }

    for (const set of state.prohibitedPermanentSets) {
      if (set.length >= 3) {
        for (const p of set) {
          drawDot(ctx, p, COLOR_KEEPOUT_DOT, DOT_RADIUS);
        }
      }
    }

    const allArrays: ({ type: "saved"; data: SavedArrayData } | { type: "active"; data: ActiveArrayData })[] = [
      ...state.arrays.map((a) => ({ type: "saved" as const, data: a })),
    ];
    if (activeArray && activeArray.panelType && activeArray.panelPoints.length >= 4 && state.alreadyDrawPanel) {
      allArrays.push({ type: "active" as const, data: activeArray });
    }

    for (let idx = 0; idx < allArrays.length; idx++) {
      const entry = allArrays[idx];
      const arr = entry.data;

      try {
        const payload = buildSolarArrayPayload(arr);
        const [sbr, arrangeData] = await Promise.all([
          api.setbackRect(payload),
          api.arrange(payload, state.prohibitedPermanentSets),
        ]);

        if (sbr) {
          drawPolygon(ctx, {
            corners: sbr.corners,
            fill: COLOR_GOLD,
            stroke: COLOR_NAVY,
            lineWidth: 2,
          });

          drawAngleLabel(ctx, sbr.center, sbr.size, sbr.angle);

          if (sbr.corners.length === 4) {
            for (const c of sbr.corners) {
              drawCircle(ctx, c[0], c[1], 4, COLOR_BLUE, COLOR_WHITE);
            }
          }
        }

        for (let pi = 0; pi < arrangeData.panel_corners.length; pi++) {
          const corners = arrangeData.panel_corners[pi];
          drawPolygon(ctx, {
            corners,
            fill: COLOR_PANEL,
            stroke: COLOR_NAVY,
            lineWidth: 1,
          });
        }

        if (arrangeData.panel_corners.length > 0) {
          const first = arrangeData.panel_corners[0];
          if (first.length >= 4) {
            const cx = first.reduce((s, c) => s + c[0], 0) / first.length;
            const cy = first.reduce((s, c) => s + c[1], 0) / first.length;
            drawCircle(ctx, cx, cy, 4, COLOR_GREEN, COLOR_WHITE);
          }
        }

        if (entry.type === "saved" && arr.panelPoints.length >= 4) {
          const label = `PV_${(entry.data as SavedArrayData).id}`;
          drawTextLabel(ctx, arr.panelPoints, label);
        }
      } catch (e) {
        console.error("draw error", e);
      }
    }

    if (state.referencePoints) {
      for (const rp of state.referencePoints) {
        drawDot(ctx, rp, COLOR_PURPLE, BIG_DOT_RADIUS);
      }
    }

    for (let i = 0; i < state.points.length; i++) {
      drawDot(ctx, state.points[i], COLOR_YELLOW, DOT_RADIUS);
    }

    if (state.points.length >= 2) {
      ctx.beginPath();
      ctx.moveTo(state.points[0].x, state.points[0].y);
      for (let i = 1; i < state.points.length; i++) {
        ctx.lineTo(state.points[i].x, state.points[i].y);
      }
      if (state.points.length === 4) {
        ctx.closePath();
      }
      ctx.strokeStyle = COLOR_ORANGE;
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    if (state.points.length === 4) {
      const rect = computeMinAreaRect(state.points);
      if (rect.length === 4) {
        const corners = rect.map((p) => [p.x, p.y] as [number, number]);
        drawPolygon(ctx, {
          corners,
          fill: "transparent",
          stroke: COLOR_BLUE,
          lineWidth: 2,
        });

        if (activeArray && activeArray.panelPoints.length === 4) {
          const apCorners = activeArray.panelPoints.map((p) => [p.x, p.y] as [number, number]);
          drawPolygon(ctx, {
            corners: apCorners,
            fill: "transparent",
            stroke: COLOR_ORANGE,
            lineWidth: 2,
          });
        }

        for (const p of rect) {
          drawCircle(ctx, p.x, p.y, 4, COLOR_BLUE, COLOR_WHITE);
        }
      }
    }

    if (state.prohibitedPoints.length > 0) {
      for (let i = 0; i < state.prohibitedPoints.length; i++) {
        drawDot(ctx, state.prohibitedPoints[i], COLOR_KEEPOUT_DOT, DOT_RADIUS);
      }
      if (state.prohibitedPoints.length >= 2) {
        ctx.beginPath();
        ctx.moveTo(state.prohibitedPoints[0].x, state.prohibitedPoints[0].y);
        for (let i = 1; i < state.prohibitedPoints.length; i++) {
          ctx.lineTo(state.prohibitedPoints[i].x, state.prohibitedPoints[i].y);
        }
        if (state.prohibitedPoints.length === 4) {
          ctx.closePath();
        }
        ctx.strokeStyle = COLOR_KEEPOUT_OUTLINE;
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    }
  }, []);

  return { redraw };
}
