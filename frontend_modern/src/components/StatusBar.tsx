"use client";

import { useSession } from "@/hooks/useSession";

export default function StatusBar() {
  const { state } = useSession();

  const scaleText = state.scaleFactor != null
    ? `Scale: ${state.scaleFactor.toFixed(5)} m/px`
    : "Scale: --";

  const coordText = "--";

  const panelCount = state.arrays.reduce((sum, arr) => sum + arr.totalPanelCount, 0);

  const infoText = state.activeArray?.kWp
    ? `${state.activeArray.totalPanelCount} panels, ${state.activeArray.kWp.toFixed(2)} kWp`
    : "--";

  return (
    <div className="flex flex-wrap gap-4 text-xs text-gray-600 px-1 py-1.5 bg-gray-100 rounded border-t border-gray-200">
      <span>{scaleText}</span>
      <span>Coords: {coordText}</span>
      <span>Panels: {panelCount}</span>
      <span>{infoText}</span>
    </div>
  );
}
