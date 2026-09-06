import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import Navbar from "../components/Navbar";
import EyeInsightLogo from "../components/EyeInsightLogo";
import { createDemoSession } from "../api/client";

type FeatureIconName = "camera" | "clock" | "quality" | "report";

function FeatureIcon({ name }: { name: FeatureIconName }) {
  const paths = {
    camera: <><path d="M7 8.5 8.5 6h7L17 8.5h2.5a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-15a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2H7Z"/><circle cx="12" cy="14" r="3.5"/></>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
    quality: <><path d="M12 3 4.5 6v5.5c0 4.4 3 7.8 7.5 9.5 4.5-1.7 7.5-5.1 7.5-9.5V6L12 3Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/></>,
    report: <><path d="M6 3.5h8l4 4v13H6v-17Z"/><path d="M14 3.5v4h4M9 12h6M9 16h6"/></>,
  };
  return <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-500/10 text-teal-600"><svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg></div>;
}

export default function HomePage() {
  const navigate = useNavigate();
  const { t } = useApp();
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoError, setDemoError] = useState<string | null>(null);
  const pendingSession = localStorage.getItem("ei_pending_session");

  async function openSafeDemo() {
    if (demoLoading) return;
    setDemoLoading(true);
    setDemoError(null);
    try {
      const session = await createDemoSession();
      navigate(`/result/${session.id}`);
    } catch (error) {
      setDemoError(error instanceof Error ? error.message : String(error));
      setDemoLoading(false);
    }
  }

  const features = [
    { icon: "camera" as const, title: t("home_f1_title"), desc: t("home_f1_desc") },
    { icon: "clock" as const, title: t("home_f2_title"), desc: t("home_f2_desc") },
    { icon: "quality" as const, title: t("home_f3_title"), desc: t("home_f3_desc") },
    { icon: "report" as const, title: t("home_f4_title"), desc: t("home_f4_desc") },
  ];

  const steps = [
    ["01", t("home_step1_title"), t("home_step1_desc")],
    ["02", t("home_step2_title"), t("home_step2_desc")],
    ["03", t("home_step3_title"), t("home_step3_desc")],
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 pt-16 pb-12 text-center max-w-4xl mx-auto w-full animate-slide-up">
        {/* Logo */}
        <div className="mb-10 relative">
          <div className="w-28 h-28 rounded-full flex items-center justify-center mx-auto"
            style={{ background: "rgba(20,184,166,0.07)", border: "1px solid rgba(20,184,166,0.2)" }}>
            <EyeInsightLogo size={72} showText={false} />
          </div>
          <div className="absolute inset-0 w-28 h-28 mx-auto rounded-full blur-2xl"
            style={{ background: "rgba(20,184,166,0.12)" }} />
        </div>

        <p className="mb-4 rounded-full border border-teal-500/20 bg-teal-500/5 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-teal-600">{t("home_eyebrow")}</p>

        <h1 className="text-4xl sm:text-6xl font-bold leading-[1.08] mb-5 tracking-tight"
          style={{ color: "var(--text)" }}>
          {t("home_title")}
        </h1>

        <p className="text-lg sm:text-xl max-w-2xl mb-7 leading-relaxed text-ui-muted">
          {t("home_subtitle")}
        </p>

        <div className="disclaimer-banner mb-10 max-w-lg text-left">
          <strong>{t("home_disclaimer_title")}</strong>{" "}
          {t("home_disclaimer_body")}
        </div>

        {pendingSession && (
          <div className="card-glass mb-6 flex w-full max-w-lg flex-col items-start gap-3 p-4 text-left sm:flex-row sm:items-center">
            <div className="flex-1"><p className="text-sm font-semibold" style={{ color: "var(--text)" }}>{t("home_resume_title")}</p><p className="mt-1 text-xs text-ui-muted">{t("home_resume_body")}</p></div>
            <button className="btn-secondary shrink-0 py-2 text-xs" onClick={() => navigate(`/analyzing/${pendingSession}`)}>{t("home_resume_cta")}</button>
          </div>
        )}

        <div className="flex w-full max-w-lg flex-col gap-3 sm:flex-row">
          <button className="btn-primary flex-1 text-base" onClick={() => navigate("/consent")}>{t("home_cta")}</button>
          <button className="btn-secondary flex-1 text-base" onClick={openSafeDemo} disabled={demoLoading}>{demoLoading ? t("home_demo_loading") : t("home_demo_cta")}</button>
        </div>
        <p className="mt-3 text-xs text-ui-subtle">{t("home_demo_note")}</p>
        {demoError && <p className="mt-2 text-xs text-rose-500">{demoError}</p>}

        <p className="mt-4 text-sm text-ui-subtle">{t("home_sub")}</p>
      </main>

      {/* Feature cards */}
      <section className="px-6 pb-20 max-w-5xl mx-auto w-full">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {features.map((feature) => (
            <div key={feature.title} className="card-glass p-6">
              <div className="mb-4"><FeatureIcon name={feature.icon} /></div>
              <h3 className="font-semibold mb-1" style={{ color: "var(--text)" }}>{feature.title}</h3>
              <p className="text-sm leading-relaxed text-ui-muted">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="px-6 pb-20 max-w-5xl mx-auto w-full">
        <div className="card-glass p-7 sm:p-10">
          <div className="max-w-2xl mb-8">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-600">{t("home_how_eyebrow")}</p>
            <h2 className="mt-2 text-2xl sm:text-3xl font-bold" style={{ color: "var(--text)" }}>{t("home_how_title")}</h2>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {steps.map(([number, title, description]) => (
              <div key={number} className="border-t border-ui pt-5">
                <span className="text-xs font-mono font-semibold text-teal-600">{number}</span>
                <h3 className="mt-3 font-semibold" style={{ color: "var(--text)" }}>{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-ui-muted">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-ui py-6 text-center text-xs text-ui-subtle px-4">
        {t("home_footer")}
      </footer>
    </div>
  );
}
