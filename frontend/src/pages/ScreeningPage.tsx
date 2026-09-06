import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import CameraRecorder, { CameraRecorderHandle } from "../components/CameraRecorder";
import StimulusPlayer, { Phase } from "../components/StimulusPlayer";
import Navbar from "../components/Navbar";
import { checkCamera, createSession, uploadVideo, type CameraReadiness } from "../api/client";

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
  const [isStarting, setIsStarting] = useState(false);
  const [readiness, setReadiness] = useState<CameraReadiness | null>(null);
  const [isCheckingCamera, setIsCheckingCamera] = useState(false);
  const [readinessError, setReadinessError] = useState<string | null>(null);

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

  const runCameraCheck = useCallback(async () => {
    if (!recorderRef.current || isCheckingCamera) return;
    setIsCheckingCamera(true);
    setReadinessError(null);
    try {
      const frames: Blob[] = [];
      for (let index = 0; index < 4; index += 1) {
        frames.push(await recorderRef.current.captureFrame());
        if (index < 3) await new Promise((resolve) => window.setTimeout(resolve, 220));
      }
      setReadiness(await checkCamera(frames));
    } catch (error) {
      setReadiness(null);
      setReadinessError(error instanceof Error ? error.message : String(error));
    } finally {
      setIsCheckingCamera(false);
    }
  }, [isCheckingCamera]);

  useEffect(() => {
    if (!cameraReady || stage !== "waiting" || readiness || readinessError || isCheckingCamera) return;
    const timer = window.setTimeout(runCameraCheck, 700);
    return () => window.clearTimeout(timer);
  }, [cameraReady, stage, readiness, readinessError, isCheckingCamera, runCameraCheck]);

  async function handleStart() {
    if (isStarting || !cameraReady || !readiness?.ready || !recorderRef.current) return;
    setIsStarting(true);
    try {
      const session = await createSession();
      sessionIdRef.current = session.id;
      recorderRef.current.startRecording();
      setStage("recording");

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
    } finally {
      setIsStarting(false);
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
      localStorage.setItem("ei_pending_session", sessionIdRef.current);
      navigate(`/analyzing/${sessionIdRef.current}`);
    } catch (e) {
      setErrorMsg(`${t("error_upload")}: ${e instanceof Error ? e.message : e}`);
      setStage("error");
    }
  }

  const overallProgress = Math.min((totalElapsed / totalDuration) * 100, 100);
  const readinessItems = [
    ["lighting", t("camera_check_lighting")],
    ["face_in_frame", t("camera_check_face")],
    ["distance", t("camera_check_distance")],
    ["stability", t("camera_check_stability")],
  ] as const;

  return (
    <div className="min-h-screen flex flex-col">
      {stage !== "recording" && <Navbar homeLink />}

      <div className="flex-1 px-4 py-6 max-w-5xl mx-auto w-full">
        {stage === "error" && (
          <div className="card-glass p-8 text-center max-w-lg mx-auto mt-16" style={{ borderColor: "rgba(239,68,68,0.3)" }}>
            <p className="font-semibold mb-2" style={{ color: "#ef4444" }}>
              {errorMsg}
            </p>
            <button onClick={() => window.location.reload()} className="btn-primary text-sm mt-4">
              {t("screening_try_again")}
            </button>
          </div>
        )}

        {stage === "uploading" && (
          <div className="flex flex-col items-center justify-center gap-4 py-24">
            <div className="w-12 h-12 border-4 border-teal-500 border-t-transparent rounded-full animate-spin"/>
            <p className="font-medium" style={{ color: "var(--text)" }}>{t("screening_uploading")}</p>
            <p className="text-sm text-ui-muted">{t("screening_uploading_sub")}</p>
          </div>
        )}

        {cameraError && stage !== "error" && (
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

        {!cameraError && (stage === "waiting" || stage === "recording") && (
          <>
            <div className={stage === "recording" ? "fixed -left-[10000px] top-0 w-[640px]" : "grid grid-cols-1 lg:grid-cols-[1.15fr_0.85fr] gap-6 items-start"}>
              <div>
                {stage === "waiting" && <p className="text-xs font-mono uppercase tracking-widest mb-3 text-ui-subtle">{t("screening_camera_label")}</p>}
              <CameraRecorder
                ref={recorderRef}
                onCameraReady={handleCameraReady}
                onCameraError={handleCameraError}
                onRecordingComplete={handleRecordingComplete}
              />

                {!cameraReady && !cameraError && (
                <p className="text-sm mt-3 text-center animate-pulse text-ui-muted">
                    {t("screening_camera_loading")}
                </p>
              )}
              </div>

              {stage === "waiting" && cameraReady && (
                <div className="card-glass p-6 lg:mt-7">
                  <div className="mb-6">
                    <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-teal-500/10 text-2xl">✓</div>
                    <p className="font-semibold text-lg mb-2" style={{ color: "var(--text)" }}>
                      {t("screening_waiting_title")}
                    </p>
                    <p className="text-sm leading-relaxed text-ui-muted">{t("screening_waiting_body")}</p>
                  </div>
                  <ul className="space-y-3 mb-6">
                      {[t("screening_tip1"), t("screening_tip2"), t("screening_tip3"), t("screening_tip4")]
                        .map((tip, index) => <li key={tip} className="flex gap-3 text-sm text-ui-muted"><span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-teal-500/10 text-xs font-semibold text-teal-600">{index + 1}</span><span>{tip}</span></li>)}
                  </ul>
                  <div className="mb-5 rounded-xl border border-ui p-4">
                    <div className="mb-3 flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold" style={{ color: "var(--text)" }}>{t("camera_check_title")}</p>
                      {isCheckingCamera && <span className="text-xs text-teal-600 animate-pulse">{t("camera_check_running")}</span>}
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      {readinessItems.map(([key, label]) => {
                        const passed = readiness?.checks[key];
                        return <div key={key} className="flex items-center gap-2 rounded-lg px-2.5 py-2 text-xs" style={{ background: "var(--chart-surface)" }}><span className={`flex h-5 w-5 items-center justify-center rounded-full font-bold ${passed ? "bg-teal-500/15 text-teal-600" : readiness ? "bg-amber-500/15 text-amber-600" : "bg-slate-500/10 text-ui-subtle"}`}>{passed ? "✓" : readiness ? "!" : "·"}</span><span className="text-ui-muted">{label}</span></div>;
                      })}
                    </div>
                    {readiness && <p className={`mt-3 text-xs font-medium ${readiness.ready ? "text-teal-600" : "text-amber-600"}`}>{readiness.ready ? t("camera_check_ready") : t("camera_check_adjust")}</p>}
                    {readinessError && <p className="mt-3 break-words text-xs text-rose-500">{t("camera_check_error")}: {readinessError}</p>}
                    <button type="button" onClick={runCameraCheck} disabled={isCheckingCamera} className="btn-secondary mt-3 w-full py-2 text-xs">{readiness ? t("camera_check_again") : t("camera_check_start")}</button>
                  </div>
                  <button className="btn-primary w-full" onClick={handleStart} disabled={isStarting || !readiness?.ready}>
                    {isStarting ? t("screening_starting") : t("screening_start")}
                  </button>
                  <p className="mt-3 text-center text-xs text-ui-subtle">{readiness?.ready ? t("screening_stimulus_ready") : t("camera_check_required")}</p>
                </div>
              )}
            </div>

            {stage === "recording" && (
              <div className="fixed inset-0 z-50 overflow-y-auto" style={{ background: "var(--bg)" }}>
                <div className="min-h-screen flex flex-col px-4 py-4 sm:px-8 sm:py-6">
                  <div className="mx-auto w-full max-w-5xl">
                    <div className="mb-5 flex items-center gap-4">
                      <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: "var(--border)" }}>
                        <div className="h-full bg-teal-500 transition-all duration-100" style={{ width: `${overallProgress}%` }}/>
                      </div>
                      <span className="shrink-0 text-sm font-mono text-ui-muted">{Math.min(Math.round(totalElapsed), totalDuration)} / {totalDuration}s</span>
                    </div>
                    <p className="mb-3 text-center text-xs text-ui-subtle">{t("screening_recording_note")}</p>
                    <StimulusPlayer phases={PHASES} onComplete={handleStimulusComplete} />
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {stage === "waiting" && !cameraError && <div className="disclaimer-banner mt-8 text-xs">{t("screening_disclaimer")}</div>}
      </div>
    </div>
  );
}
