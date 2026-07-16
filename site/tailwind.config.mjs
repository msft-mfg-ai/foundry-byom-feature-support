/** @type {import('tailwindcss').Config} */
import typography from '@tailwindcss/typography';
export default {
  content: ['./src/**/*.{astro,html,js,ts,md,mdx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      colors: {
        brand: {
          50: '#eef6ff',
          100: '#d9eaff',
          200: '#bcd9ff',
          300: '#8ebfff',
          400: '#599cff',
          500: '#3279ff',
          600: '#1d5bf5',
          700: '#1747dd',
          800: '#173cb1',
          900: '#19388b',
        },
      },
    },
  },
  plugins: [typography],
};
