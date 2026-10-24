import { useId } from 'react'

export interface VyaparMitraLogoProps {
  className?: string
  size?: number
  showBadge?: boolean
  tagline?: string
}

/**
 * VyaparMitraLogo — Modern, sleek brand logo for Vyapar Mitra.
 * Combines geometric interlocking 'V' & 'M' motifs with an upward-trending
 * commerce arrow and prosperity crest against a deep emerald & teal gradient.
 */
export function VyaparMitraLogo({
  className = 'w-10 h-10',
  size = 40,
}: {
  className?: string
  size?: number
}) {
  const id = useId().replace(/:/g, '')
  const gradId = `vm-gradient-${id}`
  const accentId = `vm-accent-${id}`
  const glowId = `vm-glow-${id}`

  return (
    <svg
      className={className}
      viewBox="0 0 44 44"
      width={size}
      height={size}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        {/* Emerald to deep forest teal gradient */}
        <linearGradient id={gradId} x1="2" y1="2" x2="42" y2="42" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#059669" />
          <stop offset="55%" stopColor="#047857" />
          <stop offset="100%" stopColor="#064E3B" />
        </linearGradient>

        {/* Auspicious golden amber accent gradient */}
        <linearGradient id={accentId} x1="16" y1="8" x2="28" y2="22" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FDE68A" />
          <stop offset="40%" stopColor="#F59E0B" />
          <stop offset="100%" stopColor="#D97706" />
        </linearGradient>

        {/* Soft radial glow */}
        <radialGradient id={glowId} cx="22" cy="14" r="18" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.22" />
          <stop offset="100%" stopColor="#FFFFFF" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Outer rounded squircle badge */}
      <rect x="2" y="2" width="40" height="40" rx="11" fill={`url(#${gradId})`} />

      {/* Subtle glass rim highlight */}
      <rect
        x="2.5"
        y="2.5"
        width="39"
        height="39"
        rx="10.5"
        stroke="white"
        strokeOpacity="0.18"
        strokeWidth="1"
      />

      {/* Internal subtle glow */}
      <circle cx="22" cy="14" r="14" fill={`url(#${glowId})`} />

      {/* Foundation ledger register lines (commerce grounding) */}
      <rect x="13" y="32" width="18" height="2" rx="1" fill="white" fillOpacity="0.3" />

      {/* Interlocking 'V' (Vyapar) & 'M' (Mitra) Modern Monogram */}
      {/* Outer dynamic 'V' stroke sweeping through the base */}
      <path
        d="M11 15L20.8 30.2C21.4 31.1 22.6 31.1 23.2 30.2L33 15"
        stroke="white"
        strokeWidth="3.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Center ascending Growth Arrow & 'M' Crest */}
      <path
        d="M16 20.5L22 11.5L28 20.5"
        stroke={`url(#${accentId})`}
        strokeWidth="3.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Auspicious prosperity apex star/diamond (Shubh-Laabh crest) */}
      <circle cx="22" cy="7.5" r="1.75" fill="#FEF08A" />
      <circle cx="22" cy="7.5" r="2.75" stroke="#FBBF24" strokeWidth="0.75" strokeOpacity="0.7" />
    </svg>
  )
}

export default VyaparMitraLogo
