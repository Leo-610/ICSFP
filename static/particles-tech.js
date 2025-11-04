/**
 * 动态粒子背景系统
 * 科技感十足的粒子连线效果
 */

class ParticlesBackground {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error(`Canvas with id "${canvasId}" not found`);
            return;
        }
        
        this.ctx = this.canvas.getContext('2d');
        
        // 配置参数
        this.config = {
            particleCount: options.particleCount || 80,
            particleColor: options.particleColor || 'rgba(0, 102, 255, 0.8)',
            lineColor: options.lineColor || 'rgba(0, 196, 140, 0.2)',
            particleRadius: options.particleRadius || 2,
            lineDistance: options.lineDistance || 150,
            particleSpeed: options.particleSpeed || 0.5,
            mouseRadius: options.mouseRadius || 150,
            glowEffect: options.glowEffect !== false
        };
        
        this.particles = [];
        this.mouse = { x: null, y: null, radius: this.config.mouseRadius };
        this.animationId = null;
        
        this.init();
    }
    
    init() {
        this.resizeCanvas();
        this.createParticles();
        this.setupEventListeners();
        this.animate();
    }
    
    resizeCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    createParticles() {
        this.particles = [];
        for (let i = 0; i < this.config.particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * this.config.particleSpeed,
                vy: (Math.random() - 0.5) * this.config.particleSpeed,
                radius: this.config.particleRadius
            });
        }
    }
    
    setupEventListeners() {
        window.addEventListener('resize', () => {
            this.resizeCanvas();
            this.createParticles();
        });
        
        this.canvas.addEventListener('mousemove', (e) => {
            this.mouse.x = e.x;
            this.mouse.y = e.y;
        });
        
        this.canvas.addEventListener('mouseleave', () => {
            this.mouse.x = null;
            this.mouse.y = null;
        });
    }
    
    drawParticle(particle) {
        this.ctx.beginPath();
        this.ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
        this.ctx.fillStyle = this.config.particleColor;
        
        if (this.config.glowEffect) {
            this.ctx.shadowBlur = 10;
            this.ctx.shadowColor = this.config.particleColor;
        }
        
        this.ctx.fill();
        this.ctx.shadowBlur = 0;
    }
    
    drawLine(p1, p2, distance) {
        const opacity = 1 - distance / this.config.lineDistance;
        this.ctx.strokeStyle = this.config.lineColor.replace(/[\d.]+\)$/, `${opacity})`);
        this.ctx.lineWidth = 1;
        this.ctx.beginPath();
        this.ctx.moveTo(p1.x, p1.y);
        this.ctx.lineTo(p2.x, p2.y);
        this.ctx.stroke();
    }
    
    connectParticles() {
        for (let i = 0; i < this.particles.length; i++) {
            for (let j = i + 1; j < this.particles.length; j++) {
                const dx = this.particles[i].x - this.particles[j].x;
                const dy = this.particles[i].y - this.particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < this.config.lineDistance) {
                    this.drawLine(this.particles[i], this.particles[j], distance);
                }
            }
        }
    }
    
    connectToMouse(particle) {
        const dx = this.mouse.x - particle.x;
        const dy = this.mouse.y - particle.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance < this.mouse.radius) {
            this.ctx.strokeStyle = `rgba(0, 102, 255, ${1 - distance / this.mouse.radius})`;
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            this.ctx.moveTo(particle.x, particle.y);
            this.ctx.lineTo(this.mouse.x, this.mouse.y);
            this.ctx.stroke();
            
            // 鼠标吸引效果
            particle.x += dx * 0.01;
            particle.y += dy * 0.01;
        }
    }
    
    updateParticle(particle) {
        particle.x += particle.vx;
        particle.y += particle.vy;
        
        // 边界反弹
        if (particle.x < 0 || particle.x > this.canvas.width) {
            particle.vx = -particle.vx;
        }
        if (particle.y < 0 || particle.y > this.canvas.height) {
            particle.vy = -particle.vy;
        }
        
        // 限制在画布内
        particle.x = Math.max(0, Math.min(this.canvas.width, particle.x));
        particle.y = Math.max(0, Math.min(this.canvas.height, particle.y));
    }
    
    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 更新和绘制粒子
        this.particles.forEach(particle => {
            this.updateParticle(particle);
            this.drawParticle(particle);
            
            // 鼠标交互
            if (this.mouse.x !== null && this.mouse.y !== null) {
                this.connectToMouse(particle);
            }
        });
        
        // 连接粒子
        this.connectParticles();
        
        this.animationId = requestAnimationFrame(() => this.animate());
    }
    
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        window.removeEventListener('resize', this.resizeCanvas);
    }
}

// 数据流动画效果
class DataFlowAnimation {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;
        
        this.config = {
            lineCount: options.lineCount || 5,
            speed: options.speed || 2,
            color: options.color || 'rgba(0, 196, 140, 0.3)'
        };
        
        this.createDataFlows();
    }
    
    createDataFlows() {
        for (let i = 0; i < this.config.lineCount; i++) {
            const flow = document.createElement('div');
            flow.className = 'data-flow';
            flow.style.cssText = `
                position: absolute;
                width: 100%;
                height: 2px;
                background: linear-gradient(90deg, transparent, ${this.config.color}, transparent);
                left: 0;
                top: ${Math.random() * 100}%;
                animation: flowMove ${5 + Math.random() * 5}s linear infinite;
                animation-delay: ${Math.random() * 2}s;
                opacity: ${0.3 + Math.random() * 0.4};
            `;
            this.container.appendChild(flow);
        }
        
        // 添加动画关键帧
        if (!document.getElementById('dataFlowStyles')) {
            const style = document.createElement('style');
            style.id = 'dataFlowStyles';
            style.textContent = `
                @keyframes flowMove {
                    from { transform: translateX(-100%); }
                    to { transform: translateX(200%); }
                }
            `;
            document.head.appendChild(style);
        }
    }
}

// 霓虹边框效果
class NeonBorder {
    static apply(element, color = '#0066FF') {
        element.style.position = 'relative';
        element.style.overflow = 'visible';
        
        const neonStyle = `
            box-shadow: 
                0 0 5px ${color}40,
                0 0 10px ${color}30,
                0 0 15px ${color}20,
                0 0 20px ${color}10,
                inset 0 0 5px ${color}20;
            border: 1px solid ${color}60;
            transition: all 0.3s ease;
        `;
        
        element.style.cssText += neonStyle;
        
        // 悬停增强效果
        element.addEventListener('mouseenter', () => {
            element.style.cssText += `
                box-shadow: 
                    0 0 10px ${color}60,
                    0 0 20px ${color}40,
                    0 0 30px ${color}30,
                    0 0 40px ${color}20,
                    inset 0 0 10px ${color}30;
                border-color: ${color};
                transform: translateY(-2px);
            `;
        });
        
        element.addEventListener('mouseleave', () => {
            element.style.cssText += neonStyle + 'transform: translateY(0);';
        });
    }
}

// 渐变动画效果
class GradientAnimation {
    static apply(element, colors = ['#0066FF', '#00C48C', '#FF5757']) {
        const gradient = colors.join(', ');
        element.style.background = `linear-gradient(270deg, ${gradient})`;
        element.style.backgroundSize = '400% 400%';
        element.style.animation = 'gradientShift 15s ease infinite';
        
        if (!document.getElementById('gradientStyles')) {
            const style = document.createElement('style');
            style.id = 'gradientStyles';
            style.textContent = `
                @keyframes gradientShift {
                    0% { background-position: 0% 50%; }
                    50% { background-position: 100% 50%; }
                    100% { background-position: 0% 50%; }
                }
            `;
            document.head.appendChild(style);
        }
    }
}

// 3D卡片效果
class Card3D {
    static apply(element) {
        element.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease';
        element.style.transformStyle = 'preserve-3d';
        
        element.addEventListener('mousemove', (e) => {
            const rect = element.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;
            
            element.style.transform = `
                perspective(1000px)
                rotateX(${rotateX}deg)
                rotateY(${rotateY}deg)
                translateZ(10px)
            `;
            
            element.style.boxShadow = `
                ${-rotateY * 2}px ${rotateX * 2}px 40px rgba(0, 102, 255, 0.3),
                0 0 20px rgba(0, 196, 140, 0.2)
            `;
        });
        
        element.addEventListener('mouseleave', () => {
            element.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
            element.style.boxShadow = '';
        });
    }
}

// 打字机效果
class TypewriterEffect {
    static async type(element, text, speed = 50) {
        element.textContent = '';
        for (let i = 0; i < text.length; i++) {
            element.textContent += text[i];
            await new Promise(resolve => setTimeout(resolve, speed));
        }
    }
}

// 数字滚动效果
class CountUp {
    static animate(element, start, end, duration = 2000) {
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                current = end;
                clearInterval(timer);
            }
            element.textContent = Math.round(current);
        }, 16);
    }
}

// 脉冲动画
class PulseEffect {
    static apply(element, color = '#0066FF') {
        if (!document.getElementById('pulseStyles')) {
            const style = document.createElement('style');
            style.id = 'pulseStyles';
            style.textContent = `
                @keyframes pulse {
                    0%, 100% {
                        box-shadow: 0 0 0 0 ${color}80;
                    }
                    50% {
                        box-shadow: 0 0 0 20px ${color}00;
                    }
                }
                .pulse-animation {
                    animation: pulse 2s infinite;
                }
            `;
            document.head.appendChild(style);
        }
        
        element.classList.add('pulse-animation');
    }
}

// 玻璃态效果
class GlassmorphismEffect {
    static apply(element, blur = 10, opacity = 0.1) {
        element.style.cssText += `
            background: rgba(255, 255, 255, ${opacity});
            backdrop-filter: blur(${blur}px) saturate(180%);
            -webkit-backdrop-filter: blur(${blur}px) saturate(180%);
            border: 1px solid rgba(255, 255, 255, 0.18);
        `;
    }
}

// 悬浮动画
class FloatingAnimation {
    static apply(element, distance = 10, duration = 3) {
        element.style.animation = `floating ${duration}s ease-in-out infinite`;
        
        if (!document.getElementById('floatingStyles')) {
            const style = document.createElement('style');
            style.id = 'floatingStyles';
            style.textContent = `
                @keyframes floating {
                    0%, 100% {
                        transform: translateY(0px);
                    }
                    50% {
                        transform: translateY(-${distance}px);
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }
}

// 鼠标轨迹特效
class MouseTrailEffect {
    constructor(options = {}) {
        this.config = {
            trailLength: options.trailLength || 20,
            particleSize: options.particleSize || 6,
            particleColor: options.particleColor || '#0066FF',
            fadeSpeed: options.fadeSpeed || 0.95,
            glowEffect: options.glowEffect !== false,
            trailType: options.trailType || 'particles' // 'particles', 'line', 'glow'
        };
        
        this.particles = [];
        this.canvas = null;
        this.ctx = null;
        this.mouse = { x: 0, y: 0 };
        this.animationId = null;
        
        this.init();
    }
    
    init() {
        // 创建Canvas
        this.canvas = document.createElement('canvas');
        this.canvas.id = 'mouseTrailCanvas';
        this.canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9999;
        `;
        document.body.appendChild(this.canvas);
        
        this.ctx = this.canvas.getContext('2d');
        this.resizeCanvas();
        
        // 事件监听
        window.addEventListener('resize', () => this.resizeCanvas());
        window.addEventListener('mousemove', (e) => this.onMouseMove(e));
        
        // 开始动画
        this.animate();
    }
    
    resizeCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    onMouseMove(e) {
        this.mouse.x = e.clientX;
        this.mouse.y = e.clientY;
        
        // 添加新粒子
        this.addParticle(e.clientX, e.clientY);
    }
    
    addParticle(x, y) {
        // 控制粒子数量
        if (this.particles.length > this.config.trailLength) {
            this.particles.shift();
        }
        
        const particle = {
            x: x,
            y: y,
            size: this.config.particleSize,
            alpha: 1,
            vx: (Math.random() - 0.5) * 2,
            vy: (Math.random() - 0.5) * 2,
            life: 1,
            color: this.config.particleColor,
            rotation: Math.random() * Math.PI * 2,
            rotationSpeed: (Math.random() - 0.5) * 0.1
        };
        
        this.particles.push(particle);
    }
    
    updateParticles() {
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            
            // 更新位置
            p.x += p.vx;
            p.y += p.vy;
            
            // 更新透明度
            p.alpha *= this.config.fadeSpeed;
            p.life *= this.config.fadeSpeed;
            
            // 更新旋转
            p.rotation += p.rotationSpeed;
            
            // 减小尺寸
            p.size *= 0.98;
            
            // 移除消失的粒子
            if (p.alpha < 0.01 || p.size < 0.5) {
                this.particles.splice(i, 1);
            }
        }
    }
    
    drawParticles() {
        this.particles.forEach((p, index) => {
            this.ctx.save();
            
            if (this.config.trailType === 'particles') {
                // 粒子效果
                this.ctx.globalAlpha = p.alpha;
                this.ctx.translate(p.x, p.y);
                this.ctx.rotate(p.rotation);
                
                // 发光效果
                if (this.config.glowEffect) {
                    this.ctx.shadowBlur = 15;
                    this.ctx.shadowColor = p.color;
                }
                
                // 绘制星形粒子
                this.ctx.beginPath();
                for (let i = 0; i < 5; i++) {
                    const angle = (Math.PI * 2 * i) / 5;
                    const x = Math.cos(angle) * p.size;
                    const y = Math.sin(angle) * p.size;
                    if (i === 0) {
                        this.ctx.moveTo(x, y);
                    } else {
                        this.ctx.lineTo(x, y);
                    }
                }
                this.ctx.closePath();
                
                // 渐变填充
                const gradient = this.ctx.createRadialGradient(0, 0, 0, 0, 0, p.size);
                gradient.addColorStop(0, p.color);
                gradient.addColorStop(1, 'transparent');
                this.ctx.fillStyle = gradient;
                this.ctx.fill();
                
            } else if (this.config.trailType === 'line') {
                // 线条轨迹
                if (index > 0) {
                    const prevP = this.particles[index - 1];
                    this.ctx.globalAlpha = p.alpha * 0.5;
                    this.ctx.strokeStyle = p.color;
                    this.ctx.lineWidth = p.size;
                    this.ctx.lineCap = 'round';
                    
                    if (this.config.glowEffect) {
                        this.ctx.shadowBlur = 10;
                        this.ctx.shadowColor = p.color;
                    }
                    
                    this.ctx.beginPath();
                    this.ctx.moveTo(prevP.x, prevP.y);
                    this.ctx.lineTo(p.x, p.y);
                    this.ctx.stroke();
                }
            } else if (this.config.trailType === 'glow') {
                // 光晕效果
                this.ctx.globalAlpha = p.alpha * 0.3;
                const gradient = this.ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size * 3);
                gradient.addColorStop(0, p.color);
                gradient.addColorStop(1, 'transparent');
                this.ctx.fillStyle = gradient;
                this.ctx.fillRect(p.x - p.size * 3, p.y - p.size * 3, p.size * 6, p.size * 6);
            }
            
            this.ctx.restore();
        });
    }
    
    animate() {
        // 清空画布
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 更新和绘制粒子
        this.updateParticles();
        this.drawParticles();
        
        this.animationId = requestAnimationFrame(() => this.animate());
    }
    
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
        window.removeEventListener('resize', this.resizeCanvas);
        window.removeEventListener('mousemove', this.onMouseMove);
    }
    
    changeStyle(type) {
        this.config.trailType = type;
    }
    
    changeColor(color) {
        this.config.particleColor = color;
    }
}

// 鼠标点击涟漪特效
class MouseClickRipple {
    constructor(options = {}) {
        this.config = {
            rippleColor: options.rippleColor || 'rgba(0, 102, 255, 0.6)',
            maxRadius: options.maxRadius || 100,
            duration: options.duration || 1000,
            lineWidth: options.lineWidth || 2
        };
        
        this.ripples = [];
        this.canvas = null;
        this.ctx = null;
        this.animationId = null;
        
        this.init();
    }
    
    init() {
        // 创建Canvas
        this.canvas = document.createElement('canvas');
        this.canvas.id = 'mouseRippleCanvas';
        this.canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9998;
        `;
        document.body.appendChild(this.canvas);
        
        this.ctx = this.canvas.getContext('2d');
        this.resizeCanvas();
        
        // 事件监听
        window.addEventListener('resize', () => this.resizeCanvas());
        window.addEventListener('click', (e) => this.onClick(e));
        
        // 开始动画
        this.animate();
    }
    
    resizeCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    onClick(e) {
        this.addRipple(e.clientX, e.clientY);
    }
    
    addRipple(x, y) {
        const ripple = {
            x: x,
            y: y,
            radius: 0,
            alpha: 1,
            startTime: Date.now()
        };
        this.ripples.push(ripple);
    }
    
    updateRipples() {
        const now = Date.now();
        
        for (let i = this.ripples.length - 1; i >= 0; i--) {
            const ripple = this.ripples[i];
            const elapsed = now - ripple.startTime;
            const progress = elapsed / this.config.duration;
            
            if (progress >= 1) {
                this.ripples.splice(i, 1);
                continue;
            }
            
            // 更新半径和透明度
            ripple.radius = this.config.maxRadius * progress;
            ripple.alpha = 1 - progress;
        }
    }
    
    drawRipples() {
        this.ripples.forEach(ripple => {
            this.ctx.save();
            this.ctx.globalAlpha = ripple.alpha;
            this.ctx.strokeStyle = this.config.rippleColor;
            this.ctx.lineWidth = this.config.lineWidth;
            
            // 绘制外圈
            this.ctx.beginPath();
            this.ctx.arc(ripple.x, ripple.y, ripple.radius, 0, Math.PI * 2);
            this.ctx.stroke();
            
            // 绘制内圈（更小更亮）
            this.ctx.globalAlpha = ripple.alpha * 0.5;
            this.ctx.beginPath();
            this.ctx.arc(ripple.x, ripple.y, ripple.radius * 0.7, 0, Math.PI * 2);
            this.ctx.stroke();
            
            this.ctx.restore();
        });
    }
    
    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.updateRipples();
        this.drawRipples();
        
        this.animationId = requestAnimationFrame(() => this.animate());
    }
    
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
        window.removeEventListener('resize', this.resizeCanvas);
        window.removeEventListener('click', this.onClick);
    }
}

// 导出所有类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ParticlesBackground,
        DataFlowAnimation,
        NeonBorder,
        GradientAnimation,
        Card3D,
        TypewriterEffect,
        CountUp,
        PulseEffect,
        GlassmorphismEffect,
        FloatingAnimation,
        MouseTrailEffect,
        MouseClickRipple
    };
}
