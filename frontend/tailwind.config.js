/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  plugins: [require("daisyui")],
  daisyui: {
      themes: ["light", "dark","cupcake","bumblebee","synthwave","coffee","lemonade","winter"], // Use your preferred themes
      base: true, // Apply DaisyUI's base styles
      darkTheme: "dark", // Specify the dark theme name
  },
};
