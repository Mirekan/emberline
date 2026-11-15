export type SceneParams = {
  heat: number;
  cool: number;
  camY: number;
  camZ: number;
};

export const stageState = {
  progress: 0,
  smoothProgress: 0,
  pointerX: 0,
  pointerY: 0,
  smoothPointerX: 0,
  smoothPointerY: 0,
  reducedMotion: false,
};

export function sceneParamsFor(progress: number): SceneParams {
  const keys: Array<{ at: number; heat: number; cool: number; camY: number; camZ: number }> = [
    { at: 0, heat: 0.42, cool: 0, camY: 8.6, camZ: 29 },
    { at: 0.34, heat: 0.78, cool: 0, camY: 6.6, camZ: 23.5 },
    { at: 0.58, heat: 1, cool: 0, camY: 5, camZ: 19.5 },
    { at: 0.8, heat: 0.7, cool: 0.35, camY: 6.6, camZ: 23 },
    { at: 1, heat: 0.4, cool: 1, camY: 9.6, camZ: 30.5 },
  ];
  const p = Math.min(1, Math.max(0, progress));
  let start = keys[0];
  let end = keys[keys.length - 1];

  for (let i = 0; i < keys.length - 1; i++) {
    if (p <= keys[i + 1].at) {
      start = keys[i];
      end = keys[i + 1];
      break;
    }
  }

  const raw = (p - start.at) / (end.at - start.at || 1);
  const t = raw * raw * (3 - 2 * raw);
  const lerp = (a: number, b: number) => a + (b - a) * t;

  return {
    heat: lerp(start.heat, end.heat),
    cool: lerp(start.cool, end.cool),
    camY: lerp(start.camY, end.camY),
    camZ: lerp(start.camZ, end.camZ),
  };
}
