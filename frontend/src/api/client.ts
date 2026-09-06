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
}

export interface CameraReadiness {
  ready: boolean;
  checks: Record<"lighting" | "face_in_frame" | "distance" | "stability", boolean>;
  issues: string[];
  metrics: Record<string, number>;
}

/**
 * AnalysisResult — all text fields are i18n codes.
 * The frontend maps them to translated strings.
 */
export interface AnalysisResult {
  session_id: string;
  risk_score: number | null;          // legacy compatibility field; current MVP returns null
  risk_level: "low" | "moderate" | "elevated" | null; // legacy compatibility field
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
  summary_code: string;               // legacy compatibility code
  recommendation_codes: string[];     // legacy compatibility codes
  source_video_deleted: boolean;
  is_demo: boolean;
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

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options?: RequestInit, timeoutMs = 20_000): Promise<T> {
  const controller = new AbortController();
  const relayAbort = () => controller.abort();
  options?.signal?.addEventListener("abort", relayAbort, { once: true });
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${BASE}${path}`, { ...options, signal: controller.signal });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new ApiError(body.detail ?? `HTTP ${response.status}`, response.status);
    }
    return response.json() as Promise<T>;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("request_timeout", 408);
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
    options?.signal?.removeEventListener("abort", relayAbort);
  }
}

export const createSession = (): Promise<SessionResponse> =>
  request<SessionResponse>("/sessions", { method: "POST" });

export const getSession = (sessionId: string): Promise<SessionResponse> =>
  request<SessionResponse>(`/sessions/${sessionId}`);

export const createDemoSession = (): Promise<SessionResponse> =>
  request<SessionResponse>("/sessions/demo", { method: "POST" }, 30_000);

export const checkCamera = (frames: Blob[]): Promise<CameraReadiness> => {
  const form = new FormData();
  frames.forEach((frame, index) => form.append("files", frame, `camera-check-${index}.jpg`));
  return request<CameraReadiness>("/camera-check", { method: "POST", body: form }, 30_000);
};

export const uploadVideo = (sessionId: string, blob: Blob): Promise<SessionResponse> => {
  const form = new FormData();
  form.append("file", blob, `${sessionId}.webm`);
  return request<SessionResponse>(`/sessions/${sessionId}/upload-video`, {
    method: "POST",
    body: form,
  });
};

export const analyzeSession = (sessionId: string, retry = false): Promise<AnalysisResult> =>
  request<AnalysisResult>(`/analyze-session/${sessionId}${retry ? "?retry=true" : ""}`, { method: "POST" }, 90_000);

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
