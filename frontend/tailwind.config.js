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
    },
  },
  plugins: [],
};
