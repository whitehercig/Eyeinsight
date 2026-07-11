import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import Navbar from "../components/Navbar";
import EyeInsightLogo from "../components/EyeInsightLogo";

export default function HomePage() {
  const navigate = useNavigate();
  const { t } = useApp();

  const features = [
    { icon: "📷", title: t("home_f1_title"), desc: t("home_f1_desc") },
    { icon: "⏱",  title: t("home_f2_title"), desc: t("home_f2_desc") },
    { icon: "🧠", title: t("home_f3_title"), desc: t("home_f3_desc") },
    { icon: "⚕️", title: t("home_f4_title"), desc: t("home_f4_desc") },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-16 text-center max-w-3xl mx-auto w-full animate-slide-up">
        {/* Logo */}
        <div className="mb-10 relative">
          <div className="w-28 h-28 rounded-full flex items-center justify-center mx-auto"
            style={{ background: "rgba(20,184,166,0.07)", border: "1px solid rgba(20,184,166,0.2)" }}>
            <EyeInsightLogo size={72} showText={false} />
          </div>
          <div className="absolute inset-0 w-28 h-28 mx-auto rounded-full blur-2xl"
            style={{ background: "rgba(20,184,166,0.12)" }} />
        </div>

        <h1 className="text-4xl sm:text-5xl font-bold leading-tight mb-4 tracking-tight"
          style={{ color: "var(--text)" }}>
          {t("home_title")}
        </h1>

        <p className="text-lg sm:text-xl max-w-xl mb-6 leading-relaxed text-ui-muted">
          {t("home_subtitle")}
        </p>

        <div className="disclaimer-banner mb-10 max-w-lg text-left">
          <strong>{t("home_disclaimer_title")}</strong>{" "}
          {t("home_disclaimer_body")}
        </div>

        <button className="btn-primary text-lg mb-4" onClick={() => navigate("/consent")}>
          {t("home_cta")}
        </button>

        <p className="text-sm text-ui-subtle">{t("home_sub")}</p>
      </main>

      {/* Feature cards */}
      <section className="px-6 pb-20 max-w-5xl mx-auto w-full">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {features.map((f) => (
            <div key={f.title} className="card-glass p-6">
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="font-semibold mb-1" style={{ color: "var(--text)" }}>{f.title}</h3>
              <p className="text-sm leading-relaxed text-ui-muted">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-ui py-6 text-center text-xs text-ui-subtle px-4">
        {t("home_footer")}
      </footer>
    </div>
  );
}
