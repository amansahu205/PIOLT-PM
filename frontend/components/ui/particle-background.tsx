'use client';

import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export function ParticleBackground() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mountRef.current) return;

    // --- Scene Setup ---
    const scene = new THREE.Scene();

    // Camera
    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    camera.position.z = 50;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mountRef.current.appendChild(renderer.domElement);

    // --- Particles (200 points) ---
    const particleCount = 200;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const velocities: { x: number; y: number; z: number }[] = [];

    for (let i = 0; i < particleCount; i++) {
        // Spread particles across a wide area
        positions[i * 3] = (Math.random() - 0.5) * 200;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 200;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 100;

        velocities.push({
            x: (Math.random() - 0.5) * 0.1,
            y: (Math.random() - 0.5) * 0.1,
            z: (Math.random() - 0.5) * 0.1,
        });
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
        size: 1.5,
        color: 0x22d3ee, // Cyan accent
        transparent: true,
        opacity: 0.6,
        blending: THREE.AdditiveBlending
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    // --- Lines connecting proximity particles ---
    const lineMaterial = new THREE.LineBasicMaterial({
        color: 0x22d3ee,
        transparent: true,
        opacity: 0.15,
        blending: THREE.AdditiveBlending
    });
    
    // Create a dynamic line system 
    // We will update geometry in the animation loop
    const lineGeometry = new THREE.BufferGeometry();
    const lineObj = new THREE.LineSegments(lineGeometry, lineMaterial);
    scene.add(lineObj);


    // --- 5 Wireframe Icospheres ---
    const icosahedronGeo = new THREE.IcosahedronGeometry(Math.random() * 4 + 4, 1);
    const icosahedronMat = new THREE.MeshBasicMaterial({
        color: 0x22d3ee,
        wireframe: true,
        transparent: true,
        opacity: 0.08,
    });

    const icospheres: THREE.Mesh[] = [];
    for (let i = 0; i < 5; i++) {
        const mesh = new THREE.Mesh(icosahedronGeo, icosahedronMat);
        mesh.position.set(
            (Math.random() - 0.5) * 100,
            (Math.random() - 0.5) * 100,
            (Math.random() - 0.5) * 50 - 20
        );
        mesh.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, 0);
        // Random spin rate
        mesh.userData = {
            rx: (Math.random() - 0.5) * 0.005,
            ry: (Math.random() - 0.5) * 0.005
        };
        icospheres.push(mesh);
        scene.add(mesh);
    }

    // --- Animation Loop ---
    let animationFrameId: number;

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      // Animate Particles
      const positionsAttr = particles.geometry.attributes.position;
      const posArray = positionsAttr.array as Float32Array;
      
      let linePositions: number[] = [];

      for (let i = 0; i < particleCount; i++) {
          const i3 = i * 3;
          posArray[i3] += velocities[i].x;
          posArray[i3 + 1] += velocities[i].y;
          posArray[i3 + 2] += velocities[i].z;

          // Boundary wrap
          if (posArray[i3] > 100 || posArray[i3] < -100) velocities[i].x *= -1;
          if (posArray[i3 + 1] > 100 || posArray[i3 + 1] < -100) velocities[i].y *= -1;
          if (posArray[i3 + 2] > 50 || posArray[i3 + 2] < -50) velocities[i].z *= -1;

          // Check connections
          for (let j = i + 1; j < particleCount; j++) {
              const j3 = j * 3;
              const dx = posArray[i3] - posArray[j3];
              const dy = posArray[i3 + 1] - posArray[j3 + 1];
              const dz = posArray[i3 + 2] - posArray[j3 + 2];
              const distSq = dx*dx + dy*dy + dz*dz;

              if (distSq < 400) { // connect if distance < 20
                  linePositions.push(
                      posArray[i3], posArray[i3 + 1], posArray[i3 + 2],
                      posArray[j3], posArray[j3 + 1], posArray[j3 + 2]
                  );
              }
          }
      }
      
      positionsAttr.needsUpdate = true;
      particles.rotation.y += 0.0005;

      // Update Lines
      const linePosFloat = new Float32Array(linePositions);
      lineObj.geometry.setAttribute('position', new THREE.BufferAttribute(linePosFloat, 3));

      // Animate Icospheres
      icospheres.forEach(mesh => {
          mesh.rotation.x += mesh.userData.rx;
          mesh.rotation.y += mesh.userData.ry;
      });

      renderer.render(scene, camera);
    };

    animate();

    // --- Resize handler ---
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
      if (mountRef.current) {
        mountRef.current.removeChild(renderer.domElement);
      }
      geometry.dispose();
      material.dispose();
      lineGeometry.dispose();
      lineMaterial.dispose();
      icosahedronGeo.dispose();
      icosahedronMat.dispose();
      renderer.dispose();
    };
  }, []);

  return (
    <div
      ref={mountRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 0,
        pointerEvents: 'none',
        background: 'transparent',
      }}
    />
  );
}
