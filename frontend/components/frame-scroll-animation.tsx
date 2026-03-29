'use client';

import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';

const VIDEO_URL = 'https://hebbkx1anhila5yf.public.blob.vercel-storage.com/Desk_transforming_into_202603290128-irMNNgLKr6LDSWpWAB7imMk9jHUdT5.mp4';
const SCROLL_DISTANCE = 3000;

const overlayTexts = [
  { text: "Your AI co-pilot for project management", start: 0, end: 0.25 },
  { text: "Watches your dev tools 24/7", start: 0.2, end: 0.45 },
  { text: "Surfaces blockers before they derail sprints", start: 0.4, end: 0.65 },
  { text: "Writes standups, syncs, and status reports", start: 0.6, end: 0.85 },
];

export default function FrameScrollAnimation() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (!isClient) return;

    const video = videoRef.current;
    if (!video) return;

    const handleScroll = () => {
      const scrollY = window.scrollY;
      const progress = Math.min(1, Math.max(0, scrollY / SCROLL_DISTANCE));
      setScrollProgress(progress);

      if (video.duration) {
        video.currentTime = progress * video.duration;
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [isClient]);

  const getTextOpacity = (start: number, end: number) => {
    const fadeIn = 0.05;
    const fadeOut = 0.05;
    
    if (scrollProgress < start) return 0;
    if (scrollProgress < start + fadeIn) return (scrollProgress - start) / fadeIn;
    if (scrollProgress < end - fadeOut) return 1;
    if (scrollProgress < end) return (end - scrollProgress) / fadeOut;
    return 0;
  };

  if (!isClient) {
    return (
      <div className="h-[4000px] bg-[#020817]">
        <div className="sticky top-0 w-full h-screen flex items-center justify-center">
          <div className="text-neutral-400">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative">
      {/* Sticky video container */}
      <div className="sticky top-0 w-full h-screen overflow-hidden bg-[#020817] z-10">
        <video
          ref={videoRef}
          src={VIDEO_URL}
          className="absolute inset-0 w-full h-full object-cover"
          muted
          playsInline
          preload="auto"
        />
        
        {/* Dark overlay for text readability */}
        <div className="absolute inset-0 bg-black/30" />
        
        {/* Overlay texts */}
        <div className="absolute inset-0 flex items-center justify-center">
          {overlayTexts.map((item, index) => (
            <motion.div
              key={index}
              className="absolute text-center px-6"
              style={{ opacity: getTextOpacity(item.start, item.end) }}
            >
              <h2 className="text-4xl md:text-6xl lg:text-7xl font-bold text-white font-[family-name:var(--font-syne)] text-balance max-w-4xl">
                {item.text}
              </h2>
            </motion.div>
          ))}
        </div>

        {/* CTA at the end */}
        <motion.div
          className="absolute bottom-20 left-1/2 -translate-x-1/2"
          style={{ opacity: scrollProgress > 0.85 ? (scrollProgress - 0.85) / 0.15 : 0 }}
        >
          <a
            href="/login"
            className="px-8 py-4 bg-[#22d3ee] text-[#020817] font-semibold rounded-full text-lg
                       shadow-[0_0_30px_rgba(34,211,238,0.5)] hover:shadow-[0_0_50px_rgba(34,211,238,0.7)]
                       transition-all duration-300 hover:scale-105"
          >
            Get early access
          </a>
        </motion.div>

        {/* Scroll indicator */}
        {scrollProgress < 0.1 && (
          <motion.div
            className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
          >
            <span className="text-neutral-400 text-sm">Scroll to explore</span>
            <motion.div
              className="w-6 h-10 border-2 border-neutral-400 rounded-full flex justify-center pt-2"
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <motion.div
                className="w-1.5 h-1.5 bg-[#22d3ee] rounded-full"
                animate={{ y: [0, 16, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            </motion.div>
          </motion.div>
        )}
      </div>
      
      {/* Scroll spacer */}
      <div className="h-[3000px] bg-gradient-to-b from-[#020817] to-[#0a1628]" />
    </div>
  );
}
