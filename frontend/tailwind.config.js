/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fdfbf7',
          100: '#faf5eb',
          200: '#f3e7ce',
          300: '#ebd4a7',
          400: '#dbbc7c',
          500: '#C6A15B',
          600: '#b38e4a',
          700: '#967439',
          800: '#785b2b',
          900: '#5a431f',
          950: '#3b2c14',
        },
        accent: {
          50: '#fdfbf7',
          100: '#faf5eb',
          200: '#f3e7ce',
          300: '#ebd4a7',
          400: '#dbbc7c',
          500: '#C6A15B',
          600: '#b38e4a',
          700: '#967439',
          800: '#785b2b',
          900: '#5a431f',
          950: '#3b2c14',
        },
        gold: {
          50: '#fdfbf7',
          100: '#faf5eb',
          200: '#f3e7ce',
          300: '#ebd4a7',
          400: '#dbbc7c',
          500: '#C6A15B',
          600: '#b38e4a',
          700: '#967439',
          800: '#785b2b',
          900: '#5a431f',
        },
        ink: '#1e1813',
        canvas: '#fdf8f3',
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Manrope', 'system-ui', 'sans-serif'],
        display: ['"Plus Jakarta Sans"', 'Manrope', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 2px 8px -1px rgba(17, 24, 39, 0.06), 0 1px 4px -1px rgba(17, 24, 39, 0.04)',
        'soft-lg': '0 12px 32px -8px rgba(17, 24, 39, 0.14), 0 4px 12px -2px rgba(17, 24, 39, 0.06)',
        'soft-xl': '0 24px 60px -12px rgba(17, 24, 39, 0.18), 0 8px 24px -4px rgba(17, 24, 39, 0.08)',
        'inner-soft': 'inset 0 2px 4px 0 rgba(17, 24, 39, 0.05)',
        'glow-primary': '0 0 0 1px rgba(124, 58, 237, 0.15), 0 8px 32px -4px rgba(124, 58, 237, 0.35)',
        'glow-gold': '0 0 0 1px rgba(249, 168, 38, 0.2), 0 8px 32px -4px rgba(249, 168, 38, 0.35)',
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out',
        'slide-up': 'slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-down': 'slideDown 0.4s ease-out',
        'scale-in': 'scaleIn 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
        'shimmer': 'shimmer 2s infinite',
        'float': 'float 6s ease-in-out infinite',
        'float-slow': 'float 10s ease-in-out infinite',
        'gradient-x': 'gradientX 8s ease infinite',
        'blob': 'blob 14s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(28px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-14px)' },
        },
        gradientX: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        blob: {
          '0%, 100%': { transform: 'translate(0px, 0px) scale(1)' },
          '33%': { transform: 'translate(30px, -40px) scale(1.1)' },
          '66%': { transform: 'translate(-20px, 20px) scale(0.95)' },
        },
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
        '4xl': '2rem',
      },
      backgroundSize: {
        '200%': '200% 200%',
      },
    },
  },
  plugins: [],
}
