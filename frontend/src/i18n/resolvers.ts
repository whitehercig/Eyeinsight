/**
 * Code resolvers — map backend codes to translated UI strings.
 *
 * Usage:
 *   resolveSummary("low_risk_summary", "ru")
 *   resolveRecommendation("not_diagnosis", "kz")
 *   resolveQualityIssue("lighting_low", "en")
 *
 * If a code is unknown (e.g. future ML model adds new codes),
 * we fall back to the raw code string so nothing breaks silently.
 */

import {
  SUMMARY_TRANSLATIONS,
  RECOMMENDATION_TRANSLATIONS,
  QUALITY_ISSUE_TRANSLATIONS,
  type Lang,
} from "./translations";

export function resolveSummary(code: string, lang: Lang): string {
  return SUMMARY_TRANSLATIONS[code]?.[lang] ?? code;
}

export function resolveRecommendation(code: string, lang: Lang): string {
  return RECOMMENDATION_TRANSLATIONS[code]?.[lang] ?? code;
}

export function resolveQualityIssue(code: string, lang: Lang): string {
  return QUALITY_ISSUE_TRANSLATIONS[code]?.[lang] ?? code;
}

/** Resolve a list of recommendation codes → translated strings */
export function resolveRecommendations(codes: string[], lang: Lang): string[] {
  return codes.map((c) => resolveRecommendation(c, lang));
}

/** Resolve a list of quality issue codes → translated strings */
export function resolveQualityIssues(codes: string[], lang: Lang): string[] {
  return codes.map((c) => resolveQualityIssue(c, lang));
}
