import type { Metadata } from 'next'
import { Inter, Syne } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import CursorParticles from '@/components/cursor-particles'
import { ParticleBackground } from '@/components/ui/particle-background'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
})

const syne = Syne({
  subsets: ['latin'],
  variable: '--font-syne',
  weight: ['400', '500', '600', '700', '800'],
})

export const metadata: Metadata = {
  metadataBase: new URL('https://www.iloveyhacks.biz'),
  title: 'PilotPM — One PM. Five engineers. Zero standups.',
  description:
    'PilotPM watches your tools 24/7 so you don\'t have to. AI-powered project management that keeps your team in sync without meetings.',
  generator: 'v0.app',
  icons: {
    icon: '/logo.png',
    apple: '/logo.png',
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${syne.variable} font-sans antialiased bg-[#020817] text-white`}>
        <ParticleBackground />
        <CursorParticles />
        {children}
        <Analytics />
      </body>
    </html>
  )
}
