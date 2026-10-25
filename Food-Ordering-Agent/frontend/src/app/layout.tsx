import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Food Ordering Agent — Complete Jury Demo',
  description: 'Real Food Ordering Agent powered by Gemini + LangGraph + Swiggy MCP',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-swiggy-dark text-white min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
