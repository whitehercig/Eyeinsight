/**
 * Code resolvers — map backend codes to translated UI strings.
 *
 * Usage:
 *   resolveQualityIssue("lighting_low", "en")
 *
 * If a code is unknown (e.g. future ML model adds new codes),
 * we fall back to the raw code string so nothing breaks silently.
 */

import { QUALITY_ISSUE_TRANSLATIONS, type Lang } from "./translations";

export function resolveQualityIssue(code: string, lang: Lang): string {
  return QUALITY_ISSUE_TRANSLATIONS[code]?.[lang] ?? code;
}

/** Resolve a list of quality issue codes → translated strings */
export function resolveQualityIssues(codes: string[], lang: Lang): string[] {
  return codes.map((c) => resolveQualityIssue(c, lang));
}
