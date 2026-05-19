"use client";

import { useState, useCallback, useEffect } from "react";
import { SessionProvider, useSession } from "@/hooks/useSession";
import CanvasView from "@/components/CanvasView";
import Toolbar from "@/components/Toolbar";
import PanelListbox from "@/components/PanelListbox";
import StatusBar from "@/components/StatusBar";
import { api, buildSolarArrayPayload } from "@/services/apiClient";

function AppContent() {
  const { state, fetchResults } = useSession();
  const [areaLabel, setAreaLabel] = useState("--");
  const [distanceLabel, setDistanceLabel] = useState("--");

  const updateLabels = useCallback((area: string, distance: string) => {
    if (area) setAreaLabel(`${area} m²`);
    if (distance) setDistanceLabel(`${distance} m`);
  }, []);

  const totalLabel = state.activeArray?.kWp
    ? `Azimuth: ${state.activeArray.azimuthAngle.toFixed(2)}°, ` +
      `${state.activeArray.horizontalPanelCount}×${state.activeArray.verticalPanelCount} panels | ` +
      `kWp: ${state.activeArray.kWp.toFixed(2)}`
    : "";

  const handleCalculate = useCallback(async () => {
    await fetchResults();
  }, [fetchResults]);

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-2 shadow-sm">
        <h1 className="text-lg font-semibold text-gray-800">Solar Panel Placer</h1>
      </header>

      <div className="flex flex-1 gap-4 p-4">
        <div className="flex flex-col gap-4 flex-1 min-w-0">
          <div className="flex justify-center">
            <CanvasView onUpdateLabels={updateLabels} />
          </div>
          <Toolbar
            areaLabel={areaLabel}
            distanceLabel={distanceLabel}
            totalLabel={totalLabel}
            onCalculate={handleCalculate}
          />
          <StatusBar />
        </div>

        <aside className="w-56 flex-shrink-0">
          <PanelListbox />
        </aside>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <SessionProvider>
      <AppContent />
    </SessionProvider>
  );
}
