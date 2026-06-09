/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eef9f4',
          100: '#d6f1e3',
          200: '#b0e3cb',
          300: '#7dcdb0',
          400: '#46b08e',
          500: '#259474',
          600: '#17765d',
          700: '#135f4c',
          800: '#114c3e',
          900: '#0f3f34',
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
