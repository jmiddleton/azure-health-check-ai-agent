"use client";

import { useEffect, useRef } from "react";

export function DotBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationId: number;
    let time = 0;

    class Orb {
      x: number;
      y: number;
      vx: number;
      vy: number;
      radius: number;
      baseRadius: number;
      color: string;
      pulseSpeed: number;
      pulseOffset: number;

      constructor(canvasWidth: number, canvasHeight: number, index: number) {
        this.x = Math.random() * canvasWidth;
        this.y = Math.random() * canvasHeight;
        this.vx = (Math.random() - 0.5) * 0.3;
        this.vy = (Math.random() - 0.5) * 0.3;
        this.baseRadius = 80 + Math.random() * 120;
        this.radius = this.baseRadius;
        this.pulseSpeed = 0.002 + Math.random() * 0.003;
        this.pulseOffset = Math.random() * Math.PI * 2;
        
        // Create color variations (blue to purple gradient)
        const hue = 220 + Math.random() * 40; // Blue to purple range
        this.color = `hsla(${hue}, 70%, 60%, 0.15)`;
      }

      update(canvasWidth: number, canvasHeight: number, deltaTime: number) {
        this.x += this.vx;
        this.y += this.vy;

        // Bounce off edges
        if (this.x < -this.radius || this.x > canvasWidth + this.radius) this.vx *= -1;
        if (this.y < -this.radius || this.y > canvasHeight + this.radius) this.vy *= -1;

        // Keep within bounds
        this.x = Math.max(-this.radius, Math.min(canvasWidth + this.radius, this.x));
        this.y = Math.max(-this.radius, Math.min(canvasHeight + this.radius, this.y));

        // Pulsing effect
        this.radius = this.baseRadius + Math.sin(time * this.pulseSpeed + this.pulseOffset) * 20;
      }

      draw(ctx: CanvasRenderingContext2D, themeIsDark: boolean) {
        const baseOpacity = themeIsDark ? 0.15 : 0.08;
        const midOpacity = themeIsDark ? 0.08 : 0.04;
        
        const gradient = ctx.createRadialGradient(
          this.x, this.y, 0,
          this.x, this.y, this.radius
        );
        gradient.addColorStop(0, this.color.replace('0.15', baseOpacity.toString()));
        gradient.addColorStop(0.5, this.color.replace('0.15', midOpacity.toString()));
        gradient.addColorStop(1, this.color.replace('0.15', '0'));

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    class Node {
      x: number;
      y: number;
      vx: number;
      vy: number;
      size: number;

      constructor(canvasWidth: number, canvasHeight: number) {
        this.x = Math.random() * canvasWidth;
        this.y = Math.random() * canvasHeight;
        this.vx = (Math.random() - 0.5) * 0.2;
        this.vy = (Math.random() - 0.5) * 0.2;
        this.size = 2 + Math.random() * 2;
      }

      update(canvasWidth: number, canvasHeight: number) {
        this.x += this.vx;
        this.y += this.vy;

        if (this.x < 0 || this.x > canvasWidth) this.vx *= -1;
        if (this.y < 0 || this.y > canvasHeight) this.vy *= -1;
        this.x = Math.max(0, Math.min(canvasWidth, this.x));
        this.y = Math.max(0, Math.min(canvasHeight, this.y));
      }

      draw(ctx: CanvasRenderingContext2D, themeIsDark: boolean) {
        const opacity = themeIsDark ? 0.4 : 0.2;
        ctx.fillStyle = `rgba(147, 197, 253, ${opacity})`;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    let orbs: Orb[] = [];
    let nodes: Node[] = [];
    let lastTime = performance.now();

    const resizeCanvas = () => {
      if (!canvas) return;
      const dpr = window.devicePixelRatio || 1;
      const width = window.innerWidth;
      const height = window.innerHeight;

      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.scale(dpr, dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
    };

    const init = () => {
      resizeCanvas();
      const width = window.innerWidth;
      const height = window.innerHeight;
      
      // Create 4-6 large gradient orbs
      orbs = Array.from({ length: 5 }, (_, i) => new Orb(width, height, i));
      
      // Create mesh nodes
      nodes = Array.from({ length: 30 }, () => new Node(width, height));
    };

    const animate = (currentTime: number) => {
      if (!canvas || !ctx) return;

      const deltaTime = currentTime - lastTime;
      lastTime = currentTime;
      time += deltaTime * 0.01;

      const width = window.innerWidth;
      const height = window.innerHeight;

      // Check theme once per frame
      const themeIsDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

      // Clear with fade effect for trails
      const fadeOpacity = themeIsDark ? 0.1 : 0.05;
      ctx.fillStyle = `rgba(0, 0, 0, ${fadeOpacity})`;
      ctx.fillRect(0, 0, width, height);

      // Update and draw orbs
      orbs.forEach(orb => {
        orb.update(width, height, deltaTime);
        orb.draw(ctx, themeIsDark);
      });

      // Update and draw nodes
      nodes.forEach(node => {
        node.update(width, height);
        node.draw(ctx, themeIsDark);
      });

      // Draw mesh connections
      const baseOpacity = themeIsDark ? 0.1 : 0.05;
      ctx.strokeStyle = `rgba(147, 197, 253, ${baseOpacity})`;
      ctx.lineWidth = 0.5;
      
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i];
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 200) {
            const maxOpacity = themeIsDark ? 0.15 : 0.08;
            const opacity = maxOpacity * (1 - dist / 200);
            ctx.strokeStyle = `rgba(147, 197, 253, ${opacity})`;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      animationId = requestAnimationFrame(animate);
    };

    init();
    animationId = requestAnimationFrame(animate);

    const handleResize = () => {
      resizeCanvas();
      const width = window.innerWidth;
      const height = window.innerHeight;
      
      // Recreate orbs and nodes on significant resize
      if (orbs.length === 0 || nodes.length === 0) {
        orbs = Array.from({ length: 5 }, (_, i) => new Orb(width, height, i));
        nodes = Array.from({ length: 30 }, () => new Node(width, height));
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, []);

  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />;
}

