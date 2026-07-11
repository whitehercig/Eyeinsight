/**
 * EyeInsightLogo
 * SVG recreation of the brand logo:
 * - Eye outline with teal/cyan gradient bottom lid
 * - Targeting crosshair pupil
 * - Orbital tracking dots + arc
 * - "EyeInsight" wordmark (Eye in white, Insight in teal gradient)
 */

interface Props {
  /** Total width in px. Height is auto-proportional. */
  size?: number;
  /** Show text wordmark below icon */
  showText?: boolean;
  /** If true, render horizontally (icon + text side by side) */
  horizontal?: boolean;
}

export default function EyeInsightLogo({
  size = 48,
  showText = true,
  horizontal = false,
}: Props) {
  const iconSize = size;

  const icon = (
    <svg
      width={iconSize}
      height={iconSize * 0.7}
      viewBox="0 0 120 84"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="lidGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#00b4d8" />
          <stop offset="100%" stopColor="#48cae4" />
        </linearGradient>
        <linearGradient id="arcGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#00b4d8" />
          <stop offset="100%" stopColor="#90e0ef" />
        </linearGradient>
      </defs>

      {/* Upper eyelid — white */}
      <path
        d="M10 42 C30 12, 90 12, 110 42"
        stroke="white"
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
      />

      {/* Lower eyelid — teal gradient */}
      <path
        d="M10 42 C30 72, 90 72, 110 42"
        stroke="url(#lidGrad)"
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
      />

      {/* Outer iris circle — white */}
      <circle cx="60" cy="42" r="20" stroke="white" strokeWidth="2.5" fill="none" />

      {/* Inner pupil circle — white */}
      <circle cx="60" cy="42" r="10" stroke="white" strokeWidth="2" fill="none" />

      {/* Crosshair — white */}
      <line x1="60" y1="22" x2="60" y2="28" stroke="white" strokeWidth="2" strokeLinecap="round" />
      <line x1="60" y1="56" x2="60" y2="62" stroke="white" strokeWidth="2" strokeLinecap="round" />
      <line x1="40" y1="42" x2="46" y2="42" stroke="white" strokeWidth="2" strokeLinecap="round" />
      <line x1="74" y1="42" x2="80" y2="42" stroke="white" strokeWidth="2" strokeLinecap="round" />

      {/* Center dot — teal */}
      <circle cx="60" cy="42" r="3.5" fill="#00b4d8" />

      {/* Orbital tracking arc */}
      <path
        d="M34 50 Q60 62 86 42"
        stroke="url(#arcGrad)"
        strokeWidth="1.8"
        fill="none"
        strokeLinecap="round"
      />

      {/* Left tracking dot */}
      <circle cx="34" cy="50" r="3.5" fill="#00b4d8" />

      {/* Right tracking dot — outline style */}
      <circle cx="86" cy="42" r="4" stroke="#90e0ef" strokeWidth="2" fill="none" />

      {/* Arrow tip on arc */}
      <path
        d="M82 39 L86 42 L82 45"
        stroke="#90e0ef"
        strokeWidth="1.8"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );

  const wordmark = (
    <span
      style={{ fontSize: size * 0.38 }}
      className="font-bold tracking-tight select-none leading-none"
    >
      <span className="text-white">Eye</span>
      <span
        style={{
          background: "linear-gradient(90deg, #00b4d8, #90e0ef)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
        }}
      >
        Insight
      </span>
    </span>
  );

  if (!showText) return icon;

  if (horizontal) {
    return (
      <div className="flex items-center gap-3">
        {icon}
        {wordmark}
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-2">
      {icon}
      {wordmark}
    </div>
  );
}
