'use client';

import { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  maxLife: number;
  size: number;
  hue: number;
}

export default function CursorParticles() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particles = useRef<Particle[]>([]);
  const mouse = useRef({ x: 0, y: 0 });
  const rafRef = useRef<number>(0);
  const lastSpawn = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Resize canvas to fill window
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    // Track mouse
    const onMouseMove = (e: MouseEvent) => {
      mouse.current = { x: e.clientX, y: e.clientY };

      const now = performance.now();
      if (now - lastSpawn.current < 16) return; // cap spawn rate ~60fps
      lastSpawn.current = now;

      // Spawn 3-5 particles per move event
      const count = Math.floor(Math.random() * 3) + 2;
      for (let i = 0; i < count; i++) {
        const angle = Math.random() * Math.PI * 2;
        const speed = Math.random() * 1.5 + 0.5;
        particles.current.push({
          x: e.clientX + (Math.random() - 0.5) * 8,
          y: e.clientY + (Math.random() - 0.5) * 8,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed - 1.2, // slight upward drift
          life: 1,
          maxLife: Math.random() * 40 + 30, // frames alive
          size: Math.random() * 2.5 + 1,
          hue: Math.random() * 30 - 15, // ±15° hue shift around cyan (185°)
        });
      }

      // Cap particle count
      if (particles.current.length > 300) {
        particles.current = particles.current.slice(-300);
      }
    };

    window.addEventListener('mousemove', onMouseMove);

    // Animation loop
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.current = particles.current.filter((p) => {
        p.life -= 1;
        if (p.life <= 0) return false;

        // Physics
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.04; // subtle gravity
        p.vx *= 0.98; // air resistance

        const alpha = (p.life / p.maxLife) * 0.8;
        const size = p.size * (p.life / p.maxLife);

        // Glow effect: draw larger dim circle first
        ctx.save();
        ctx.globalCompositeOperation = 'screen';

        // Outer glow
        const gradient = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, size * 4);
        gradient.addColorStop(0, `hsla(${185 + p.hue}, 90%, 70%, ${alpha * 0.4})`);
        gradient.addColorStop(1, `hsla(${185 + p.hue}, 90%, 70%, 0)`);
        ctx.beginPath();
        ctx.arc(p.x, p.y, size * 4, 0, Math.PI * 2);
        ctx.fillStyle = gradient;
        ctx.fill();

        // Core dot
        ctx.beginPath();
        ctx.arc(p.x, p.y, size, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${185 + p.hue}, 100%, 80%, ${alpha})`;
        ctx.fill();

        ctx.restore();
        return true;
      });

      rafRef.current = requestAnimationFrame(animate);
    };

    rafRef.current = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', onMouseMove);
      cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9998,
        pointerEvents: 'none',
        mixBlendMode: 'screen',
      }}
    />
  );
}
