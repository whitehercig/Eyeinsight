/**
 * EyeInsight API client — typed wrappers around backend endpoints.
 *
 * ARCHITECTURE: The backend returns CODES, not translated text.
 * All human-readable strings are resolved on the frontend via i18n.
 */

const BASE = "/api";

export interface SessionResponse {
  id: string;
  created_at: string;
  status: string;
  video_path: string | null;
}

/**
 * AnalysisResult — all text fields are i18n codes.
 * The frontend maps them to translated strings.
 */
export interface AnalysisResult {
  session_id: string;
  risk_score: number | null;          // null when quality_failed
  risk_level: "low" | "moderate" | "elevated" | null;
  quality_score: number;
  quality_failed: boolean;
  quality_issues: string[];           // e.g. ["lighting_low", "face_not_visible"]
  quality_metrics?: Record<string, unknown>; // local/dev debugging metrics
  attention_score?: number | null;
  attention_level?: string | null;
  score_breakdown?: Record<string, number>;
  score_explanation?: string | null;
  risk_confidence?: number | null;
  risk_confidence_type?: string | null;
  top_contributing_factors?: { factor: string; contribution: number }[];
  summary_code: string;               // e.g. "low_risk_summary"
  recommendation_codes: string[];     // e.g. ["not_diagnosis", "consult_specialist"]
  created_at: string;
}

export interface FeatureBundle {
  session_id: string;
  quality_metrics: Record<string, number | string>;
  frame_preview: Record<string, number | string | null>[];
  phase_features: Record<string, number | string | null>[];
  session_features: Record<string, unknown>;
  attention_score: number | null;
  attention_level: string | null;
  visualizations: {
    gaze_heatmap?: number[][];
    gaze_path?: {
      timestamp: number;
      gaze_screen_x: number;
      gaze_screen_y: number;
      target_screen_x: number;
      target_screen_y: number;
      target_aligned: number;
    }[];
  };
  downloads: Record<string, string>;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const createSession = (): Promise<SessionResponse> =>
  request<SessionResponse>("/sessions", { method: "POST" });

export const uploadVideo = (sessionId: string, blob: Blob): Promise<SessionResponse> => {
  const form = new FormData();
  form.append("file", blob, `${sessionId}.webm`);
  return request<SessionResponse>(`/sessions/${sessionId}/upload-video`, {
    method: "POST",
    body: form,
  });
};

export const analyzeSession = (sessionId: string): Promise<AnalysisResult> =>
  request<AnalysisResult>(`/analyze-session/${sessionId}`, { method: "POST" });

export const getResult = (sessionId: string): Promise<AnalysisResult> =>
  request<AnalysisResult>(`/sessions/${sessionId}/result`);

export const getFeatures = (sessionId: string): Promise<FeatureBundle> =>
  request<FeatureBundle>(`/sessions/${sessionId}/features`);

export const deleteSession = (sessionId: string): Promise<void> =>
  fetch(`${BASE}/sessions/${sessionId}`, { method: "DELETE" }).then(async (response) => {
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail ?? `HTTP ${response.status}`);
    }
  });
