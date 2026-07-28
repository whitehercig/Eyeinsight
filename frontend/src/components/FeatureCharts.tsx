import { useMemo, useState } from "react";

type Frame = Record<string, number | string | null>;
type Phase = Record<string, number | string | null>;

interface Props {
  frames: Frame[];
  phases: Phase[];
  labels: { attention: string; movement: string; blink: string; visibility: string; tracking: string; away: string; phases: string; phaseNames: Record<string, string> };
}

const metrics = [
  ["attention", "usable_frame"],
  ["movement", "head_motion"],
  ["blink", "blink_probability"],
  ["visibility", "face_detected"],
  ["tracking", "tracking_confidence"],
  ["away", "looking_away"],
] as const;

export default function FeatureCharts({ frames, phases, labels }: Props) {
  const [metric, setMetric] = useState<(typeof metrics)[number][0]>("attention");
  const [hovered, setHovered] = useState<number | null>(null);
  const field = metrics.find(([name]) => name === metric)?.[1] ?? "usable_frame";
  const points = useMemo(() => frames.map((frame, index) => ({
    x: frames.length > 1 ? (index / (frames.length - 1)) * 100 : 0,
    y: Math.max(0, Math.min(1, Number(frame[field] ?? 0))),
    time: Number(frame.timestamp ?? 0),
  })), [frames, field]);
  const path = points.map((point, index) => `${index ? "L" : "M"}${point.x.toFixed(2)},${(100 - point.y * 92 - 4).toFixed(2)}`).join(" ");
  const selected = hovered === null ? null : points[hovered];

  if (!frames.length) return null;
  return (
    <div className="card-glass p-5 mt-4">
      <div className="flex flex-wrap gap-2 mb-4">
        {metrics.map(([name]) => (
          <button key={name} onClick={() => setMetric(name)} className="px-2 py-1 text-xs rounded border" style={{ borderColor: metric === name ? "#14b8a6" : "var(--border)", color: metric === name ? "#14b8a6" : "var(--text-muted)" }}>{labels[name]}</button>
        ))}
      </div>
      <div className="relative h-44">
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full" onMouseMove={(event) => setHovered(Math.min(points.length - 1, Math.max(0, Math.round((event.nativeEvent.offsetX / event.currentTarget.clientWidth) * (points.length - 1)))))} onMouseLeave={() => setHovered(null)}>
          <path d="M0,96 L100,96" stroke="rgba(148,163,184,.3)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
          <path d={path} fill="none" stroke="#14b8a6" strokeWidth="2" vectorEffect="non-scaling-stroke" />
          {selected && <circle cx={selected.x} cy={100 - selected.y * 92 - 4} r="2.5" fill="#f8fafc" stroke="#14b8a6" strokeWidth="1" vectorEffect="non-scaling-stroke" />}
        </svg>
        {selected && <span className="absolute top-1 right-1 text-xs font-mono text-ui-muted">{selected.time.toFixed(1)}s · {(selected.y * 100).toFixed(0)}%</span>}
      </div>
      {phases.length > 0 && <div className="mt-6"><p className="text-xs uppercase tracking-widest text-ui-subtle mb-3">{labels.phases}</p><div className="space-y-2">{phases.map((phase) => { const ratio = Math.max(0, Math.min(1, Number(phase.attention_ratio ?? 0))); const phaseName = String(phase.phase); return <div key={phaseName} className="flex items-center gap-3 text-xs"><span className="w-28 truncate text-ui-muted">{labels.phaseNames[phaseName] ?? phaseName}</span><div className="flex-1 h-2 rounded" style={{ background: "var(--meter-track)" }}><div className="h-full rounded bg-teal-500" style={{ width: `${ratio * 100}%` }} /></div><span className="w-8 text-right text-ui-muted">{(ratio * 100).toFixed(0)}%</span></div>; })}</div></div>}
    </div>
  );
}
