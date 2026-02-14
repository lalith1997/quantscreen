/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark theme colors
        background: {
          primary: '#0a0a0a',
          secondary: '#141414',
          tertiary: '#1f1f1f',
        },
        surface: {
          DEFAULT: '#1a1a1a',
          hover: '#252525',
          active: '#2a2a2a',
        },
        border: {
          DEFAULT: '#2a2a2a',
          hover: '#3a3a3a',
        },
        // Accent colors
        accent: {
          green: '#00d26a',
          red: '#ff4757',
          blue: '#0095ff',
          yellow: '#ffc107',
          purple: '#8b5cf6',
        },
        // Text colors
        text: {
          primary: '#ffffff',
          secondary: '#a0a0a0',
          tertiary: '#666666',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
