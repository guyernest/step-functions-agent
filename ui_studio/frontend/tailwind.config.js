/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'studio-bg': '#1a1a2e',
        'studio-panel': '#16213e',
        'studio-accent': '#0f3460',
        'studio-highlight': '#e94560',
      },
    },
  },
  plugins: [],
}
