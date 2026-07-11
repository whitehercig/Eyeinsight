import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import Navbar from "../components/Navbar";

export default function ConsentPage() {
  const navigate = useNavigate();
  const { t } = useApp();
  const [checked, setChecked] = useState<Record<string, boolean>>({});

  const consents = [
    { id: "not-diagnosis", label: t("consent_1") },
    { id: "video-upload",  label: t("consent_2") },
    { id: "specialist",    label: t("consent_3") },
  ];

  const allChecked = consents.every((c) => checked[c.id]);
  const toggle = (id: string) => setChecked((p) => ({ ...p, [id]: !p[id] }));

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar homeLink />

      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        <div className="card-glass max-w-xl w-full p-8 animate-slide-up">
          <button onClick={() => navigate("/")}
            className="mb-6 text-sm text-ui-muted hover:text-teal-500 transition-colors flex items-center gap-1">
            {t("consent_back")}
          </button>

          <h2 className="text-2xl font-bold mb-2" style={{ color: "var(--text)" }}>
            {t("consent_title")}
          </h2>
          <p className="text-sm leading-relaxed mb-6 text-ui-muted">
            {t("consent_subtitle")}
          </p>

          <div className="disclaimer-banner mb-6">
            <p className="font-semibold mb-1">{t("consent_alert_title")}</p>
            <p>{t("consent_alert_body")}</p>
          </div>

          <div className="space-y-4 mb-8">
            {consents.map((c) => (
              <label key={c.id}
                className={`flex gap-4 p-4 rounded-xl border cursor-pointer transition-all ${
                  checked[c.id]
                    ? "border-teal-500/50 bg-teal-500/5"
                    : "border-ui hover:border-teal-500/30"
                }`}>
                <div
                  onClick={() => toggle(c.id)}
                  className={`mt-0.5 w-5 h-5 shrink-0 rounded border-2 flex items-center justify-center transition-all ${
                    checked[c.id] ? "border-teal-500 bg-teal-500" : "border-slate-500"
                  }`}>
                  {checked[c.id] && (
                    <svg viewBox="0 0 12 10" className="w-3 h-3" fill="none">
                      <path d="M1 5l3.5 3.5L11 1" stroke="white" strokeWidth="2" strokeLinecap="round"/>
                    </svg>
                  )}
                </div>
                <input type="checkbox" className="sr-only"
                  checked={!!checked[c.id]} onChange={() => toggle(c.id)} />
                <span className="text-sm leading-relaxed text-ui-muted">{c.label}</span>
              </label>
            ))}
          </div>

          <button className="btn-primary w-full" disabled={!allChecked}
            onClick={() => navigate("/screening")}>
            {allChecked ? t("consent_cta_ready") : t("consent_cta_wait")}
          </button>

          <p className="text-xs text-center mt-4 text-ui-subtle">{t("consent_privacy")}</p>
        </div>
      </div>
    </div>
  );
}
