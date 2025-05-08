/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#2A5C8B',
          light: '#3D7AB8',
          dark: '#1F4468'
        },
        secondary: {
          DEFAULT: '#F07F3C',
          light: '#F59B66',
          dark: '#D66527'
        },
        neutral: {
          DEFAULT: '#4A4A4A',
          light: '#F5F5F5',
          dark: '#2D2D2D'
        },
        success: '#6BAF6B',
        error: '#E74C3C'
      },
      fontFamily: {
        poppins: ['Poppins', 'sans-serif'],
        'open-sans': ['Open Sans', 'sans-serif']
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.5s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
} 