"use client"

type ThemeBackgroundsProps = {
  currentTheme?: string
}

export function ThemeBackgrounds({ currentTheme }: ThemeBackgroundsProps) {
  return (
    <div className="pointer-events-none absolute inset-0 -z-10">
      <div className="absolute inset-0 bg-[radial-gradient(1000px_600px_at_0%_-10%,hsl(var(--primary)/0.12),transparent),radial-gradient(800px_500px_at_100%_0%,hsl(var(--secondary)/0.12),transparent)] animate-[pulse_12s_ease-in-out_infinite]" />
      <div className="absolute inset-0 bg-gradient-to-b from-background/60 to-background" />
    </div>
  )
}


