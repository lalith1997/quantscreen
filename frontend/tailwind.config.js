/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Light warm theme colors
        background: {
          primary: '#FDF8F0',
          secondary: '#F5EFE6',
          tertiary: '#EDE5D8',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          hover: '#F9F5EE',
          active: '#F2EDE4',
        },
        border: {
          DEFAULT: '#E8DFD0',
          hover: '#D4C9B8',
        },
        // Accent colors
        accent: {
          green: '#2D6A4F',
          red: '#E63946',
          blue: '#40916C',
          yellow: '#E9A820',
          purple: '#7C6DB0',
        },
        // Text colors
        text: {
          primary: '#1A1A2E',
          secondary: '#5A5A6E',
          tertiary: '#8A8A9A',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04)',
        'card-hover': '0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04)',
        'card-lg': '0 8px 24px rgba(0, 0, 0, 0.08), 0 4px 8px rgba(0, 0, 0, 0.04)',
      },
    },
  },
  plugins: [],
}
