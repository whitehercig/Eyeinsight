import { useEffect, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { analyzeSession } from "../api/client";
import { useApp } from "../context/AppContext";
import Navbar from "../components/Navbar";

export default function LoadingAnalysisPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { t } = useApp();
  const called = useRef(false);

  const messages = [t("loading_m1"), t("loading_m2"), t("loading_m3"), t("loading_m4")];

  useEffect(() => {
    if (called.current || !sessionId) return;
    called.current = true;
    async function run() {
      try {
        await new Promise((r) => setTimeout(r, 1500));
        await analyzeSession(sessionId!);
        navigate(`/result/${sessionId}`, { replace: true });
      } catch {
        navigate(`/result/${sessionId}?error=1`, { replace: true });
      }
    }
    run();
  }, [sessionId, navigate]);

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar homeLink />
      <div className="flex-1 flex flex-col items-center justify-center px-6 text-center gap-8">
        {/* Animated eye */}
        <div className="relative">
          <div className="w-24 h-24 rounded-full flex items-center justify-center"
            style={{ border: "2px solid rgba(20,184,166,0.3)" }}>
            <svg viewBox="0 0 48 48" className="w-12 h-12" fill="none">
              <ellipse cx="24" cy="24" rx="20" ry="12" stroke="#14b8a6" strokeWidth="2"/>
              <circle cx="24" cy="24" r="6" fill="#14b8a6" opacity="0.9">
                <animate attributeName="r" values="6;7.5;6" dur="2s" repeatCount="indefinite"/>
              </circle>
            </svg>
          </div>
          <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-teal-500 animate-spin"/>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-2" style={{ color: "var(--text)" }}>
            {t("loading_title")}
          </h2>
          <p className="text-sm text-ui-muted">{t("loading_sub")}</p>
        </div>

        <div className="space-y-2">
          {messages.map((msg, i) => (
            <div key={i} className="flex items-center gap-3 text-sm text-ui-muted">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-500/40"/>
              {msg}
            </div>
          ))}
        </div>

        <div className="disclaimer-banner max-w-sm text-xs">{t("loading_disclaimer")}</div>
      </div>
    </div>
  );
}
