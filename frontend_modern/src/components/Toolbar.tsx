"use client";

import { useRef, useCallback } from "react";
import { useSession } from "@/hooks/useSession";
import { api, buildSolarArrayPayload } from "@/services/apiClient";

interface ToolbarProps {
  areaLabel: string;
  distanceLabel: string;
  totalLabel: string;
  onCalculate: () => void;
}

export default function Toolbar({ areaLabel, distanceLabel, totalLabel, onCalculate }: ToolbarProps) {
  const { state, setState, resetActive, resetAll, loadImage, savePanel, fetchResults } = useSession();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleBrowse = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      try {
        const [constants, panelTypes] = await Promise.all([
          api.getConstants(),
          api.getPanelTypes(),
        ]);
        setState((s) => ({ ...s, constants, panelTypes }));
        await loadImage(file);
      } catch (err) {
        alert("Failed to load image or connect to backend");
        console.error(err);
      }
    },
    [loadImage, setState]
  );

  const updateGapInput = useCallback(
    (field: "gw" | "gh" | "walk" | "setback", value: string) => {
      setState((s) => ({
        ...s,
        gapInputs: { ...s.gapInputs, [field]: value },
      }));
    },
    [setState]
  );

  const recalcGaps = useCallback(() => {
    setState((s) => {
      if (!s.scaleFactor || !s.activeArray?.panelType) return s;
      const sf = s.scaleFactor;
      const active = { ...s.activeArray };
      const gw = parseFloat(s.gapInputs.gw) || 0;
      const gh = parseFloat(s.gapInputs.gh) || 0;
      const walk = parseFloat(s.gapInputs.walk) || 0;
      const setback = parseFloat(s.gapInputs.setback) || 0;

      const gapWPx = gw / sf;
      const gapHPx = gh / sf;
      const walkPx = walk / sf;

      const p = active.panelType!;
      let sw = p.width_m / sf;
      let sh = p.height_m / sf;
      if (active.panelRotationTick === 1) {
        [sw, sh] = [sh, sw];
      }
      active.smallRectSize = [sw, sh];
      active.setbackLength = setback / sf;

      let bg_w: number, bg_h: number, sg_w: number, sg_h: number;
      if (active.walkGapRotationTick === 1) {
        bg_w = walkPx; bg_h = gapHPx;
        sg_w = gapWPx; sg_h = gapHPx;
      } else {
        bg_w = gapWPx; bg_h = walkPx;
        sg_w = gapWPx; sg_h = gapHPx;
      }
      const gwp = (bg_w + sg_w) / 2;
      const ghp = (bg_h + sg_h) / 2;
      active.gapSize = [bg_w, bg_h, sg_w, sg_h, gwp, ghp];
      active.panelPoints = s.activeArray?.panelPoints || [];

      return { ...s, activeArray: active };
    });
  }, [setState]);

  const handlePanelRotate = useCallback(() => {
    setState((s) => {
      if (!s.activeArray) return s;
      const active = { ...s.activeArray, panelRotationTick: s.activeArray.panelRotationTick === 1 ? 0 : 1 };
      return { ...s, activeArray: active };
    });
    setTimeout(recalcGaps, 0);
  }, [setState, recalcGaps]);

  const handleWalkRotate = useCallback(() => {
    setState((s) => {
      if (!s.activeArray) return s;
      const active = { ...s.activeArray, walkGapRotationTick: s.activeArray.walkGapRotationTick === 1 ? 0 : 1 };
      return { ...s, activeArray: active };
    });
    setTimeout(recalcGaps, 0);
  }, [setState, recalcGaps]);

  const handlePanelTypeChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      const name = e.target.value;
      const found = state.panelTypes.find((p) => p.name === name) || null;
      setState((s) => {
        const active = s.activeArray || createDefaultActive();
        return { ...s, activeArray: { ...active, panelType: found } };
      });
      setTimeout(recalcGaps, 0);
    },
    [state.panelTypes, setState, recalcGaps]
  );

  const handlePVPanel = useCallback(async () => {
    recalcGaps();
    setTimeout(async () => {
      setState((s) => {
        if (!s.activeArray?.panelType) { alert("Select a panel type first"); return s; }
        if ((s.activeArray.panelPoints?.length || 0) < 4) { alert("Draw 4 boundary points first"); return s; }
        return { ...s, alreadyDrawPanel: true };
      });
      setTimeout(() => onCalculate(), 100);
    }, 50);
  }, [recalcGaps, setState, onCalculate]);

  const handleKeepout = useCallback(() => {
    setState((s) => {
      if (s.prohibitedPoints.length < 4) return s;
      return {
        ...s,
        prohibitedPermanentSets: [...s.prohibitedPermanentSets, [...s.prohibitedPoints]],
        prohibitedPoints: [],
      };
    });
  }, [setState]);

  const canPVPanel = state.points.length === 4 && !state.alreadyDrawPanel;
  const canSave = state.alreadyDrawPanel && state.activeArray?.panelType != null;
  const canClear = state.points.length > 0;
  const canKeepout = state.prohibitedPoints.length === 4;

  return (
    <div className="space-y-3">
      <input
        ref={fileInputRef}
        type="file"
        accept=".png,.jpg,.jpeg,.gif"
        className="hidden"
        onChange={handleFileChange}
      />

      <div className="flex flex-wrap gap-2 items-center">
        <button
          onClick={handleBrowse}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium"
        >
          Browse Image
        </button>
      </div>

      <div className="flex flex-wrap gap-3 items-end">
        <div>
          <label className="block text-xs text-gray-600 mb-0.5">GW (m)</label>
          <input
            type="number"
            step="0.1"
            value={state.gapInputs.gw}
            onChange={(e) => updateGapInput("gw", e.target.value)}
            onBlur={recalcGaps}
            className="w-16 px-2 py-1 border rounded text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-600 mb-0.5">GH (m)</label>
          <input
            type="number"
            step="0.1"
            value={state.gapInputs.gh}
            onChange={(e) => updateGapInput("gh", e.target.value)}
            onBlur={recalcGaps}
            className="w-16 px-2 py-1 border rounded text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-600 mb-0.5">Walk (m)</label>
          <input
            type="number"
            step="0.1"
            value={state.gapInputs.walk}
            onChange={(e) => updateGapInput("walk", e.target.value)}
            onBlur={recalcGaps}
            className="w-16 px-2 py-1 border rounded text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-600 mb-0.5">Setback (m)</label>
          <input
            type="number"
            step="0.1"
            value={state.gapInputs.setback}
            onChange={(e) => updateGapInput("setback", e.target.value)}
            onBlur={recalcGaps}
            className="w-16 px-2 py-1 border rounded text-sm"
          />
        </div>

        <label className="flex items-center gap-1 text-sm cursor-pointer select-none">
          <input
            type="checkbox"
            checked={state.activeArray?.panelRotationTick === 1}
            onChange={handlePanelRotate}
          />
          P↻
        </label>
        <label className="flex items-center gap-1 text-sm cursor-pointer select-none">
          <input
            type="checkbox"
            checked={state.activeArray?.walkGapRotationTick === 1}
            onChange={handleWalkRotate}
          />
          W↻
        </label>
      </div>

      <div className="flex flex-wrap gap-2 items-center">
        <select
          value={state.activeArray?.panelType?.name || ""}
          onChange={handlePanelTypeChange}
          className="px-2 py-1 border rounded text-sm"
        >
          <option value="">-- Select Panel --</option>
          {state.panelTypes.map((pt) => (
            <option key={pt.name} value={pt.name}>
              {pt.name}
            </option>
          ))}
        </select>

        <button
          onClick={handlePVPanel}
          disabled={!canPVPanel}
          className="px-3 py-1.5 rounded text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed bg-green-600 text-white hover:bg-green-700"
        >
          PV Panel
        </button>
        <button
          onClick={savePanel}
          disabled={!canSave}
          className="px-3 py-1.5 rounded text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed bg-blue-600 text-white hover:bg-blue-700"
        >
          Save
        </button>
        <button
          onClick={resetActive}
          disabled={!canClear}
          className="px-3 py-1.5 rounded text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed bg-yellow-600 text-white hover:bg-yellow-700"
        >
          Clear
        </button>
        <button
          onClick={handleKeepout}
          disabled={!canKeepout}
          className="px-3 py-1.5 rounded text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed bg-red-600 text-white hover:bg-red-700"
        >
          Keepout
        </button>
        <button
          onClick={resetAll}
          className="px-3 py-1.5 rounded text-sm font-medium bg-gray-600 text-white hover:bg-gray-700"
        >
          Clear All
        </button>
      </div>

      <div className="text-sm space-y-0.5 text-gray-700">
        <div>Area: {areaLabel}</div>
        <div>Distance: {distanceLabel}</div>
      </div>

      <div className="text-sm font-medium text-gray-800">
        {totalLabel}
      </div>
    </div>
  );
}

function createDefaultActive() {
  return {
    panelPoints: [] as { x: number; y: number }[],
    panelType: null as { name: string; power_W: number; width_m: number; height_m: number; model_str: string } | null,
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
