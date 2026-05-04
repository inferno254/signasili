import type { Metadata } from 'next';
import { Noto_Sans } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/providers';
import { Header } from '@/components/layout/Header';
import { Toaster } from 'react-hot-toast';

const notoSans = Noto_Sans({
  subsets: ['latin'],
  variable: '--font-noto-sans',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'SignAsili - Kenyan Sign Language Education',
  description: 'Learn Kenyan Sign Language (KSL) with AI-powered interactive lessons. Accessible education for the deaf community.',
  keywords: ['KSL', 'Kenyan Sign Language', 'deaf education', 'sign language learning'],
  authors: [{ name: 'SignAsili Team' }],
  openGraph: {
    title: 'SignAsili - Kenyan Sign Language Education',
    description: 'Learn Kenyan Sign Language with interactive AI-powered lessons',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={notoSans.variable}>
      <body className="min-h-screen bg-gray-50 font-sans antialiased">
        <Providers>
          <Header />
          <main className="flex-1">
            {children}
          </main>
          <Toaster position="top-right" />
        </Providers>
      </body>
    </html>
  );
}
