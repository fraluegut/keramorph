/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ceramic: {
          50: "#fdf8f0",
          100: "#f9edd9",
          200: "#f2d9b0",
          300: "#e9be7e",
          400: "#df9f4e",
          500: "#d6852e",
          600: "#c46c22",
          700: "#a3531f",
          800: "#844321",
          900: "#6c381e",
          950: "#3a1b0e",
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'ceramic': '0 0 20px rgba(198, 108, 34, 0.15), 0 0 40px rgba(198, 108, 34, 0.1)',
        'ceramic-lg': '0 0 30px rgba(198, 108, 34, 0.2), 0 0 60px rgba(198, 108, 34, 0.15)',
      },
    },
  },
  plugins: [],
};
