/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        radar: {
          dark: "#0b0f19",
          card: "#121826",
          border: "#1f293d",
          adopt: "#10b981",
          trial: "#3b82f6",
          assess: "#f59e0b",
          hold: "#ef4444",
        }
      }
    },
  },
  plugins: [],
}
