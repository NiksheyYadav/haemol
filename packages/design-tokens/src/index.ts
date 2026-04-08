export const designTokens = {
  color: {
    canvas: "#f5f7f4",
    canvasDark: "#0e1512",
    surface: "#ffffff",
    surfaceMuted: "#edf3ef",
    surfaceDark: "#15201b",
    cardDark: "#1b2822",
    text: "#14211b",
    textMuted: "#4f665a",
    textOnDark: "#f4faf6",
    primary: "#0e8f64",
    primaryStrong: "#0a6f4d",
    secondary: "#1d5d91",
    accent: "#e97d35",
    danger: "#c7423d",
    warning: "#a8670a",
    success: "#20744c",
    border: "#c9d9cf",
    borderDark: "#2a3a33"
  },
  typography: {
    display: "'Space Grotesk', 'Segoe UI', sans-serif",
    body: "'Plus Jakarta Sans', 'Segoe UI', sans-serif",
    mono: "'IBM Plex Mono', 'Courier New', monospace"
  },
  radius: {
    sm: "12px",
    md: "18px",
    lg: "28px",
    pill: "999px"
  },
  spacing: {
    xs: "0.25rem",
    sm: "0.5rem",
    md: "1rem",
    lg: "1.5rem",
    xl: "2rem",
    "2xl": "3rem",
    "3xl": "4rem"
  },
  shadow: {
    soft: "0 20px 60px rgba(13, 37, 24, 0.08)",
    card: "0 24px 48px rgba(8, 24, 16, 0.12)",
    glow: "0 0 0 1px rgba(14, 143, 100, 0.15), 0 18px 44px rgba(14, 143, 100, 0.14)"
  },
  motion: {
    fast: "160ms ease",
    base: "240ms cubic-bezier(0.2, 0.8, 0.2, 1)",
    slow: "420ms cubic-bezier(0.2, 0.8, 0.2, 1)"
  }
} as const;

export type DesignTokens = typeof designTokens;
