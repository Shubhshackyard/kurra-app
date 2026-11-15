import type { Metadata } from "next";
import { Inter, Noto_Sans_Devanagari } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const notoDevanagari = Noto_Sans_Devanagari({
  subsets: ["devanagari"],
  variable: "--font-noto-devanagari",
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "एसडीएम कुर्रा डैशबोर्ड — SDM Kurra Dashboard | धारा 116 / नियम 109(5)",
  description: "उत्तर प्रदेश राजस्व संहिता 2006 धारा 116 व नियमावली नियम 109(5) हेतु बुद्धिमान स्थानीय भू-सर्वेक्षण व कुर्रा विभाजन प्रणाली",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="hi" className="h-full">
      <body className={`${inter.variable} ${notoDevanagari.variable} font-sans h-full bg-slate-50 text-slate-900 antialiased selection:bg-indigo-100 selection:text-indigo-900`}>
        {children}
      </body>
    </html>
  );
}
