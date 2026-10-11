/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#060B14',
          900: '#0B132B',
          850: '#0F172A',
          800: '#1C2541',
          700: '#3A506B',
          600: '#475569',
        },
        signal: {
          red: '#EF4444',
          'red-glow': 'rgba(239, 68, 68, 0.25)',
          amber: '#F59E0B',
          'amber-glow': 'rgba(245, 158, 11, 0.25)',
          green: '#10B981',
          'green-glow': 'rgba(16, 185, 129, 0.25)',
          blue: '#3B82F6',
          cyan: '#06B6D4'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      }
    },
  },
  plugins: [],
}
