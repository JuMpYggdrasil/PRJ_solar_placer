"use client";

import { useSession } from "@/hooks/useSession";

export default function PanelListbox() {
  const { state, editArray, deleteArray } = useSession();

  return (
    <div className="border rounded-lg p-3 bg-gray-50">
      <h3 className="text-sm font-semibold mb-2 text-gray-700">Saved Arrays</h3>
      <div className="space-y-1 max-h-48 overflow-y-auto">
        {state.arrays.length === 0 && (
          <p className="text-xs text-gray-400 italic">No saved arrays</p>
        )}
        {state.arrays.map((arr) => (
          <div
            key={arr.id}
            className={`flex items-center justify-between px-2 py-1.5 rounded text-sm cursor-pointer ${
              state.selectedListboxIndex === state.arrays.indexOf(arr)
                ? "bg-blue-100 border border-blue-300"
                : "hover:bg-gray-100"
            }`}
            onClick={() => editArray(arr.id)}
          >
            <span>
              PV_{arr.id}: {arr.kWp.toFixed(1)} kW
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                deleteArray(arr.id);
              }}
              className="text-red-500 hover:text-red-700 text-xs ml-2"
              title="Delete"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
