/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // SignAsili brand colors
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        // KSL visual colors
        ksl: {
          blue: '#0052cc',
          green: '#36b37e',
          yellow: '#ffab00',
          red: '#de350b',
        },
        // Accessibility colors
        accessibility: {
          high: '#000000',
          medium: '#666666',
          low: '#999999',
        },
      },
      fontFamily: {
        sans: ['var(--font-noto-sans)', 'system-ui', 'sans-serif'],
        sign: ['var(--font-sign-language)', 'sans-serif'],
      },
      animation: {
        'sign-motion': 'signMotion 2s ease-in-out infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        signMotion: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
