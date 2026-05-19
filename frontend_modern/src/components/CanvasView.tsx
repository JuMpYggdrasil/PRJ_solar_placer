"use client";

import { useRef, useEffect, useCallback, useState } from "react";
import type { SessionState, ActiveArrayData, Point } from "@/types";
import { useSession } from "@/hooks/useSession";
import { useCanvasDrawing } from "@/hooks/useCanvasDrawing";
import { api } from "@/services/apiClient";

interface CanvasViewProps {
  onUpdateLabels: (area: string, distance: string) => void;
}

export default function CanvasView({ onUpdateLabels }: CanvasViewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { state, setState } = useSession();
  const { redraw } = useCanvasDrawing();
  const awaitingRef = useRef(false);
  const redrawTimerRef = useRef<number | null>(null);

  const scheduleRedraw = useCallback(() => {
    if (redrawTimerRef.current) clearTimeout(redrawTimerRef.current);
    redrawTimerRef.current = window.setTimeout(() => {
      const ctx = canvasRef.current?.getContext("2d");
      if (ctx && state.imageElement) {
        redraw(ctx, state, state.activeArray);
      }
    }, 50);
  }, [state, redraw]);

  useEffect(() => {
    const ctx = canvasRef.current?.getContext("2d");
    if (ctx && state.imageElement) {
      redraw(ctx, state, state.activeArray);
    }
  }, [state, state.activeArray, redraw]);

  const handleCanvasClick = useCallback(
    async (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!canvasRef.current || !state.imageElement) return;
      if (awaitingRef.current) return;

      const canvas = canvasRef.current;
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      const x = (e.clientX - rect.left) * scaleX;
      const y = (e.clientY - rect.top) * scaleY;
      const pt: Point = { x, y };

      if (!state.referencePoints) {
        if (state.points.length === 0) {
          setState((s) => ({ ...s, points: [pt] }));
          return;
        }
        if (state.points.length === 1) {
          const p1 = state.points[0];
          const p2 = pt;
          const pxDist = Math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2);
          const refZoom = state.constants?.REFERENCE_ZOOM_IN ?? 3;

          const entered = prompt("Enter distance between reference points (meters):");
          if (!entered) {
            setState((s) => ({
              ...s,
              points: [],
              referencePoints: null,
              scaleFactor: null,
            }));
            return;
          }
          const realDist = parseFloat(entered);
          if (isNaN(realDist) || realDist <= 0) {
            alert("Invalid distance");
            return;
          }

          const sf = realDist / pxDist / refZoom;
          const dw = state.displayWidth;
          const dh = state.displayHeight;
          const ref1: Point = {
            x: (p1.x + 2 * dw) / 3,
            y: (p1.y + 2 * dh) / 3,
          };
          const ref2: Point = {
            x: (p2.x + 2 * dw) / 3,
            y: (p2.y + 2 * dh) / 3,
          };

          setState((s) => ({
            ...s,
            referencePoints: [ref1, ref2],
            scaleFactor: sf,
            points: [],
          }));
          return;
        }
        return;
      }

      for (const arr of state.arrays) {
        if (arr.panelPoints.length >= 4) {
          try {
            const res = await api.pointInPolygon(x, y, arr.panelPoints);
            if (res.inside) return;
          } catch { }
        }
      }

      if (state.activeArray && state.activeArray.panelPoints.length >= 4) {
        try {
          const res = await api.pointInPolygon(x, y, state.activeArray.panelPoints);
          if (res.inside) return;
        } catch { }
      }

      awaitingRef.current = true;
      setState((s) => {
        let newPoints = [...s.points, pt];
        if (newPoints.length > 4) {
          newPoints = newPoints.slice(newPoints.length - 4);
        }

        if (newPoints.length === 4) {
          try {
            const area = polygonArea(newPoints);
            const areaM2 = area * (s.scaleFactor ?? 1) ** 2;
            onUpdateLabels(areaM2.toFixed(2), "");

            const active = s.activeArray || createDefaultActive();
            active.panelPoints = [...newPoints];
            return {
              ...s,
              points: newPoints,
              activeArray: active,
            };
          } catch { }
        }

        if (newPoints.length >= 2 && s.scaleFactor) {
          const dist = pointDistance(newPoints[0], newPoints[newPoints.length - 1]) * s.scaleFactor;
          onUpdateLabels("", dist.toFixed(2));
          if (newPoints.length >= 3) {
            try {
              const area = polygonArea(newPoints);
              const areaM2 = area * (s.scaleFactor ?? 1) ** 2;
              onUpdateLabels(areaM2.toFixed(2), dist.toFixed(2));
            } catch { }
          }
        }

        return { ...s, points: newPoints };
      });
      awaitingRef.current = false;
    },
    [state, setState, onUpdateLabels]
  );

  const handleRightClick = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      e.preventDefault();
      if (!canvasRef.current || !state.imageElement) return;

      const canvas = canvasRef.current;
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      const x = (e.clientX - rect.left) * scaleX;
      const y = (e.clientY - rect.top) * scaleY;
      const pt: Point = { x, y };

      setState((s) => {
        let newPts = [...s.prohibitedPoints, pt];
        if (newPts.length > 4) {
          newPts = newPts.slice(newPts.length - 4);
        }
        return { ...s, prohibitedPoints: newPts };
      });
    },
    [state, setState]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!canvasRef.current || !state.imageElement) return;
      const canvas = canvasRef.current;
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      const x = (e.clientX - rect.left) * scaleX;
      const y = (e.clientY - rect.top) * scaleY;
    },
    [state.imageElement]
  );

  useEffect(() => {
    if (state.imageElement && canvasRef.current) {
      canvasRef.current.width = state.displayWidth;
      canvasRef.current.height = state.displayHeight;
    }
  }, [state.imageElement, state.displayWidth, state.displayHeight]);

  if (!state.imageElement) {
    return (
      <div className="flex items-center justify-center bg-gray-200 rounded-lg"
        style={{ width: 800, height: 500 }}>
        <p className="text-gray-500 text-lg">Load an image to begin</p>
      </div>
    );
  }

  return (
    <canvas
      ref={canvasRef}
      className="border border-gray-300 rounded-lg cursor-crosshair bg-gray-100"
      style={{ width: state.displayWidth, height: state.displayHeight }}
      onClick={handleCanvasClick}
      onContextMenu={handleRightClick}
      onMouseMove={handleMouseMove}
    />
  );
}

function createDefaultActive() {
  return {
    panelPoints: [] as Point[],
    panelType: null,
    setbackLength: 0,
    gapSize: null as [number, number, number, number, number, number] | null,
    smallRectSize: null as [number, number] | null,
    panelRotationTick: 0,
    walkGapRotationTick: 0,
    totalPanelCount: 0,
    horizontalPanelCount: 0,
    verticalPanelCount: 0,
    intersectKeepoutCount: 0,
    kWp: 0,
    azimuthAngle: 0,
  };
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

function pointDistance(a: Point, b: Point): number {
  return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);
}
