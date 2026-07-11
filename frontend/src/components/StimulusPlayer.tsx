import { useEffect, useRef, useState } from "react";

export interface Phase {
  duration: number;
  label: string;
  render: () => React.ReactNode;
}

interface Props {
  phases: Phase[];
  onComplete: () => void;
}

export default function StimulusPlayer({ phases, onComplete }: Props) {
  const [phaseIndex, setPhaseIndex] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  useEffect(() => {
    setElapsed(0);
    const interval = setInterval(() => setElapsed((p) => p + 0.1), 100);
    const timeout = setTimeout(() => {
      clearInterval(interval);
      if (phaseIndex < phases.length - 1) {
        setPhaseIndex((i) => i + 1);
      } else {
        onCompleteRef.current();
      }
    }, phases[phaseIndex].duration * 1000);
    return () => { clearInterval(interval); clearTimeout(timeout); };
  }, [phaseIndex, phases]);

  const phase = phases[phaseIndex];
  const progress = Math.min((elapsed / phase.duration) * 100, 100);

  return (
    <div className="flex flex-col gap-4 w-full">
      <div className="text-center">
        <span className="text-xs font-mono uppercase tracking-widest text-teal-500">
          {phaseIndex + 1} / {phases.length}
        </span>
        <p className="text-xl font-semibold mt-1" style={{ color: "var(--text)" }}>{phase.label}</p>
      </div>

      <div className="relative w-full aspect-video rounded-2xl overflow-hidden shadow-2xl border border-ui">
        {phase.render()}
      </div>

      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "var(--border)" }}>
        <div className="h-full rounded-full transition-all duration-100 bg-teal-500"
          style={{ width: `${progress}%` }}/>
      </div>
    </div>
  );
}
