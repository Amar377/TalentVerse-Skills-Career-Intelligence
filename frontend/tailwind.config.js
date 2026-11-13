/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          50: '#fffcf7', 100: '#f6f0e8', 200: '#e7ded3', 300: '#d8cdc1',
          400: '#b7a9ac', 500: '#817780', 600: '#655b64', 700: '#4d444c',
          800: '#3b333c', 900: '#29232a', 950: '#211923',
        },
        indigo: {
          50: '#f3edf2', 100: '#e8dce6', 200: '#d1b9cd', 300: '#b795b3',
          400: '#98728f', 500: '#75546f', 600: '#62445d', 700: '#51384e',
          800: '#422e41', 900: '#351e36', 950: '#281626',
        },
        violet: {
          50: '#f4f0f3', 100: '#e9e1e8', 200: '#d6c8d5', 300: '#bba5bb',
          400: '#9b809c', 500: '#756477', 600: '#655468', 700: '#554558',
          800: '#443747', 900: '#352a37', 950: '#281f2b',
        },
        emerald: {
          50: '#f0f2ed', 100: '#e0e5db', 200: '#c4cebb', 300: '#a5b197',
          400: '#899879', 500: '#75816b', 600: '#626f58', 700: '#505b49',
          800: '#414a3c', 900: '#343b31', 950: '#252b24',
        },
        cyan: {
          50: '#f0f2ed', 100: '#e0e5db', 200: '#c4cebb', 300: '#a5b197',
          400: '#899879', 500: '#75816b', 600: '#626f58', 700: '#505b49',
          800: '#414a3c', 900: '#343b31', 950: '#252b24',
        },
        amber: {
          50: '#faf3e9', 100: '#f3e5cf', 200: '#e8cda5', 300: '#ddb77f',
          400: '#d6a66a', 500: '#c58e4c', 600: '#a8743b', 700: '#85582f',
          800: '#68462b', 900: '#523923', 950: '#302014',
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        brand: {
          50: '#fbf0eb',
          100: '#f5dfd5',
          200: '#ecc4b4',
          300: '#dca08b',
          400: '#c8755b',
          500: '#a64b35',
          600: '#913c2b',
          700: '#773025',
          800: '#5d2726',
          900: '#351e36',
          950: '#281626',
        },
        navy: {
          800: '#453846',
          850: '#352a37',
          900: '#281f2b',
          950: '#211923',
        },
        accent: {
          cyan: '#75816b',
          violet: '#756477',
          emerald: '#75816b',
          amber: '#d6a66a',
          rose: '#f43f5e',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'glow': '0 8px 28px -12px rgba(53, 30, 54, 0.28)',
        'glow-cyan': '0 8px 24px -12px rgba(117, 129, 107, 0.32)',
        'subtle': '0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03)',
        'card': '0 4px 20px -2px rgba(0, 0, 0, 0.05)',
        'card-dark': '0 4px 25px -2px rgba(0, 0, 0, 0.4)',
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.35s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        }
      }
    },
  },
  plugins: [],
}
