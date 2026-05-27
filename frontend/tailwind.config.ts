import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx,js,jsx}", "./components/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      boxShadow: {
        glow: "0 0 0 1px rgba(99,102,241,0.15), 0 0 25px rgba(99,102,241,0.25)",
      },
      backgroundImage: {
        "ai-gradient":
          "radial-gradient(650px circle at 20% 10%, rgba(99,102,241,0.30), transparent 40%), radial-gradient(450px circle at 80% 0%, rgba(34,211,238,0.18), transparent 35%), radial-gradient(500px circle at 50% 80%, rgba(168,85,247,0.15), transparent 45%)",
      },
    },
  },
  plugins: [],
};

export default config;

