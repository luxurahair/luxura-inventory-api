/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'luxura-gold': '#c9a050',
        'luxura-dark': '#0c0c0c',
        'luxura-gray': '#1a1a1a',
      },
    },
  },
  plugins: [],
}
