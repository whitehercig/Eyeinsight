/**
 * CameraRecorder
 * Manages camera access, live preview, and MediaRecorder lifecycle.
 * Calls onRecordingComplete with the final Blob when done.
 */

import { useEffect, useRef, useState, useImperativeHandle, forwardRef } from "react";
import { useApp } from "../context/AppContext";

export interface CameraRecorderHandle {
  startRecording: () => void;
  stopRecording: () => void;
}

interface Props {
  onRecordingComplete: (blob: Blob) => void;
  onCameraReady: () => void;
  onCameraError: (err: string) => void;
}

const CameraRecorder = forwardRef<CameraRecorderHandle, Props>(
  ({ onRecordingComplete, onCameraReady, onCameraError }, ref) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const recorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);
    const [isRecording, setIsRecording] = useState(false);
    const { t } = useApp();

    useEffect(() => {
      let mounted = true;

      async function initCamera() {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "user", width: 640, height: 480 },
            audio: false, // Audio not needed for visual screening
          });

          if (!mounted) {
            stream.getTracks().forEach((t) => t.stop());
            return;
          }

          streamRef.current = stream;
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
          }
          onCameraReady();
        } catch (err) {
          const msg =
            err instanceof Error ? err.message : "Camera access denied";
          onCameraError(msg);
        }
      }

      initCamera();

      return () => {
        mounted = false;
        // Clean up stream tracks on unmount
        streamRef.current?.getTracks().forEach((t) => t.stop());
      };
    }, [onCameraReady, onCameraError]);

    useImperativeHandle(ref, () => ({
      startRecording() {
        if (!streamRef.current) return;
        chunksRef.current = [];

        const mimeType = ["video/webm;codecs=vp9", "video/webm;codecs=vp8", "video/webm"]
          .find((candidate) => MediaRecorder.isTypeSupported(candidate));
        const options: MediaRecorderOptions = { videoBitsPerSecond: 2_000_000 };
        if (mimeType) options.mimeType = mimeType;
        const recorder = new MediaRecorder(streamRef.current, options);

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) chunksRef.current.push(e.data);
        };

        recorder.onstop = () => {
          const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "video/webm" });
          if (blob.size > 0) onRecordingComplete(blob);
          else onCameraError("Recording produced an empty video file");
          setIsRecording(false);
        };

        recorder.onerror = () => {
          onCameraError("The browser could not encode the recording");
          setIsRecording(false);
        };
        recorder.start();
        recorderRef.current = recorder;
        setIsRecording(true);
      },

      stopRecording() {
        if (recorderRef.current?.state === "recording") recorderRef.current.stop();
      },
    }));

    return (
      <div className="relative w-full rounded-2xl overflow-hidden border border-slate-800 bg-black shadow-xl shadow-slate-950/20">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full aspect-video object-cover scale-x-[-1]" // Mirror for natural selfie feel
        />
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center" aria-hidden="true">
          <div className="camera-guide-oval absolute" />
          <div className="camera-guide-corners absolute" />
          <div className="absolute bottom-4 rounded-full border border-teal-300/40 bg-slate-950/65 px-3 py-1.5 text-center text-xs font-medium text-teal-50 backdrop-blur-sm">
            {t("camera_face_guide")}
          </div>
        </div>
        {isRecording && (
          <div className="absolute top-3 right-3 flex items-center gap-2 bg-black/60 px-3 py-1.5 rounded-full">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
            <span className="text-white text-xs font-mono">REC</span>
          </div>
        )}
      </div>
    );
  }
);

CameraRecorder.displayName = "CameraRecorder";
export default CameraRecorder;
