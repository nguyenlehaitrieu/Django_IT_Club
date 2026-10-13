
/* ==================================================
   IT MUCE - INTERACTIVE CYBER NETWORK
   Particles + Mouse Repulsion + Network Glow + Ripples
   ================================================== */

(() => {
    "use strict";

    const canvas = document.getElementById("techBackground");
    const glow = document.getElementById("cursorGlow");
    const ring = document.getElementById("cursorRing");

    if (!canvas) {
        console.warn("[IT MUCE] Không tìm thấy #techBackground");
        return;
    }

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    const coarsePointer = window.matchMedia(
        "(pointer: coarse)"
    ).matches;

    let width = 0;
    let height = 0;
    let dpr = 1;
    let particles = [];
    let ripples = [];
    let animationId = null;
    let lastFrame = 0;
    let elapsed = 0;

    const CONFIG = {
        maxParticles: 100,
        minParticles: 35,
        particleArea: 14000,
        connectionDistance: 150,
        mouseRadius: 190,
        mouseForce: 0.075,
        particleSpeed: 0.38,
        frameInterval: 1000 / 40,
        rippleInterval: 90
    };

    const mouse = {
        x: -1000,
        y: -1000,
        previousX: -1000,
        previousY: -1000,
        active: false,
        speed: 0,
        lastRipple: 0
    };

    /* ---------- Canvas setup ---------- */

    function resizeCanvas() {
        dpr = Math.min(window.devicePixelRatio || 1, 2);

        width = window.innerWidth;
        height = window.innerHeight;

        canvas.width = Math.round(width * dpr);
        canvas.height = Math.round(height * dpr);

        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;

        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        createParticles();
        draw(elapsed);
    }

    /* ---------- Create network particles ---------- */

    function createParticles() {
        const count = Math.min(
            CONFIG.maxParticles,
            Math.max(
                CONFIG.minParticles,
                Math.floor(width * height / CONFIG.particleArea)
            )
        );

        particles = Array.from({ length: count }, () => ({
            x: Math.random() * width,
            y: Math.random() * height,

            vx: (Math.random() - 0.5) * CONFIG.particleSpeed,
            vy: (Math.random() - 0.5) * CONFIG.particleSpeed,

            radius: Math.random() * 1.4 + 0.7,
            phase: Math.random() * Math.PI * 2,
            pulseSpeed: 0.7 + Math.random() * 1.5
        }));
    }

    /* ---------- Mouse tracking ---------- */

    if (!coarsePointer && !reducedMotion) {
        window.addEventListener("pointermove", (event) => {
            const x = event.clientX;
            const y = event.clientY;

            if (mouse.active) {
                const dx = x - mouse.previousX;
                const dy = y - mouse.previousY;

                mouse.speed = Math.min(Math.hypot(dx, dy), 45);
            } else {
                mouse.speed = 0;
            }

            mouse.previousX = x;
            mouse.previousY = y;
            mouse.x = x;
            mouse.y = y;
            mouse.active = true;

            if (glow) glow.classList.add("active");
            if (ring) ring.classList.add("active");

            // Tạo gợn sóng theo quãng đường di chuyển
            if (mouse.speed > 5) {
                const now = performance.now();

                if (now - mouse.lastRipple > CONFIG.rippleInterval) {
                    addRipple(x, y);
                    mouse.lastRipple = now;
                }
            }
        }, { passive: true });

        window.addEventListener("pointerout", (event) => {
            if (!event.relatedTarget) {
                mouse.active = false;

                if (glow) glow.classList.remove("active");
                if (ring) ring.classList.remove("active");
            }
        });

        window.addEventListener("blur", () => {
            mouse.active = false;

            if (glow) glow.classList.remove("active");
            if (ring) ring.classList.remove("active");
        });
    }

    /* ---------- Ripple effect ---------- */

    function addRipple(x, y) {
        ripples.push({
            x,
            y,
            radius: 4,
            opacity: 0.65,
            speed: 2.1
        });

        // Giới hạn số gợn sóng để tránh tốn tài nguyên
        if (ripples.length > 10) {
            ripples.shift();
        }
    }

    function drawRipples() {
        for (let i = ripples.length - 1; i >= 0; i--) {
            const ripple = ripples[i];

            ctx.beginPath();
            ctx.arc(
                ripple.x,
                ripple.y,
                ripple.radius,
                0,
                Math.PI * 2
            );

            ctx.strokeStyle =
                `rgba(75, 190, 255, ${ripple.opacity})`;

            ctx.lineWidth = 1.2;
            ctx.stroke();

            // Vòng sóng lan rộng và mờ dần
            ripple.radius += ripple.speed;
            ripple.opacity *= 0.965;

            if (ripple.opacity < 0.025 || ripple.radius > 100) {
                ripples.splice(i, 1);
            }
        }
    }

    /* ---------- Particle physics ---------- */

    function updateParticles() {
        for (const p of particles) {
            p.phase += 0.018 * p.pulseSpeed;

            p.x += p.vx;
            p.y += p.vy;

            if (p.x < 0 || p.x > width) p.vx *= -1;
            if (p.y < 0 || p.y > height) p.vy *= -1;

            if (!mouse.active) continue;

            const dx = p.x - mouse.x;
            const dy = p.y - mouse.y;
            const distance = Math.hypot(dx, dy);

            if (distance > 0 && distance < CONFIG.mouseRadius) {
                const influence = 1 - distance / CONFIG.mouseRadius;
                const force = influence * CONFIG.mouseForce;

                // Đẩy các hạt ra khỏi con trỏ
                p.vx += (dx / distance) * force;
                p.vy += (dy / distance) * force;

                // Giới hạn vận tốc để mạng lưới không bị hỗn loạn
                const maxSpeed = 1.35;
                p.vx = Math.max(-maxSpeed, Math.min(maxSpeed, p.vx));
                p.vy = Math.max(-maxSpeed, Math.min(maxSpeed, p.vy));
            }

            // Lực cản giúp hạt dần trở về tốc độ bình thường
            p.vx *= 0.998;
            p.vy *= 0.998;
        }
    }

    /* ---------- Draw particles ---------- */

    function drawParticles() {
        for (const p of particles) {
            const pulse = 0.65 + Math.sin(p.phase) * 0.25;

            let brightness = pulse;

            if (mouse.active) {
                const distance = Math.hypot(
                    p.x - mouse.x,
                    p.y - mouse.y
                );

                if (distance < CONFIG.mouseRadius) {
                    brightness = Math.min(
                        1,
                        brightness + (1 - distance / CONFIG.mouseRadius) * 0.5
                    );
                }
            }

            // Quầng sáng nhỏ
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius * 4, 0, Math.PI * 2);

            ctx.fillStyle =
                `rgba(45, 140, 255, ${brightness * 0.09})`;

            ctx.fill();

            // Hạt chính
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);

            ctx.fillStyle =
                `rgba(135, 205, 255, ${brightness})`;

            ctx.fill();
        }
    }

    /* ---------- Draw network connections ---------- */

    function drawConnections(timestamp) {
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const a = particles[i];
                const b = particles[j];

                const dx = b.x - a.x;
                const dy = b.y - a.y;
                const distance = Math.hypot(dx, dy);

                if (distance >= CONFIG.connectionDistance) continue;

                const strength = 1 - distance / CONFIG.connectionDistance;

                const midX = (a.x + b.x) / 2;
                const midY = (a.y + b.y) / 2;

                let mouseInfluence = 0;

                if (mouse.active) {
                    const mouseDistance = Math.hypot(
                        midX - mouse.x,
                        midY - mouse.y
                    );

                    mouseInfluence = Math.max(
                        0,
                        1 - mouseDistance / 210
                    );
                }

                // Đường mạng sáng lên khi chuột đến gần
                const opacity =
                    strength * (0.15 + mouseInfluence * 0.7);

                ctx.beginPath();
                ctx.moveTo(a.x, a.y);
                ctx.lineTo(b.x, b.y);

                ctx.strokeStyle =
                    `rgba(65, 155, 255, ${opacity})`;

                ctx.lineWidth = 0.55 + mouseInfluence * 1.15;
                ctx.stroke();

                // Tia sáng chạy trên các đường kết nối
                const progress =
                    ((timestamp * 0.00018 + i * 0.173 + j * 0.071) % 1);

                const sx = a.x + dx * progress;
                const sy = a.y + dy * progress;

                // Ưu tiên tia sáng ở gần chuột
                if (mouseInfluence > 0.15 || strength > 0.72) {
                    const alpha = Math.min(
                        0.95,
                        strength * 0.18 + mouseInfluence * 0.65
                    );

                    ctx.beginPath();
                    ctx.arc(sx, sy, 1.2 + mouseInfluence, 0, Math.PI * 2);

                    ctx.fillStyle =
                        `rgba(140, 225, 255, ${alpha})`;

                    ctx.fill();
                }
            }
        }
    }

    /* ---------- Cursor glow ---------- */

    function updateCursorElements() {
        if (!mouse.active) return;

        if (glow) {
            glow.style.transform =
                `translate3d(${mouse.x - 230}px, ${mouse.y - 230}px, 0)`;
        }

        if (ring) {
            ring.style.transform =
                `translate3d(${mouse.x - 4}px, ${mouse.y - 4}px, 0)`;
        }
    }

    /* ---------- Render frame ---------- */

    function draw(timestamp) {
        ctx.clearRect(0, 0, width, height);

        if (!reducedMotion) {
            updateParticles();
        }

        drawConnections(timestamp);
        drawParticles();

        if (!reducedMotion) {
            drawRipples();
        }

        updateCursorElements();
    }

    function animate(timestamp) {
        if (document.hidden) {
            animationId = null;
            return;
        }

        if (timestamp - lastFrame >= CONFIG.frameInterval) {
            const delta = lastFrame ? timestamp - lastFrame : 16;

            elapsed += Math.min(delta, 40);
            draw(elapsed);
            lastFrame = timestamp;
        }

        animationId = requestAnimationFrame(animate);
    }

    function startAnimation() {
        if (reducedMotion || document.hidden || animationId !== null) {
            return;
        }

        animationId = requestAnimationFrame(animate);
    }

    function stopAnimation() {
        if (animationId !== null) {
            cancelAnimationFrame(animationId);
            animationId = null;
        }
    }

    /* ---------- Start ---------- */

    resizeCanvas();

    if (!reducedMotion) {
        startAnimation();
    }

    window.addEventListener("resize", resizeCanvas);

    document.addEventListener("visibilitychange", () => {
        if (document.hidden) {
            stopAnimation();
        } else {
            draw(elapsed);
            startAnimation();
        }
    });
})();
