import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import CameraRecorder, { CameraRecorderHandle } from "../components/CameraRecorder";
import StimulusPlayer, { Phase } from "../components/StimulusPlayer";
import Navbar from "../components/Navbar";
import { createSession, uploadVideo } from "../api/client";

// ── Stimulus visuals (pure CSS animations, no external deps) ─────────────────

function MovingDotH() {
  return (
    <div className="w-full h-full relative flex items-center" style={{ background: "var(--bg-card)" }}>
      <div className="absolute w-10 h-10 rounded-full shadow-lg"
        style={{ background: "#2563eb", animation: "moveH 1.8s ease-in-out infinite alternate" }}/>
      <style>{`@keyframes moveH { from{left:8%} to{left:82%} }`}</style>
    </div>
  );
}
function MovingDotV() {
  return (
    <div className="w-full h-full relative flex justify-center" style={{ background: "var(--bg-card)" }}>
      <div className="absolute w-10 h-10 rounded-full shadow-lg"
        style={{ background: "#dc2626", animation: "moveV 1.8s ease-in-out infinite alternate" }}/>
      <style>{`@keyframes moveV { from{top:8%} to{top:75%} }`}</style>
    </div>
  );
}
function SmilingFace() {
  return (
    <div className="w-full h-full flex items-center justify-center"
      style={{ background: "var(--bg-card)" }}>
      <span className="text-8xl select-none" style={{ animation: "pulse 2s ease-in-out infinite" }}>😊</span>
    </div>
  );
}
function ColorfulObject() {
  return (
    <div className="w-full h-full relative" style={{ background: "var(--bg-card)" }}>
      <div className="absolute w-16 h-16 rounded-2xl shadow-lg"
        style={{ top: "calc(50% - 2rem)", background: "linear-gradient(135deg,#7c3aed,#db2777)", animation: "jumpSides 2s step-end infinite" }}/>
      <style>{`@keyframes jumpSides { 0%,50%{left:10%} 51%,100%{left:74%} }`}</style>
    </div>
  );
}
function CenterCross() {
  return (
    <div className="w-full h-full flex items-center justify-center"
      style={{ background: "var(--bg-card)" }}>
      <div className="relative w-16 h-16">
        <div className="absolute top-1/2 left-0 right-0 h-2 rounded -translate-y-1/2"
          style={{ background: "var(--text)" }}/>
        <div className="absolute left-1/2 top-0 bottom-0 w-2 rounded -translate-x-1/2"
          style={{ background: "var(--text)" }}/>
      </div>
    </div>
  );
}
function FinishScreen({ text }: { text: string }) {
  return (
    <div className="w-full h-full flex flex-col items-center justify-center gap-3"
      style={{ background: "var(--bg-card)" }}>
      <span className="text-6xl">🎉</span>
      <p className="font-semibold text-xl" style={{ color: "var(--text)" }}>{text}</p>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

type Stage = "waiting" | "recording" | "uploading" | "error";

export default function ScreeningPage() {
  const navigate = useNavigate();
  const { t } = useApp();
  const recorderRef = useRef<CameraRecorderHandle>(null);
  const sessionIdRef = useRef<string | null>(null);
  const tickerRef = useRef<number | null>(null);

  const [stage, setStage] = useState<Stage>("waiting");
  const [cameraReady, setCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [totalElapsed, setTotalElapsed] = useState(0);

  // Build phases using i18n labels.
  // IMPORTANT: keep this array stable while recording. If PHASES is recreated on
  // every render, StimulusPlayer restarts its timers and the eye-target sequence breaks.
  const PHASES: Phase[] = useMemo(() => [
    { duration: 5,  label: t("phase1_label"), render: () => <CenterCross /> },
    { duration: 10, label: t("phase2_label"), render: () => <MovingDotH /> },
    { duration: 10, label: t("phase3_label"), render: () => <MovingDotV /> },
    { duration: 10, label: t("phase4_label"), render: () => <SmilingFace /> },
    { duration: 10, label: t("phase5_label"), render: () => <ColorfulObject /> },
    { duration: 5,  label: t("phase6_label"), render: () => <FinishScreen text={t("phase_finish_text")} /> },
  ], [t]);

  const totalDuration = useMemo(
    () => PHASES.reduce((sum, phase) => sum + phase.duration, 0),
    [PHASES]
  );

  useEffect(() => {
    return () => {
      if (tickerRef.current !== null) {
        window.clearInterval(tickerRef.current);
      }
    };
  }, []);

  const handleCameraReady = useCallback(() => setCameraReady(true), []);
  const handleCameraError = useCallback((err: string) => setCameraError(err), []);

  async function handleStart() {
    try {
      const session = await createSession();
      sessionIdRef.current = session.id;
      setStage("recording");
      recorderRef.current?.startRecording();

      setTotalElapsed(0);
      const start = Date.now();
      if (tickerRef.current !== null) {
        window.clearInterval(tickerRef.current);
      }
      tickerRef.current = window.setInterval(() => {
        const sec = (Date.now() - start) / 1000;
        setTotalElapsed(sec);
        if (sec >= totalDuration && tickerRef.current !== null) {
          window.clearInterval(tickerRef.current);
          tickerRef.current = null;
        }
      }, 100);
    } catch (e) {
      setErrorMsg(`${t("error_start_session")}: ${e instanceof Error ? e.message : e}`);
      setStage("error");
    }
  }

  function handleStimulusComplete() {
    if (tickerRef.current !== null) {
      window.clearInterval(tickerRef.current);
      tickerRef.current = null;
    }
    recorderRef.current?.stopRecording();
  }

  async function handleRecordingComplete(blob: Blob) {
    if (tickerRef.current !== null) {
      window.clearInterval(tickerRef.current);
      tickerRef.current = null;
    }
    if (!sessionIdRef.current) return;
    setStage("uploading");
    try {
      await uploadVideo(sessionIdRef.current, blob);
      navigate(`/analyzing/${sessionIdRef.current}`);
    } catch (e) {
      setErrorMsg(`${t("error_upload")}: ${e instanceof Error ? e.message : e}`);
      setStage("error");
    }
  }

  const overallProgress = Math.min((totalElapsed / totalDuration) * 100, 100);

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar homeLink />

      <div className="flex-1 px-4 py-6 max-w-5xl mx-auto w-full">
        {/* Timer row */}
        {stage === "recording" && (
          <div className="flex justify-end mb-2 text-sm font-mono text-ui-muted">
            {Math.min(Math.round(totalElapsed), totalDuration)}s / {totalDuration}s
          </div>
        )}

        {/* Error */}
        {stage === "error" && (
          <div className="card-glass p-6 text-center" style={{ borderColor: "rgba(239,68,68,0.3)" }}>
            <p className="font-semibold mb-2" style={{ color: "#ef4444" }}>
              {errorMsg}
            </p>
            <button onClick={() => navigate("/")} className="btn-secondary text-sm mt-2">
              {t("error_back_home")}
            </button>
          </div>
        )}

        {/* Uploading */}
        {stage === "uploading" && (
          <div className="flex flex-col items-center justify-center gap-4 py-24">
            <div className="w-12 h-12 border-4 border-teal-500 border-t-transparent rounded-full animate-spin"/>
            <p className="font-medium" style={{ color: "var(--text)" }}>{t("screening_uploading")}</p>
            <p className="text-sm text-ui-muted">{t("screening_uploading_sub")}</p>
          </div>
        )}

        {/* Camera error */}
        {cameraError && (
          <div className="card-glass p-8 text-center max-w-lg mx-auto"
            style={{ borderColor: "rgba(239,68,68,0.3)" }}>
            <div className="text-4xl mb-4">🎥</div>
            <p className="font-semibold mb-2" style={{ color: "#ef4444" }}>
              {t("screening_camera_error_title")}
            </p>
            <p className="text-sm text-ui-muted mb-4">{cameraError}</p>
            <button onClick={() => window.location.reload()} className="btn-primary">
              {t("screening_camera_reload")}
            </button>
          </div>
        )}

        {/* Main grid */}
        {!cameraError && stage !== "uploading" && stage !== "error" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Camera */}
            <div>
              <p className="text-xs font-mono uppercase tracking-widest mb-3 text-ui-subtle">
                {t("screening_camera_label")}
              </p>
              <CameraRecorder
                ref={recorderRef}
                onCameraReady={handleCameraReady}
                onCameraError={handleCameraError}
                onRecordingComplete={handleRecordingComplete}
              />

              {!cameraReady && !cameraError && (
                <p className="text-sm mt-3 text-center animate-pulse text-ui-muted">
                  …
                </p>
              )}

              {stage === "waiting" && cameraReady && (
                <div className="mt-4 space-y-3">
                  <div className="card-glass p-4 text-sm leading-relaxed text-ui-muted">
                    <p className="font-medium mb-1" style={{ color: "var(--text)" }}>
                      {t("screening_waiting_title")}
                    </p>
                    <ul className="space-y-1 list-disc list-inside">
                      {[t("screening_tip1"), t("screening_tip2"), t("screening_tip3"), t("screening_tip4")]
                        .map((tip, i) => <li key={i}>{tip}</li>)}
                    </ul>
                  </div>
                  <button className="btn-primary w-full" onClick={handleStart}>
                    {t("screening_start")}
                  </button>
                </div>
              )}

              {stage === "recording" && (
                <div className="mt-3">
                  <div className="h-1 rounded-full overflow-hidden" style={{ background: "var(--border)" }}>
                    <div className="h-full bg-teal-500 transition-all duration-100"
                      style={{ width: `${overallProgress}%` }}/>
                  </div>
                  <p className="text-xs text-center mt-1 text-ui-subtle">{t("screening_overall")}</p>
                </div>
              )}
            </div>

            {/* Stimulus */}
            <div>
              {stage === "waiting" && (
                <div className="card-glass p-8 h-full flex items-center justify-center text-center">
                  <div>
                    <div className="text-5xl mb-4">👁</div>
                    <p className="text-sm text-ui-muted">{t("screening_stimulus_ready")}</p>
                  </div>
                </div>
              )}
              {stage === "recording" && (
                <StimulusPlayer phases={PHASES} onComplete={handleStimulusComplete} />
              )}
            </div>
          </div>
        )}

        <div className="disclaimer-banner mt-8 text-xs">{t("screening_disclaimer")}</div>
      </div>
    </div>
  );
}
