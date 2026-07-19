type Heatmap = number[][];

interface GazePoint {
  timestamp: number;
  gaze_screen_x: number;
  gaze_screen_y: number;
  target_screen_x: number;
  target_screen_y: number;
  target_aligned: number;
}

interface Props {
  visualizations: { gaze_heatmap?: Heatmap; gaze_path?: GazePoint[] };
  labels: { heatmap: string; path: string; proxy: string; gaze: string; target: string };
}

const clamp = (value: number) => Math.max(0, Math.min(1, value));

export default function GazeVisualizations({ visualizations, labels }: Props) {
  const heatmap = visualizations.gaze_heatmap ?? [];
  const gazePath = (visualizations.gaze_path ?? []).filter((point) =>
    [point.gaze_screen_x, point.gaze_screen_y, point.target_screen_x, point.target_screen_y]
      .every((value) => Number.isFinite(value)),
  );
  const maxHeat = Math.max(1, ...heatmap.flat().map((value) => Number(value) || 0));
  const gazeLine = gazePath.map((point, index) => `${index ? "L" : "M"}${(clamp(point.gaze_screen_x) * 100).toFixed(1)},${((1 - clamp(point.gaze_screen_y)) * 100).toFixed(1)}`).join(" ");
  const targetLine = gazePath.map((point, index) => `${index ? "L" : "M"}${(clamp(point.target_screen_x) * 100).toFixed(1)},${((1 - clamp(point.target_screen_y)) * 100).toFixed(1)}`).join(" ");

  if (!heatmap.length && !gazePath.length) return null;

  return (
    <div className="card-glass p-5 mt-4 space-y-6">
      {heatmap.length > 0 && (
        <div>
          <h3 className="font-semibold text-sm uppercase tracking-widest mb-3 text-ui-muted">{labels.heatmap}</h3>
          <div className="grid gap-px rounded overflow-hidden border border-slate-700/50 bg-slate-900/40" style={{ gridTemplateColumns: `repeat(${heatmap[0].length}, minmax(0, 1fr))` }}>
            {heatmap.flatMap((row, rowIndex) => row.map((value, columnIndex) => {
              const intensity = clamp((Number(value) || 0) / maxHeat);
              return <span key={`${rowIndex}-${columnIndex}`} className="aspect-square" title={`${(intensity * 100).toFixed(0)}%`} style={{ backgroundColor: `rgba(20, 184, 166, ${0.05 + intensity * 0.9})` }} />;
            }))}
          </div>
        </div>
      )}

      {gazePath.length > 1 && (
        <div>
          <h3 className="font-semibold text-sm uppercase tracking-widest mb-3 text-ui-muted">{labels.path}</h3>
          <div className="h-56 rounded border border-slate-700/50 bg-slate-900/30 p-2">
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full" aria-label={labels.path}>
              {[25, 50, 75].map((position) => <g key={position}><line x1={position} y1="0" x2={position} y2="100" stroke="rgba(148,163,184,.15)" vectorEffect="non-scaling-stroke" /><line x1="0" y1={position} x2="100" y2={position} stroke="rgba(148,163,184,.15)" vectorEffect="non-scaling-stroke" /></g>)}
              <path d={targetLine} fill="none" stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="3 2" vectorEffect="non-scaling-stroke" />
              <path d={gazeLine} fill="none" stroke="#14b8a6" strokeWidth="2" vectorEffect="non-scaling-stroke" />
              <circle cx={clamp(gazePath[0].gaze_screen_x) * 100} cy={(1 - clamp(gazePath[0].gaze_screen_y)) * 100} r="1.8" fill="#f8fafc" vectorEffect="non-scaling-stroke" />
            </svg>
          </div>
          <div className="mt-2 flex gap-4 text-xs text-ui-muted"><span className="text-teal-400">— {labels.gaze}</span><span className="text-amber-400">- - {labels.target}</span></div>
        </div>
      )}
      <p className="text-xs leading-relaxed text-ui-subtle">{labels.proxy}</p>
    </div>
  );
}
