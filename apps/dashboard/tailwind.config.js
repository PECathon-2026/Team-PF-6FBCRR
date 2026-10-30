/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a0d14',
        surface: '#111827',
        surfaceSubtle: '#1f2937',
        border: '#374151',
        brand: {
          50: '#f0fdf4',
          500: '#22c55e',
          600: '#16a34a',
        },
        privacy: {
          safe: '#10b981',
          warning: '#f59e0b',
          danger: '#ef4444',
          redacted: '#a855f7',
        }
      },
    },
  },
  plugins: [],
}

