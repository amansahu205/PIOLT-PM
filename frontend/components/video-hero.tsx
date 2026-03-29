'use client'

import { useEffect, useRef, useState } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'

const VIDEO_SCROLL_RANGE = 2000 // px of scroll to play the full video

interface ScrollTextItem {
  scrollStart: number
  scrollEnd: number
  text: string
  isCta?: boolean
}

const SCROLL_TEXTS: ScrollTextItem[] = [
  { scrollStart: 0, scrollEnd: 300, text: 'One PM. Five engineers.\nZero standups.' },
  { scrollStart: 400, scrollEnd: 700, text: 'PilotPM watches your tools 24/7' },
  { scrollStart: 800, scrollEnd: 1100, text: 'So you don\'t have to' },
  { scrollStart: 1200, scrollEnd: VIDEO_SCROLL_RANGE, text: 'Try PilotPM →', isCta: true },
]

function useScrollY() {
  const [scrollY, setScrollY] = useState(0)

  useEffect(() => {
    let rafId: number
    const onScroll = () => {
      rafId = requestAnimationFrame(() => {
        setScrollY(window.scrollY)
      })
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      window.removeEventListener('scroll', onScroll)
      if (rafId) cancelAnimationFrame(rafId)
    }
  }, [])

  return scrollY
}

function getOpacity(scrollY: number, start: number, end: number): number {
  const fadeIn = 60
  const fadeOut = 60

  if (scrollY < start - fadeIn) return 0
  if (scrollY < start) return (scrollY - (start - fadeIn)) / fadeIn
  if (scrollY < end - fadeOut) return 1
  if (scrollY < end) return 1 - (scrollY - (end - fadeOut)) / fadeOut
  return 0
}

export default function VideoHero() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [videoLoaded, setVideoLoaded] = useState(false)
  const scrollY = useScrollY()

  // Scrub video based on scroll
  useEffect(() => {
    const video = videoRef.current
    if (!video || !videoLoaded) return
    const duration = video.duration
    if (!duration) return
    const progress = Math.min(scrollY / VIDEO_SCROLL_RANGE, 1)
    video.currentTime = progress * duration
  }, [scrollY, videoLoaded])

  return (
    <section
      className="relative"
      style={{ height: `calc(100vh + ${VIDEO_SCROLL_RANGE}px)` }}
      aria-label="PilotPM hero"
    >
      {/* Sticky video container */}
      <div className="sticky top-0 h-screen w-full overflow-hidden">
        {/* Video */}
        <video
          ref={videoRef}
          className="absolute inset-0 h-full w-full object-cover"
          src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/Desk_transforming_into_202603290128-irMNNgLKr6LDSWpWAB7imMk9jHUdT5.mp4"
          muted
          playsInline
          preload="auto"
          onLoadedMetadata={() => setVideoLoaded(true)}
          onError={() => setVideoLoaded(false)}
          aria-hidden="true"
        />

        {/* Dark overlay for readability */}
        <div className="absolute inset-0 bg-black/40" />

        {/* Scroll text overlays */}
        {SCROLL_TEXTS.map((item) => {
          const opacity = getOpacity(scrollY, item.scrollStart, item.scrollEnd)

          if (item.isCta) {
            return (
              <div
                key={item.text}
                className="absolute inset-0 flex items-center justify-center"
                style={{ opacity, pointerEvents: opacity > 0.1 ? 'auto' : 'none' }}
              >
                <a
                  href="#features"
                  className="group relative inline-flex items-center gap-2 rounded-full border border-cyan-400/60 bg-cyan-400/10 px-8 py-4 text-xl font-semibold text-cyan-300 transition-all duration-300 hover:bg-cyan-400/20"
                  style={{
                    fontFamily: 'var(--font-syne)',
                    boxShadow: `0 0 32px 8px rgba(34,211,238,0.25), 0 0 64px 16px rgba(34,211,238,0.12)`,
                    textShadow: '0 0 20px rgba(34,211,238,0.8)',
                  }}
                >
                  {item.text}
                </a>
              </div>
            )
          }

          return (
            <div
              key={item.text}
              className="absolute inset-0 flex items-center justify-center px-6 text-center"
              style={{ opacity, pointerEvents: 'none' }}
            >
              <h1
                className="max-w-4xl whitespace-pre-line text-5xl font-bold leading-tight text-white sm:text-6xl lg:text-7xl"
                style={{
                  fontFamily: 'var(--font-syne)',
                  textShadow: '0 2px 40px rgba(0,0,0,0.8)',
                }}
              >
                {item.text}
              </h1>
            </div>
          )
        })}

        {/* Scroll indicator — only visible at top */}
        <div
          className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
          style={{ opacity: Math.max(0, 1 - scrollY / 150), pointerEvents: 'none' }}
          aria-hidden="true"
        >
          <span className="text-xs uppercase tracking-widest text-white/50" style={{ fontFamily: 'var(--font-syne)' }}>
            Scroll
          </span>
          <div className="h-10 w-px bg-white/20" />
        </div>
      </div>
    </section>
  )
}
