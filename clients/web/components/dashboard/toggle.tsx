"use client"

/**
 * iOS-style toggle with symmetric thumb gap. The previous inline impl had
 * asymmetric translate math (thumb hugged the left but floated away from the
 * right when checked); this anchors the thumb at `left-0.5 top-0.5` as a
 * fixed offset so the translate values are symmetric.
 */
export function Toggle({
  checked,
  onChange,
  disabled,
  size = "md",
  label,
}: {
  checked: boolean
  onChange: (v: boolean) => void
  disabled?: boolean
  size?: "sm" | "md"
  label?: string
}) {
  const dims =
    size === "sm"
      ? {
          // 16×32 track, 12 thumb, travel 16 → track 32 - 12 - 2*2 = 16px
          track: "h-4 w-8",
          thumb: "h-3 w-3",
          translate: "translate-x-4",
        }
      : {
          // 24×44 track, 20 thumb, travel 20 → track 44 - 20 - 2*2 = 20px
          track: "h-6 w-11",
          thumb: "h-5 w-5",
          translate: "translate-x-5",
        }

  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => !disabled && onChange(!checked)}
      className={`relative shrink-0 rounded-full transition-colors duration-200 ease-out focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent-warm)] ${
        dims.track
      } ${
        checked
          ? "bg-[var(--color-accent-warm)]"
          : "bg-white/15 hover:bg-white/20"
      } ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
    >
      <span
        className={`absolute left-0.5 top-0.5 rounded-full shadow-[0_1px_3px_rgba(0,0,0,0.45)] transition-transform duration-200 ease-out ${
          dims.thumb
        } ${
          checked
            ? `${dims.translate} bg-[var(--color-surface)]`
            : "translate-x-0 bg-white"
        }`}
      />
    </button>
  )
}
