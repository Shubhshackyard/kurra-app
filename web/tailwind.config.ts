import type { Config } from "tailwindcss";

export default {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "var(--font-noto-devanagari)", "system-ui", "sans-serif"],
        hindi: ["var(--font-noto-devanagari)", "var(--font-inter)", "system-ui", "sans-serif"],
      },
      colors: {
        court: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
          950: "#020617",
        },
        revenue: {
          blue: "#1e40af",
          amber: "#d97706",
          emerald: "#059669",
          crimson: "#dc2626",
        }
      },
      transitionDuration: {
        150: "150ms",
        200: "200ms",
        250: "250ms",
      }
    },
  },
  plugins: [],
} satisfies Config;
