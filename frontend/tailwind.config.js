/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Sora', 'sans-serif'],
        mono: ['DM Mono', 'monospace'],
      },
      colors: {
        'cc-amber': {
          DEFAULT: '#FAEEDA',
          text: '#854F0B',
          border: '#FAC775',
        },
        'cc-green': {
          DEFAULT: '#EAF3DE',
          text: '#3B6D11',
          border: '#C0DD97',
        },
        'cc-red': {
          DEFAULT: '#FCEBEB',
          text: '#A32D2D',
          border: '#F09595',
        },
      },
    },
  },
  plugins: [],
}
