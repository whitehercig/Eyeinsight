/**
 * ResultPage
 *
 * ARCHITECTURE:
 * - Receives AnalysisResult with CODES from backend (no English text)
 * - Uses resolvers to map codes → translated strings in current language
 * - Language switching updates all content instantly (reactive via useApp)
 * - Zero hardcoded English strings in rendered output
 *
 * MEDICAL SAFETY:
 * - Never uses the word "diagnosis" applied to the child
 * - Prominent disclaimer on every render
 * - Does not suggest any specific condition
 */

import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { deleteSession, getFeatures, getResult, type AnalysisResult, type FeatureBundle } from "../api/client";
import { useApp } from "../context/AppContext";
import {
  resolveSummary,
  resolveRecommendations,
  resolveQualityIssues,
} from "../i18n/resolvers";
import RiskCard from "../components/RiskCard";
import Navbar from "../components/Navbar";
import FeatureCharts from "../components/FeatureCharts";
import GazeVisualizations from "../components/GazeVisualizations";

export default function ResultPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { t, lang } = useApp(); // lang used for live code resolution

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
        return getFeatures(sessionId)
          .then(setFeatures)
          .catch(() => setFeaturesUnavailable(true));
      })
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, [sessionId]);

  // ── Derived translations — resolved fresh on every lang change ────────────
  // These are computed values, not stored state, so language switch is instant.

  const summaryText = result
    ? resolveSummary(result.summary_code, lang)
    : "";

  const recommendationTexts = result
    ? resolveRecommendations(result.recommendation_codes, lang)
    : [];

  const qualityIssueTexts = result
    ? resolveQualityIssues(result.quality_issues, lang)
    : [];

  async function handleDeleteSession() {
    if (!sessionId || !window.confirm(t("result_delete_confirm"))) return;
    setDeleting(true);
    try {
      await deleteSession(sessionId);
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

          {/* Summary (translated via code) */}
          <div className="card-glass p-6 mb-4">
            <p className="text-sm leading-relaxed text-ui-muted">{summaryText}</p>
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
              <span>{t("risk_quality_label")}</span>
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

        {/* ⚠️ Top disclaimer — always first, before any score */}
        <div className="disclaimer-banner mb-6 text-center">
          <p className="font-bold text-base mb-1">{t("result_disclaimer_title")}</p>
          <p>{t("result_disclaimer_body")}</p>
        </div>

        {/* Risk card — uses t() internally, fully translated */}
        <RiskCard
          riskScore={result.risk_score!}
          riskLevel={result.risk_level!}
          qualityScore={result.quality_score}
        />

        <div className="card-glass p-6 mt-4">
          <div className="flex justify-between items-end gap-4">
            <div><h3 className="font-semibold text-sm uppercase tracking-widest mb-2 text-ui-muted">{t("result_attention")}</h3><p className="text-xs text-ui-subtle">{result.score_explanation}</p></div>
            <span className="text-3xl font-mono font-bold text-teal-400">{result.attention_score?.toFixed(0) ?? "—"}<span className="text-sm text-ui-subtle">/100</span></span>
          </div>
          {result.score_breakdown && <div className="grid grid-cols-2 gap-x-4 gap-y-2 mt-4">{Object.entries(result.score_breakdown).map(([name, score]) => <div key={name} className="flex justify-between text-xs text-ui-muted"><span className="truncate">{name.replace(/_/g, " ")}</span><span>{score.toFixed(0)}%</span></div>)}</div>}
        </div>

        {/* Summary — resolved from summary_code in current language */}
        <div className="card-glass p-6 mt-4">
          <h3 className="font-semibold text-sm uppercase tracking-widest mb-2 text-ui-muted">
            {t("result_summary_label")}
          </h3>
          <p className="text-sm leading-relaxed text-ui-muted">{summaryText}</p>
        </div>

        {result.top_contributing_factors && result.top_contributing_factors.length > 0 && <div className="card-glass p-6 mt-4"><h3 className="font-semibold text-sm uppercase tracking-widest mb-3 text-ui-muted">{t("result_factors")}</h3><div className="space-y-2">{result.top_contributing_factors.map((factor) => <div key={factor.factor} className="flex justify-between text-sm text-ui-muted"><span>{factor.factor.replace(/_/g, " ")}</span><span className="font-mono">{factor.contribution.toFixed(1)}</span></div>)}</div>{result.risk_confidence !== null && result.risk_confidence !== undefined && <p className="text-xs text-ui-subtle mt-4">{result.risk_confidence_type?.replace(/_/g, " ")}: {result.risk_confidence.toFixed(0)}%</p>}</div>}

        {features && <><h3 className="font-semibold text-sm uppercase tracking-widest mt-6 text-ui-muted">{t("result_analysis")}</h3><FeatureCharts frames={features.frame_preview} phases={features.phase_features} labels={{ attention: t("chart_attention"), movement: t("chart_movement"), blink: t("chart_blink"), visibility: t("chart_visibility"), tracking: t("chart_tracking"), away: t("chart_away"), phases: t("chart_phases"), phaseNames: { center_focus: t("phase1_label"), horizontal_tracking: t("phase2_label"), vertical_tracking: t("phase3_label"), social_face: t("phase4_label"), attention_shift: t("phase5_label"), final_center: t("phase6_label") } }} /><GazeVisualizations visualizations={features.visualizations} labels={{ heatmap: t("gaze_heatmap_title"), path: t("gaze_path_title"), proxy: t("gaze_proxy_note"), gaze: t("gaze_path_gaze"), target: t("gaze_path_target") }} /></>}
        {featuresUnavailable && <p className="mt-4 text-xs text-ui-subtle">{t("result_features_unavailable")}</p>}

        {/* Recommendations — each code resolved to current language */}
        <div className="card-glass p-6 mt-4">
          <h3 className="font-semibold text-sm uppercase tracking-widest mb-3 text-ui-muted">
            {t("result_recs_label")}
          </h3>
          <ul className="space-y-3">
            {recommendationTexts.map((rec, i) => (
              <li key={i} className="flex gap-3 text-sm text-ui-muted">
                <span
                  className="mt-0.5 w-5 h-5 shrink-0 rounded-full flex items-center justify-center text-xs font-bold text-teal-400"
                  style={{ background: "rgba(20,184,166,0.12)" }}
                >
                  {i + 1}
                </span>
                {rec}
              </li>
            ))}
          </ul>
        </div>

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

        {/* Bottom disclaimer */}
        <div className="mt-6 card-glass p-5 text-center">
          <p className="text-xs leading-relaxed text-ui-subtle">
            {t("result_footer_disclaimer")}
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 mt-6">
          <button onClick={() => navigate("/")} className="btn-primary flex-1 text-center">
            {t("result_new")}
          </button>
          {features && <div className="card-glass p-4 flex-1"><p className="text-xs text-ui-muted mb-3">{t("result_downloads")}</p><div className="flex flex-wrap gap-2">{Object.entries(features.downloads).map(([name, href]) => <a key={name} href={href} className="btn-secondary text-xs">{name}</a>)}</div></div>}
        </div>

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
