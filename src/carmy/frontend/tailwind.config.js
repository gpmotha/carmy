/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary - Carmy Blue
        carmy: {
          DEFAULT: '#1C2A39',
          dark: '#141D28',
          light: '#2C3E50',
        },
        // Background - Kitchen White
        kitchen: {
          DEFAULT: '#F5F5F2',
          white: '#FFFFFF',
          warm: '#FAFAF8',
        },
        // Accent - Herb Green (success)
        herb: {
          DEFAULT: '#4E6E58',
          light: '#E8F0EA',
        },
        // Accent - Tomato Red (danger)
        tomato: {
          DEFAULT: '#B23A48',
          light: '#F8E8EA',
        },
        // Neutrals
        stone: {
          DEFAULT: '#6B7280',
          light: '#9CA3AF',
          dark: '#374151',
        },
        // Borders
        border: {
          DEFAULT: '#E5E5E0',
          light: '#F0F0EB',
        },
      },
      borderRadius: {
        'sm': '6px',   // Buttons, inputs
        'DEFAULT': '6px',
        'md': '8px',   // Cards
        'lg': '8px',
      },
      boxShadow: {
        'sm': '0 1px 3px rgba(0,0,0,0.06)',
        'DEFAULT': '0 2px 6px rgba(0,0,0,0.08)',
        'md': '0 2px 6px rgba(0,0,0,0.08)',
        'lg': '0 4px 12px rgba(0,0,0,0.10)',
        'card': '0 2px 6px rgba(0,0,0,0.08)',
        'hover': '0 4px 12px rgba(0,0,0,0.12)',
      },
      fontFamily: {
        // Canela alternative - elegant serif for headers
        serif: ['Cormorant Garamond', 'Georgia', 'serif'],
        // Helvetica Neue / system sans-serif for body
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Helvetica Neue', 'Helvetica', 'Arial', 'sans-serif'],
      },
      spacing: {
        // 8px grid system
        '1': '8px',
        '2': '16px',
        '3': '24px',
        '4': '32px',
        '5': '40px',
        '6': '48px',
        '0.5': '4px',
        '1.5': '12px',
        '2.5': '20px',
      },
    },
  },
  plugins: [],
}
