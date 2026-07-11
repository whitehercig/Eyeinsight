import { useApp } from "../context/AppContext";

interface Props {
  riskScore: number;
  riskLevel: "low" | "moderate" | "elevated";
  qualityScore: number;
}

const LEVEL_CONFIG = {
  low:      { color: "#22c55e", bg: "rgba(34,197,94,0.08)",  border: "rgba(34,197,94,0.25)",  emoji: "✅" },
  moderate: { color: "#f59e0b", bg: "rgba(245,158,11,0.08)", border: "rgba(245,158,11,0.25)", emoji: "⚠️" },
  elevated: { color: "#ef4444", bg: "rgba(239,68,68,0.08)",  border: "rgba(239,68,68,0.25)",  emoji: "🔔" },
};

export default function RiskCard({ riskScore, riskLevel, qualityScore }: Props) {
  const { t } = useApp();
  const cfg = LEVEL_CONFIG[riskLevel];

  const labelKey = riskLevel === "low"
    ? "risk_low" : riskLevel === "moderate"
    ? "risk_moderate" : "risk_elevated";

  return (
    <div className="card-glass p-6" style={{ borderColor: cfg.border }}>
      {/* Badge */}
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium mb-5"
        style={{ background: cfg.bg, color: cfg.color }}>
        <span>{cfg.emoji}</span>
        <span>{t(labelKey)}</span>
      </div>

      {/* Risk gauge */}
      <div className="mb-6">
        <div className="flex justify-between text-xs mb-2 text-ui-muted">
          <span>{t("risk_score_label")}</span>
          <span className="font-mono font-bold text-base" style={{ color: cfg.color }}>
            {riskScore.toFixed(0)}<span className="text-ui-subtle font-normal text-xs">/100</span>
          </span>
        </div>
        <div className="h-3 rounded-full overflow-hidden" style={{ background: "var(--border)" }}>
          <div className="h-full rounded-full transition-all duration-700"
            style={{ width: `${riskScore}%`, background: `linear-gradient(90deg, ${cfg.color}aa, ${cfg.color})` }}/>
        </div>
        <div className="flex justify-between text-xs mt-1 text-ui-subtle">
          <span>{t("risk_axis_low")}</span>
          <span>{t("risk_axis_mod")}</span>
          <span>{t("risk_axis_el")}</span>
        </div>
      </div>

      {/* Quality */}
      <div>
        <div className="flex justify-between text-xs mb-2 text-ui-muted">
          <span>{t("risk_quality_label")}</span>
          <span className="font-mono" style={{ color: "var(--text)" }}>{qualityScore.toFixed(0)}/100</span>
        </div>
        <div className="h-2 rounded-full overflow-hidden" style={{ background: "var(--border)" }}>
          <div className="h-full rounded-full"
            style={{ width: `${qualityScore}%`, background: "linear-gradient(90deg,#0d9488,#14b8a6)" }}/>
        </div>
        {qualityScore < 70 && (
          <p className="text-xs mt-2" style={{ color: "#f59e0b" }}>{t("risk_quality_warning")}</p>
        )}
      </div>
    </div>
  );
}
