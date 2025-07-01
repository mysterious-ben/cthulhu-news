/**
 * Dynamic circular gauge effects based on values
 */
document.addEventListener('DOMContentLoaded', function() {
    const gauges = document.querySelectorAll('.circular-gauge[data-value]');
    
    gauges.forEach(gauge => {
        const value = parseFloat(gauge.dataset.value);
        const limit = parseFloat(gauge.dataset.limit);
        const gaugeFill = gauge.querySelector('.gauge-fill');
        
        // Calculate progress (0 to 1)
        let progress = 0;
        if (value > 0) {
            progress = Math.min(value / limit, 1); // Cap at 1 (100%)
        }
        
        // Calculate stroke-dashoffset for circular progress
        // Circumference is 314 (2 * π * 50), so offset should be 314 * (1 - progress)
        const circumference = 314;
        const offset = circumference * (1 - progress);
        
        // Handle visibility: completely black (invisible) if <= 0
        if (value <= 0) {
            gaugeFill.style.opacity = '0';
            gaugeFill.style.strokeDashoffset = circumference; // Completely empty
        } else {
            gaugeFill.style.opacity = '1';
            
            // Animate the gauge filling
            setTimeout(() => {
                gaugeFill.style.strokeDashoffset = offset;
            }, 200);
            
            // Add pulsing animation if at or above limit
            if (value >= limit) {
                gauge.classList.add('gauge-pulse');
            }
        }
        
        // Enhanced glow effects based on progress
        if (progress > 0.8) {
            // High intensity for near-full gauges
            const isCultist = gauge.dataset.faction === 'cultist';
            if (isCultist) {
                gaugeFill.style.filter = 'drop-shadow(0 0 8px rgba(220, 20, 60, 0.9))';
            } else {
                gaugeFill.style.filter = 'drop-shadow(0 0 8px rgba(59, 130, 246, 0.9))';
            }
        } else if (progress > 0.5) {
            // Medium intensity for half-full gauges
            const isCultist = gauge.dataset.faction === 'cultist';
            if (isCultist) {
                gaugeFill.style.filter = 'drop-shadow(0 0 6px rgba(220, 20, 60, 0.7))';
            } else {
                gaugeFill.style.filter = 'drop-shadow(0 0 6px rgba(59, 130, 246, 0.7))';
            }
        }
    });
});