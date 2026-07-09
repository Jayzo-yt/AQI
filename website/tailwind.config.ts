import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'SF Pro Display', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      colors: {
        dark: {
          950: '#0B0F14',
          900: '#111820',
          800: '#151F2C',
          700: '#1e293b',
          600: '#334155',
          500: '#475569',
          400: '#64748b',
          300: '#94a3b8',
          200: '#cbd5e1',
          100: '#f1f5f9',
        },
        mission: {
          bg: '#0B0F14',
          panel: '#111820',
          secondary: '#151F2C',
          accent: '#2EA8FF',
          success: '#3CD96B',
          warning: '#FFC84A',
          danger: '#FF5E57',
          severe: '#C026D3',
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
      boxShadow: {
        'soft-glow': '0 0 15px rgba(46, 168, 255, 0.15)',
        'panel': '0 4px 30px rgba(0, 0, 0, 0.4)',
      }
    },
  },
  plugins: [],
  darkMode: 'class',
}
export default config
