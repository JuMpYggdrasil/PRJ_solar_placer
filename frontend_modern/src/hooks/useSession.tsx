"use client";

import { createContext, useContext, useState, useCallback, useRef, type ReactNode } from "react";
import type { SessionState, ActiveArrayData, SavedArrayData, Point, GapSize } from "@/types";
import { api, buildSolarArrayPayload } from "@/services/apiClient";

function createEmptyActive(): ActiveArrayData {
  return {
    panelPoints: [],
    panelType: null,
    setbackLength: 0,
    gapSize: null,
    smallRectSize: null,
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

const defaultState: SessionState = {
  imageElement: null,
  originalWidth: 0,
  originalHeight: 0,
  displayWidth: 0,
  displayHeight: 0,
  scaleFactor: null,
  referencePoints: null,
  points: [],
  prohibitedPoints: [],
  prohibitedPermanentSets: [],
  arrays: [],
  activeArray: null,
  alreadyDrawPanel: false,
  selectedListboxIndex: null,
  constants: null,
  panelTypes: [],
  gapInputs: { gw: "0.2", gh: "0.2", walk: "0.7", setback: "0.5" },
};

let nextArrayId = 1;

interface SessionContextValue {
  state: SessionState;
  setState: React.Dispatch<React.SetStateAction<SessionState>>;
  resetActive: () => void;
  resetAll: () => void;
  loadImage: (file: File) => Promise<void>;
  savePanel: () => Promise<void>;
  editArray: (id: number) => void;
  deleteArray: (id: number) => void;
  fetchResults: () => Promise<void>;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<SessionState>({ ...defaultState });
  const loadedRef = useRef(false);

  const resetActive = useCallback(() => {
    setState((s) => ({
      ...s,
      points: [],
      prohibitedPoints: [],
      activeArray: null,
      alreadyDrawPanel: false,
      selectedListboxIndex: null,
    }));
  }, []);

  const resetAll = useCallback(() => {
    setState({ ...defaultState, panelTypes: state.panelTypes });
    loadedRef.current = false;
  }, [state.panelTypes]);

  const loadImage = useCallback(async (file: File) => {
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const i = new Image();
      i.onload = () => resolve(i);
      i.onerror = reject;
      i.src = URL.createObjectURL(file);
    });

    const dw = Math.round(img.width * 7 / 10);
    const dh = Math.round(img.height * 7 / 10);

    setState((s) => ({
      ...s,
      imageElement: img,
      originalWidth: img.width,
      originalHeight: img.height,
      displayWidth: dw,
      displayHeight: dh,
      referencePoints: null,
      scaleFactor: null,
      points: [],
      prohibitedPoints: [],
      prohibitedPermanentSets: [],
      arrays: [],
      activeArray: null,
      alreadyDrawPanel: false,
      selectedListboxIndex: null,
    }));
  }, []);

  const savePanel = useCallback(async () => {
    setState((s) => {
      if (!s.activeArray) return s;
      const saved: SavedArrayData = {
        ...JSON.parse(JSON.stringify(s.activeArray)),
        id: nextArrayId++,
      };
      return {
        ...s,
        arrays: [...s.arrays, saved],
        activeArray: null,
        alreadyDrawPanel: false,
        points: [],
        selectedListboxIndex: null,
      };
    });
  }, []);

  const editArray = useCallback((id: number) => {
    setState((s) => {
      const found = s.arrays.find((a) => a.id === id);
      if (!found) return s;
      const { id: _, ...active } = found;
      return {
        ...s,
        activeArray: { ...active, panelPoints: [...active.panelPoints] },
        points: [],
        alreadyDrawPanel: true,
        selectedListboxIndex: s.arrays.indexOf(found),
      };
    });
  }, []);

  const deleteArray = useCallback((id: number) => {
    setState((s) => ({
      ...s,
      arrays: s.arrays.filter((a) => a.id !== id),
      selectedListboxIndex: null,
    }));
  }, []);

  const fetchResults = useCallback(async () => {
    setState((s) => {
      if (!s.activeArray || !s.activeArray.panelType) return s;
      const active = s.activeArray;
      const payload = buildSolarArrayPayload(active);
      const prohibited = s.prohibitedPermanentSets;

      api.arrange(payload, prohibited).then((result) => {
        setState((prev) => {
          if (!prev.activeArray) return prev;
          return {
            ...prev,
            activeArray: {
              ...prev.activeArray,
              totalPanelCount: result.total_count,
              horizontalPanelCount: result.horizontal_count,
              verticalPanelCount: result.vertical_count,
              intersectKeepoutCount: result.intersect_keepout_count,
              kWp: result.kWp,
              azimuthAngle: result.angle,
            },
            alreadyDrawPanel: true,
          };
        });
      }).catch(console.error);

      return s;
    });
  }, []);

  return (
    <SessionContext.Provider
      value={{
        state,
        setState,
        resetActive,
        resetAll,
        loadImage,
        savePanel,
        editArray,
        deleteArray,
        fetchResults,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}
