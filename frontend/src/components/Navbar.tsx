/**
 * Navbar — top bar with logo, language switcher, and dark/light theme toggle.
 * Used across all pages.
 */

import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import EyeInsightLogo from "./EyeInsightLogo";
import type { Lang } from "../i18n/translations";

const LANGS: { code: Lang; label: string; flag: string }[] = [
  { code: "en", label: "EN", flag: "🇬🇧" },
  { code: "ru", label: "RU", flag: "🇷🇺" },
  { code: "kz", label: "KZ", flag: "🇰🇿" },
];

interface Props {
  /** Show "back to home" click on logo */
  homeLink?: boolean;
}

export default function Navbar({ homeLink = false }: Props) {
  const { lang, setLang, theme, toggleTheme, t } = useApp();
  const navigate = useNavigate();

  return (
    <nav className="navbar w-full px-4 sm:px-6 py-4 flex items-center justify-between border-b">
      {/* Logo */}
      <button
        onClick={() => homeLink && navigate("/")}
        className={homeLink ? "cursor-pointer" : "cursor-default"}
        aria-label="EyeInsight home"
      >
        <EyeInsightLogo size={36} horizontal />
      </button>

      {/* Right controls */}
      <div className="flex items-center gap-2">
        {/* Badge */}
        <span className="nav-badge hidden sm:inline text-xs font-mono px-2.5 py-1 border rounded-full">
          {t("nav_badge")}
        </span>

        {/* Language switcher */}
        <div className="nav-control flex items-center rounded-xl overflow-hidden border">
          {LANGS.map((l) => (
            <button
              key={l.code}
              onClick={() => setLang(l.code)}
              className={`px-2.5 py-1.5 text-xs font-semibold transition-colors ${
                lang === l.code
                  ? "bg-teal-500 text-white"
                  : "text-ui-muted hover:text-teal-600 dark:hover:text-teal-400"
              }`}
              title={l.flag}
            >
              {l.label}
            </button>
          ))}
        </div>

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="nav-control w-9 h-9 rounded-xl flex items-center justify-center border transition-all"
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        >
          {theme === "dark" ? "☀️" : "🌙"}
        </button>
      </div>
    </nav>
  );
}
