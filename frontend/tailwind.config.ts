import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // Semua warna merek memakai CSS variable (lihat app/globals.css) agar
      // palet dapat diganti Admin lewat atribut data-theme di <html>.
      // Nilai default variabel = palet "native" (identik dengan warna asli).
      colors: {
        saffron: "rgb(var(--c-saffron) / <alpha-value>)",
        "deep-brown": "rgb(var(--c-deep-brown) / <alpha-value>)",
        cream: "rgb(var(--c-cream) / <alpha-value>)",
        terracotta: "rgb(var(--c-terracotta) / <alpha-value>)",
        sage: "rgb(var(--c-sage) / <alpha-value>)",
        ocean: "rgb(var(--c-ocean) / <alpha-value>)",
        sand: "rgb(var(--c-sand) / <alpha-value>)",
        charcoal: "rgb(var(--c-charcoal) / <alpha-value>)",
        "saffron-light": "rgb(var(--c-saffron-light) / <alpha-value>)",
        "saffron-dark": "rgb(var(--c-saffron-dark) / <alpha-value>)",
      },
      fontFamily: {
        sans: ["var(--font-jakarta)", "Inter", "system-ui", "sans-serif"],
        bali: ["Noto Sans Balinese", "sans-serif"],
        display: ["Fraunces", "serif"],
      },
      borderRadius: {
        "4xl": "2rem",
        "5xl": "2.5rem",
      },
      boxShadow: {
        "soft": "0 2px 10px rgba(44, 24, 16, 0.05)",
        "medium": "0 4px 20px rgba(44, 24, 16, 0.1)",
        "large": "0 10px 40px rgba(44, 24, 16, 0.15)",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out",
        "slide-up": "slideUp 0.5s ease-out",
        "bounce-soft": "bounceSoft 0.6s ease-out",
        "confetti": "confetti 0.8s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(20px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        bounceSoft: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        confetti: {
          "0%": { transform: "translateY(0) rotate(0deg)", opacity: "1" },
          "100%": { transform: "translateY(-100px) rotate(720deg)", opacity: "0" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
