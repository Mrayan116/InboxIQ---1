import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Gmail's actual palette: white surfaces, very light gray page bg,
        // blue for links/selection, red reserved for Compose + destructive
        // actions -- not sprinkled everywhere the way a generic "brand red"
        // theme would use it.
        bg: "#F6F8FC",
        surface: "#FFFFFF",
        ink: "#202124",
        muted: "#5F6368",
        border: "#E0E0E0",
        hover: "#F2F6FC",
        selected: "#D3E3FD",
        accent: {
          DEFAULT: "#1A73E8",
          hover: "#1B66C9",
          soft: "#E8F0FE",
        },
        compose: {
          DEFAULT: "#C2E7FF",
          text: "#001D35",
        },
        danger: {
          DEFAULT: "#D93025",
          hover: "#C5221F",
          soft: "#FCE8E6",
        },
        star: "#F4B400",
        priority: {
          critical: "#D93025",
          high: "#E37400",
          medium: "#F9AB00",
          low: "#80868B",
        },
      },
      fontFamily: {
        // Gmail uses Google Sans for headings and Roboto for UI text.
        // Google Sans isn't freely distributable, so Roboto (Gmail's own
        // fallback) covers both roles here.
        display: ["var(--font-sans)", "sans-serif"],
        sans: ["var(--font-sans)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      borderRadius: {
        sm: "6px",
        md: "10px",
        lg: "16px",
        full: "9999px",
      },
    },
  },
  plugins: [],
};
export default config;
