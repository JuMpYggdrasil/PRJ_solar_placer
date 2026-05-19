export interface Point {
  x: number;
  y: number;
}

export interface PanelTypeData {
  name: string;
  power_W: number;
  width_m: number;
  height_m: number;
  model_str: string;
}

export interface RectResult {
  center: [number, number];
  size: [number, number];
  angle: number;
  corners: [[number, number], [number, number], [number, number], [number, number]];
}

export interface ArrangeResult {
  total_count: number;
  horizontal_count: number;
  vertical_count: number;
  intersect_keepout_count: number;
  kWp: number;
  angle: number;
  positions: [number, number][];
  panel_corners: [[number, number], [number, number], [number, number], [number, number]][];
}

export type GapSize = [number, number, number, number, number, number];

export interface ActiveArrayData {
  panelPoints: Point[];
  panelType: PanelTypeData | null;
  setbackLength: number;
  gapSize: GapSize | null;
  smallRectSize: [number, number] | null;
  panelRotationTick: number;
  walkGapRotationTick: number;
  totalPanelCount: number;
  horizontalPanelCount: number;
  verticalPanelCount: number;
  intersectKeepoutCount: number;
  kWp: number;
  azimuthAngle: number;
}

export interface SavedArrayData extends ActiveArrayData {
  id: number;
}

export interface SessionState {
  imageElement: HTMLImageElement | null;
  originalWidth: number;
  originalHeight: number;
  displayWidth: number;
  displayHeight: number;
  scaleFactor: number | null;
  referencePoints: [Point, Point] | null;
  points: Point[];
  prohibitedPoints: Point[];
  prohibitedPermanentSets: Point[][];
  arrays: SavedArrayData[];
  activeArray: ActiveArrayData | null;
  alreadyDrawPanel: boolean;
  selectedListboxIndex: number | null;
  constants: { REFERENCE_ZOOM_IN: number } | null;
  panelTypes: PanelTypeData[];
  gapInputs: {
    gw: string;
    gh: string;
    walk: string;
    setback: string;
  };
}

export interface ConstantsData {
  REFERENCE_ZOOM_IN: number;
}
