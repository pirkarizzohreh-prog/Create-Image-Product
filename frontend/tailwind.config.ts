import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef4ff",
          100: "#dbe6fe",
          200: "#bed0fd",
          300: "#91b1fb",
          400: "#5e87f7",
          500: "#3b63f0",
          600: "#2745e4",
          700: "#2135c9",
          800: "#212ea3",
          900: "#202c80",
        },
      },
    },
  },
  plugins: [],
};

export default config;
