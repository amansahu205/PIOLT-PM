'use client'

import { useEffect, useState } from 'react'
import Image from 'next/image'

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <header
      className="fixed top-0 z-50 w-full transition-all duration-500"
      style={{
        backgroundColor: scrolled ? 'rgba(2, 8, 23, 0.85)' : 'transparent',
        backdropFilter: scrolled ? 'blur(20px)' : 'none',
        borderBottom: scrolled ? '1px solid rgba(30, 45, 69, 0.8)' : '1px solid transparent',
      }}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        {/* Logo */}
        <a
          href="/"
          className="flex items-center gap-2.5 text-lg font-bold text-white"
          style={{ fontFamily: 'var(--font-syne)' }}
        >
          <Image
            src="/logo.png"
            alt="PilotPM logo"
            width={32}
            height={32}
            className="object-contain"
            priority
          />
          PilotPM
        </a>

        {/* Nav links */}
        <nav className="hidden items-center gap-7 md:flex" aria-label="Main navigation">
          {['Features', 'Pricing', 'Docs', 'Changelog'].map((link) => (
            <a
              key={link}
              href="#"
              className="text-sm text-white/50 transition-colors hover:text-white"
              style={{ fontFamily: 'var(--font-syne)' }}
            >
              {link}
            </a>
          ))}
        </nav>

        {/* CTA */}
        <div className="flex items-center gap-3">
          <a
            href="#"
            className="hidden text-sm text-white/50 transition-colors hover:text-white md:block"
            style={{ fontFamily: 'var(--font-syne)' }}
          >
            Sign in
          </a>
          <a
            href="#"
            className="rounded-full bg-cyan-400 px-5 py-2 text-sm font-semibold text-[#020817] transition-all hover:bg-cyan-300"
            style={{
              fontFamily: 'var(--font-syne)',
              boxShadow: '0 0 16px 2px rgba(34,211,238,0.25)',
            }}
          >
            Get early access
          </a>
        </div>
      </div>
    </header>
  )
}
