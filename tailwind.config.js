/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        border: 'var(--border)',
        input: 'var(--input)',
        ring: 'var(--ring)',
        background: 'var(--bg)',
        foreground: 'var(--text)',
        primary: {
          DEFAULT: 'var(--brand)',
          foreground: 'black',
        },
        secondary: {
          DEFAULT: 'var(--bg-3)',
          foreground: 'var(--text)',
        },
        destructive: {
          DEFAULT: 'var(--error)',
          foreground: 'white',
        },
        muted: {
          DEFAULT: 'var(--bg-3)',
          foreground: 'var(--text-muted)',
        },
        accent: {
          DEFAULT: 'var(--accent)',
          foreground: 'var(--accent)',
        },
        popover: {
          DEFAULT: 'var(--bg-elevated)',
          foreground: 'var(--text)',
        },
        card: {
          DEFAULT: 'var(--bg-elevated)',
          foreground: 'var(--text)',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
