import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { analyzeSession, ApiError, getSession } from "../api/client";
import { useApp } from "../context/AppContext";
import Navbar from "../components/Navbar";

const FINAL_STATUSES = new Set(["analyzed", "quality_failed"]);

const delay = (milliseconds: number) => new Promise((resolve) => window.setTimeout(resolve, milliseconds));

export default function LoadingAnalysisPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { t } = useApp();
  const completedAttempt = useRef(-1);
  const [attempt, setAttempt] = useState(0);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [recovering, setRecovering] = useState(false);

  const messages = [t("loading_m1"), t("loading_m2"), t("loading_m3"), t("loading_m4")];

  useEffect(() => {
    if (completedAttempt.current === attempt || !sessionId) return;
    completedAttempt.current = attempt;
    let cancelled = false;
    setAnalysisError(null);
    setRecovering(false);
    setElapsed(0);
    localStorage.setItem("ei_pending_session", sessionId);

    const finish = () => {
      if (cancelled) return;
      localStorage.removeItem("ei_pending_session");
      navigate(`/result/${sessionId}`, { replace: true });
    };

    const pollForResult = async (timeoutMs: number) => {
      setRecovering(true);
      const deadline = Date.now() + timeoutMs;
      while (!cancelled && Date.now() < deadline) {
        try {
          const session = await getSession(sessionId);
          if (FINAL_STATUSES.has(session.status)) {
            finish();
            return true;
          }
          if (session.status === "analysis_failed") throw new Error("analysis_failed");
        } catch (error) {
          if (error instanceof Error && error.message === "analysis_failed") throw error;
        }
        await delay(2500);
      }
      throw new Error("analysis_timeout");
    };

    const run = async () => {
      try {
        const session = await getSession(sessionId);
        if (FINAL_STATUSES.has(session.status)) {
          finish();
          return;
        }
        if (session.status === "processing" && attempt === 0) {
          await pollForResult(120_000);
          return;
        }
        if (!["uploaded", "analysis_failed", "processing"].includes(session.status)) {
          throw new Error(`session_not_ready:${session.status}`);
        }
        await analyzeSession(sessionId, attempt > 0);
        finish();
      } catch (error) {
        const shouldRecover = error instanceof ApiError && (error.status === 408 || error.status === 409);
        if (shouldRecover) {
          try {
            await pollForResult(120_000);
            return;
          } catch (pollError) {
            if (!cancelled) setAnalysisError(pollError instanceof Error ? pollError.message : String(pollError));
            return;
          }
        }
        if (!cancelled) setAnalysisError(error instanceof Error ? error.message : String(error));
      }
    };
    void run();
    return () => { cancelled = true; };
  }, [sessionId, navigate, attempt]);

  useEffect(() => {
    if (analysisError) return;
    const timer = window.setInterval(() => setElapsed((value) => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, [analysisError, attempt]);

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar homeLink />
      <div className="flex-1 flex flex-col items-center justify-center px-6 text-center gap-8">
        {analysisError ? (
          <div className="card-glass p-7 max-w-md">
            <h2 className="text-xl font-semibold mb-3" style={{ color: "#ef4444" }}>{t("analysis_failed_title")}</h2>
            <p className="text-sm text-ui-muted mb-5">{analysisError === "analysis_timeout" ? t("analysis_timeout_body") : t("analysis_failed_body")}</p>
            <details className="mb-5 text-left text-xs text-ui-subtle"><summary className="cursor-pointer">{t("analysis_error_detail")}</summary><p className="mt-2 break-words font-mono">{analysisError}</p></details>
            <div className="flex flex-col gap-3">
              <button onClick={() => setAttempt((value) => value + 1)} className="btn-primary w-full">{t("analysis_retry_processing")}</button>
              <button onClick={() => navigate("/screening", { replace: true })} className="btn-secondary w-full">{t("analysis_retry")}</button>
            </div>
          </div>
        ) : <>
          <div className="relative">
            <div className="w-24 h-24 rounded-full flex items-center justify-center" style={{ border: "2px solid rgba(20,184,166,0.3)" }}>
              <svg viewBox="0 0 48 48" className="w-12 h-12" fill="none">
                <ellipse cx="24" cy="24" rx="20" ry="12" stroke="#14b8a6" strokeWidth="2"/>
                <circle cx="24" cy="24" r="6" fill="#14b8a6" opacity="0.9"><animate attributeName="r" values="6;7.5;6" dur="2s" repeatCount="indefinite"/></circle>
              </svg>
            </div>
            <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-teal-500 animate-spin"/>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-2" style={{ color: "var(--text)" }}>{t("loading_title")}</h2>
            <p className="text-sm text-ui-muted">{recovering ? t("loading_recovering") : t("loading_sub")}</p>
            <p className="mt-2 text-xs font-mono text-ui-subtle">{t("loading_elapsed")}: {elapsed}s</p>
          </div>

          <div className="space-y-2">
            {messages.map((message) => <div key={message} className="flex items-center gap-3 text-sm text-ui-muted"><span className="w-1.5 h-1.5 rounded-full bg-teal-500/60"/>{message}</div>)}
          </div>

          <div className="disclaimer-banner max-w-sm text-xs">{t("loading_disclaimer")}</div>
        </>}
      </div>
    </div>
  );
}
