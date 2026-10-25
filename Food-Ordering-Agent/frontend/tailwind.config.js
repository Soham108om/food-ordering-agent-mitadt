/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        cream: {
          DEFAULT: '#FBF9F5',
          dark: '#F5F0E6',
        },
        sand: {
          DEFAULT: '#F2ECE1',
          light: '#F8F5EE',
          dark: '#E8DFD1',
        },
        espresso: {
          DEFAULT: '#261E1A',
          muted: '#544741',
          light: '#7A6B62',
        },
        terracotta: {
          DEFAULT: '#D9531E',
          hover: '#C24415',
          light: '#FDF3EE',
          border: '#F2CBB8',
        },
        olive: {
          DEFAULT: '#4E6B38',
          light: '#F1F5EC',
          border: '#C3D4B5',
        },
        warmamber: {
          DEFAULT: '#C48421',
          light: '#FBF5EB',
          border: '#EED6AE',
        },
        warmred: {
          DEFAULT: '#B93829',
          light: '#FDF2F0',
          border: '#F2BEB8',
        },
        // Legacy color mapping aliases to maintain full component compatibility
        swiggy: {
          orange: '#D9531E',
          dark: '#FBF9F5',
          card: '#FFFFFF',
          accent: '#4E6B38',
        }
      },
      boxShadow: {
        'warm-sm': '0 2px 8px -2px rgba(42, 33, 29, 0.05), 0 1px 4px -1px rgba(42, 33, 29, 0.03)',
        'warm-md': '0 4px 16px -4px rgba(42, 33, 29, 0.08), 0 2px 6px -2px rgba(42, 33, 29, 0.04)',
        'warm-lg': '0 12px 32px -8px rgba(42, 33, 29, 0.12), 0 4px 12px -4px rgba(42, 33, 29, 0.06)',
      },
      fontFamily: {
        serif: ['Georgia', 'Cambria', '"Times New Roman"', 'Times', 'serif'],
        sans: ['system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
};
