/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      colors: {
        bento: {
          peach: '#FAD4C0',
          steel: '#80A1C1',
          surface: '#0B0F17',
          card: '#0F172A',
          border: '#1E293B',
          muted: '#94A3B8',
          success: '#16A34A',
          warning: '#D97706',
          danger: '#DC2626',
        },
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      boxShadow: {
        'bento': '0 10px 30px -10px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05)',
        'bento-hover': '0 20px 40px -15px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(250, 212, 192, 0.15)',
        'glow-peach': '0 0 25px -5px rgba(250, 212, 192, 0.3)',
        'glow-steel': '0 0 25px -5px rgba(128, 161, 193, 0.3)',
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}
