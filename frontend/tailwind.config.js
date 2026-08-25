/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef4ff",
          100: "#dbe6fe",
          500: "#4f6df5",
          600: "#3c56e0",
          700: "#3045c0",
        },
      },
    },
  },
  plugins: [],
};
