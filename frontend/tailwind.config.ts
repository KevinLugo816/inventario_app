import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        fondo: "#1a1a1a",
        fondo2: "#262626",
        naranja: "#ff8c1a",
        naranja2: "#ffa64d",
      },
    },
  },
} satisfies Config;
