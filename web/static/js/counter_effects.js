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
        let progress = Math.min(value / limit, 1); // Cap at 1 (100%)
        
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
    
    // Handle vertical bar counter change indicators
    const counterBars = document.querySelectorAll('.counter-bar[data-change]');
    
    counterBars.forEach(counterBar => {
        const change = parseFloat(counterBar.dataset.change);
        const barFill = counterBar.querySelector('.bar-fill');
        
        // Calculate progress based on change value
        // Map change values (-1 to +1) to fill percentage (0 to 100%)
        let progress = Math.min(Math.abs(change), 1);
        // Convert progress to height percentage
        const heightPercentage = progress * 100;
        
        // Handle different change states
        if (change <= 0) {
            // Negative change: dimmed appearance with gray gradient
            barFill.style.opacity = '0.5';
            setTimeout(() => {
                barFill.style.height = `${heightPercentage}%`;
            }, 300);
        } else {
            // Positive change: normal appearance
            barFill.style.opacity = '1';
            setTimeout(() => {
                barFill.style.height = `${heightPercentage}%`;
            }, 300);
            
            // Enhanced glow for significant positive changes
            if (change >= 1.0) {
                const isCultist = counterBar.classList.contains('cultist-bar');
                if (isCultist) {
                    barFill.style.boxShadow = '0 0 8px rgba(220, 20, 60, 0.9)';
                } else {
                    barFill.style.boxShadow = '0 0 8px rgba(59, 130, 246, 0.9)';
                }
            }
        }
    });
});