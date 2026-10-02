import type { Config } from "tailwindcss";

// MODERN INDIAN FINANCIAL OBSERVATORY: midnight navy, warm ivory, muted saffron/gold, restrained maroon, muted emerald, muted red.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        midnight: { DEFAULT: "#0E1A33", 800: "#16264A", 700: "#1F3260", 600: "#2B4380" },
        ivory: { DEFAULT: "#FBF6EA", 100: "#F6EFDD", 200: "#EDE3C9", 300: "#E0D3B0" },
        saffron: { DEFAULT: "#8F5A08", 400: "#D79B2E", 300: "#E8C16A", 100: "#F8EBC7" },
        maroon: { DEFAULT: "#7A2432", 100: "#F2DDE0" },
        emerald: { DEFAULT: "#25694A", 100: "#D9EBE1" },
        danger: { DEFAULT: "#A33B36", 100: "#F5DEDC" },
        ink: { DEFAULT: "#1B2236", muted: "#4C566E", faint: "#5B6580" },
        line: "#DCD0B1",
        series: { blue: "#3A5FA0", gold: "#C0841A", green: "#1F8F5F", red: "#A8323E" },
      },
      fontFamily: {
        sans: ['"Segoe UI"', "system-ui", "-apple-system", '"Noto Sans"', '"Noto Sans Devanagari"', '"Nirmala UI"', "Roboto", "sans-serif"],
        serif: ['"Iowan Old Style"', '"Palatino Linotype"', "Palatino", '"Noto Serif"', '"Noto Serif Devanagari"', '"Nirmala UI"', "Georgia", "serif"],
      },
      boxShadow: { card: "0 1px 0 rgba(14,26,51,.04), 0 8px 24px -12px rgba(14,26,51,.18)" },
      keyframes: { rise: { from: { opacity: "0", transform: "translateY(8px)" }, to: { opacity: "1", transform: "none" } } },
      animation: { rise: "rise .45s ease-out both" },
    },
  },
  plugins: [],
};
export default config;
