/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          50:  "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81",
        },
        surface: {
          900: "#0f0f1a",
          800: "#16162a",
          700: "#1e1e35",
          600: "#252540",
          500: "#2e2e50",
        },
      },
      backgroundImage: {
        "hero-gradient": "linear-gradient(135deg, #312e81 0%, #1e1e35 50%, #0f0f1a 100%)",
        "card-gradient": "linear-gradient(145deg, rgba(99,102,241,0.12), rgba(30,30,53,0.8))",
        "button-gradient": "linear-gradient(135deg, #6366f1, #4f46e5)",
      },
      animation: {
        "spin-slow": "spin 2s linear infinite",
        "pulse-slow": "pulse 3s ease-in-out infinite",
        "fade-in": "fadeIn 0.4s ease-out",
        "slide-up": "slideUp 0.4s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      boxShadow: {
        "glow": "0 0 30px rgba(99, 102, 241, 0.25)",
        "glow-sm": "0 0 15px rgba(99, 102, 241, 0.15)",
        "card": "0 4px 24px rgba(0, 0, 0, 0.4)",
      },
    },
  },
  plugins: [],
}
