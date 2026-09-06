/**
 * ResultPage
 *
 * ARCHITECTURE:
 * - Presents descriptive technical metrics from the computer-vision pipeline
 * - Language switching updates all content instantly
 *
 * MEDICAL SAFETY:
 * - Never presents a clinical risk score
 * - Clearly labels camera-derived values as unvalidated technical proxies
 */

import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { deleteSession, getFeatures, getResult, type AnalysisResult, type FeatureBundle } from "../api/client";
import { useApp } from "../context/AppContext";
import { resolveQualityIssues } from "../i18n/resolvers";
import Navbar from "../components/Navbar";
import FeatureCharts from "../components/FeatureCharts";
import GazeVisualizations from "../components/GazeVisualizations";

export default function ResultPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { t, lang } = useApp();

  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [features, setFeatures] = useState<FeatureBundle | null>(null);
  const [featuresUnavailable, setFeaturesUnavailable] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const hasError = searchParams.get("error") === "1";

  useEffect(() => {
    if (!sessionId) return;
    getResult(sessionId)
      .then((analysis) => {
        setResult(analysis);
        if (localStorage.getItem("ei_pending_session") === sessionId) localStorage.removeItem("ei_pending_session");
        return getFeatures(sessionId)
          .then(setFeatures)
          .catch(() => setFeaturesUnavailable(true));
      })
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, [sessionId]);

  const qualityIssueTexts = result
    ? resolveQualityIssues(result.quality_issues, lang)
    : [];

  const sessionFeatures = features?.session_features;
  const percentMetric = (key: string) => {
    const value = Number(sessionFeatures?.[key]);
    return Number.isFinite(value) ? `${(value * 100).toFixed(0)}%` : "—";
  };
  const latencyValue = Number(sessionFeatures?.estimated_response_latency_ms);
  const reportHref = sessionId
    ? `/api/sessions/${sessionId}/clinical-report?lang=${lang}`
    : "#";

  async function handleDeleteSession() {
    if (!sessionId || !window.confirm(t("result_delete_confirm"))) return;
    setDeleting(true);
    try {
      await deleteSession(sessionId);
      if (localStorage.getItem("ei_pending_session") === sessionId) localStorage.removeItem("ei_pending_session");
      navigate("/", { replace: true });
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : String(deleteError));
    } finally {
      setDeleting(false);
    }
  }

  // ── Loading state ─────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navbar homeLink />
        <div className="flex-1 flex items-center justify-center">
          <div className="w-10 h-10 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  // ── Error state ───────────────────────────────────────────────────────────

  if (error || hasError || !result) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navbar homeLink />
        <div className="flex-1 flex flex-col items-center justify-center px-6 text-center gap-4">
          <p className="font-semibold text-lg" style={{ color: "#ef4444" }}>
            {t("result_error_title")}
          </p>
          <p className="text-sm text-ui-muted">{error ?? t("result_error_sub")}</p>
          <button onClick={() => navigate("/")} className="btn-primary">
            {t("result_new")}
          </button>
        </div>
      </div>
    );
  }

  // ── Quality failure state ─────────────────────────────────────────────────

  if (result.quality_failed) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navbar homeLink />
        <div className="flex-1 px-4 py-10 max-w-xl mx-auto w-full animate-slide-up">
          <div className="text-center mb-8">
            <div className="text-5xl mb-4">📷</div>
            <h1 className="text-2xl font-bold" style={{ color: "var(--text)" }}>
              {t("quality_failed_title")}
            </h1>
          </div>

          <div className="card-glass p-6 mb-4">
            <p className="text-sm leading-relaxed text-ui-muted">{t("quality_failed_body")}</p>
          </div>

          {/* Quality issues (translated via codes) */}
          {qualityIssueTexts.length > 0 && (
            <div className="card-glass p-6 mb-4">
              <h3 className="font-semibold text-sm uppercase tracking-widest mb-3 text-ui-muted">
                {t("quality_failed_issues_label")}
              </h3>
              <ul className="space-y-2">
                {qualityIssueTexts.map((issue, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-ui-muted">
                    <span className="text-amber-400">⚠</span>
                    {issue}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Video quality bar */}
          <div className="card-glass p-6 mb-6">
            <div className="flex justify-between text-xs mb-2 text-ui-muted">
              <span>{t("result_data_quality")}</span>
              <span className="font-mono" style={{ color: "var(--text)" }}>
                {result.quality_score.toFixed(0)}/100
              </span>
            </div>
            <div className="h-2 rounded-full overflow-hidden" style={{ background: "var(--border)" }}>
              <div
                className="h-full rounded-full"
                style={{
                  width: `${result.quality_score}%`,
                  background: "linear-gradient(90deg,#ef4444,#f97316)",
                }}
              />
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <button onClick={() => navigate("/screening")} className="btn-primary flex-1">
              {t("result_record_again")}
            </button>
            <button onClick={() => navigate("/")} className="btn-secondary flex-1 text-sm">
              {t("error_back_home")}
            </button>
          </div>
          {features && <div className="mt-5 flex flex-wrap gap-2">{Object.entries(features.downloads).map(([name, href]) => <a key={name} href={href} className="btn-secondary text-xs">{name}</a>)}</div>}
        </div>
      </div>
    );
  }

  // ── Normal result state ───────────────────────────────────────────────────

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar homeLink />

      <div className="flex-1 px-4 py-10 max-w-2xl mx-auto w-full animate-slide-up">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold mt-2 mb-1" style={{ color: "var(--text)" }}>
            {t("result_title")}
          </h1>
          <p className="text-sm font-mono text-ui-subtle">
            #{sessionId?.slice(0, 8)}
          </p>
        </div>

        {/* Safety notice — always shown before metrics. */}
        {result.is_demo && (
          <div className="mb-4 rounded-xl border border-sky-500/30 bg-sky-500/5 p-4 text-center text-sky-700 dark:text-sky-300">
            <p className="font-bold">{t("result_demo_title")}</p>
            <p className="mt-1 text-sm">{t("result_demo_body")}</p>
          </div>
        )}
        <div className="disclaimer-banner mb-6 text-center">
          <p className="font-bold text-base mb-1">{t("result_disclaimer_title")}</p>
          <p>{t("result_disclaimer_body")}</p>
        </div>

        <div className="card-glass p-6 border-teal-500/30">
          <div className="flex items-start gap-4">
            <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-teal-500/10 text-xl text-teal-500">✓</div>
            <div>
              <h2 className="font-semibold" style={{ color: "var(--text)" }}>{t("result_status_title")}</h2>
              <p className="mt-1 text-sm leading-relaxed text-ui-muted">{result.is_demo ? t("result_demo_status") : t("result_status_body")}</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mt-4 sm:grid-cols-4">
          {[
            [t("result_data_quality"), `${result.quality_score.toFixed(0)}/100`],
            [t("result_usable_frames"), percentMetric("overall_usable_frames")],
            [t("result_face_visibility"), percentMetric("overall_face_visibility")],
            [t("result_tracking_quality"), percentMetric("overall_tracking_quality")],
          ].map(([label, value]) => (
            <div key={label} className="card-glass p-4">
              <p className="text-xs leading-snug text-ui-subtle">{label}</p>
              <p className="mt-2 text-xl font-bold font-mono text-teal-500">{value}</p>
            </div>
          ))}
        </div>

        <div className="card-glass p-6 mt-4">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h3 className="font-semibold text-sm uppercase tracking-widest text-ui-muted">{t("result_attention_proxy")}</h3>
              <p className="mt-2 max-w-lg text-xs leading-relaxed text-ui-subtle">{t("result_attention_proxy_note")}</p>
            </div>
            <div className="shrink-0 sm:text-right">
              <span className="text-3xl font-mono font-bold text-teal-500">{result.attention_score?.toFixed(0) ?? "—"}</span>
              <span className="text-sm text-ui-subtle">/100</span>
            </div>
          </div>
          <div className="mt-5 border-t border-ui pt-4 flex items-center justify-between gap-4 text-sm">
            <span className="text-ui-muted">{t("result_response_latency")}</span>
            <span className="font-mono font-semibold" style={{ color: "var(--text)" }}>{Number.isFinite(latencyValue) ? `${latencyValue.toFixed(0)} ms` : t("result_not_available")}</span>
          </div>
        </div>

        {features && <><h3 className="font-semibold text-sm uppercase tracking-widest mt-6 text-ui-muted">{t("result_analysis")}</h3><FeatureCharts frames={features.frame_preview} phases={features.phase_features} labels={{ usable: t("chart_attention"), movement: t("chart_movement"), blink: t("chart_blink"), visibility: t("chart_visibility"), tracking: t("chart_tracking"), away: t("chart_away"), phases: t("chart_phases"), phaseNames: { center_focus: t("phase1_short"), horizontal_tracking: t("phase2_short"), vertical_tracking: t("phase3_short"), social_face: t("phase4_short"), attention_shift: t("phase5_short"), final_center: t("phase6_short") } }} /><GazeVisualizations visualizations={features.visualizations} labels={{ heatmap: t("gaze_heatmap_title"), path: t("gaze_path_title"), proxy: t("gaze_proxy_note"), gaze: t("gaze_path_gaze"), target: t("gaze_path_target"), empty: t("gaze_empty") }} /></>}
        {featuresUnavailable && <p className="mt-4 text-xs text-ui-subtle">{t("result_features_unavailable")}</p>}

        {/* Quality issues (if any, even in non-failed results) */}
        {qualityIssueTexts.length > 0 && (
          <div className="card-glass p-6 mt-4">
            <h3 className="font-semibold text-sm uppercase tracking-widest mb-3 text-ui-muted">
              {t("quality_failed_issues_label")}
            </h3>
            <ul className="space-y-2">
              {qualityIssueTexts.map((issue, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-ui-muted">
                  <span className="text-amber-400">⚠</span>
                  {issue}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-6 card-glass p-5 text-center">
          <p className="text-xs leading-relaxed text-ui-subtle">
            {t("result_footer_disclaimer")}
          </p>
          <p className={`mt-2 text-xs font-medium ${result.source_video_deleted ? "text-teal-600" : "text-amber-600"}`}>{result.is_demo ? t("result_demo_no_video") : result.source_video_deleted ? t("result_video_deleted") : t("result_video_retained")}</p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 mt-6">
          <a href={reportHref} className="btn-primary flex-1 text-center">{t("result_download_pdf")}</a>
          <button onClick={() => navigate("/")} className="btn-secondary flex-1 text-center">{t("result_new")}</button>
        </div>

        {features && (
          <details className="card-glass p-4 mt-4">
            <summary className="cursor-pointer text-sm font-medium text-ui-muted">{t("result_technical_downloads")}</summary>
            <div className="flex flex-wrap gap-2 mt-4">{Object.entries(features.downloads).map(([name, href]) => <a key={name} href={href} className="btn-secondary text-xs">{name}</a>)}</div>
          </details>
        )}

        <p className="text-xs text-center mt-6 text-ui-subtle">
          {t("result_generated")}
        </p>
        <button onClick={handleDeleteSession} disabled={deleting} className="block mx-auto mt-4 text-xs text-ui-subtle underline disabled:opacity-50">
          {deleting ? t("result_deleting") : t("result_delete_data")}
        </button>
      </div>
    </div>
  );
}
