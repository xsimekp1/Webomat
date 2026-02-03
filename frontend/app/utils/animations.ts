/**
 * Progressive Disclosure Animation Utilities
 * 
 * These utilities help implement subtle, sequential animations
 * that guide user attention based on visual hierarchy.
 */

// Animation delay utilities - create cascading effects
export const animationDelays = {
  immediate: 'delay-0',
  fast: 'delay-75',
  normal: 'delay-100', 
  medium: 'delay-150',
  slow: 'delay-200',
  slower: 'delay-300',
  slowest: 'delay-500'
} as const;

// Animation classes for different element types
export const animations = {
  // Entry animations - subtle and fast
  fadeIn: {
    initial: 'opacity-0',
    animate: 'opacity-100 transition-opacity duration-300 ease-out'
  },
  
  fadeInUp: {
    initial: 'opacity-0 transform translate-y-2',
    animate: 'opacity-100 transform translate-y-0 transition-all duration-400 ease-out'
  },
  
  fadeInDown: {
    initial: 'opacity-0 transform -translate-y-2', 
    animate: 'opacity-100 transform translate-y-0 transition-all duration-400 ease-out'
  },
  
  fadeInScale: {
    initial: 'opacity-0 transform scale-95',
    animate: 'opacity-100 transform scale-100 transition-all duration-300 ease-out'
  },
  
  slideInRight: {
    initial: 'opacity-0 transform translate-x-4',
    animate: 'opacity-100 transform translate-x-0 transition-all duration-400 ease-out'
  },
  
  slideInLeft: {
    initial: 'opacity-0 transform -translate-x-4',
    animate: 'opacity-100 transform translate-x-0 transition-all duration-400 ease-out'
  }
} as const;

// Visual hierarchy levels with corresponding animations
export const hierarchyLevels = {
  // Level 0: Primary elements (hero, main title) - immediate, prominent
  primary: {
    animation: animations.fadeInDown,
    delay: animationDelays.immediate,
    className: 'opacity-0 -translate-y-2 animate-fade-in-down'
  },
  
  // Level 1: Secondary elements (subtitles, main actions) - fast
  secondary: {
    animation: animations.fadeInUp,
    delay: animationDelays.fast,
    className: 'opacity-0 translate-y-2 animate-fade-in-up'
  },
  
  // Level 2: Content elements (cards, forms) - normal delay
  content: {
    animation: animations.fadeInScale,
    delay: animationDelays.normal,
    className: 'opacity-0 scale-95 animate-fade-in-scale'
  },
  
  // Level 3: Supporting elements (metadata, secondary actions) - medium delay
  supporting: {
    animation: animations.fadeIn,
    delay: animationDelays.medium,
    className: 'opacity-0 animate-fade-in'
  },
  
  // Level 4: Detail elements (fine print, tertiary actions) - slow delay
  details: {
    animation: animations.slideInRight,
    delay: animationDelays.slow,
    className: 'opacity-0 translate-x-4 animate-slide-in-right'
  }
} as const;

// Component-level animation utilities
export const createProgressiveAnimation = (level: keyof typeof hierarchyLevels) => {
  return hierarchyLevels[level];
};

// Hook for progressive disclosure
export const useProgressiveDisclosure = () => {
  return {
    animations: hierarchyLevels,
    delays: animationDelays,
    createAnimation: createProgressiveAnimation
  };
};

// CSS Animation definitions (to be added to globals.css)
export const animationCSS = `
@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fade-in-up {
  from { 
    opacity: 0;
    transform: translateY(0.5rem);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fade-in-down {
  from { 
    opacity: 0;
    transform: translateY(-0.5rem);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fade-in-scale {
  from { 
    opacity: 0;
    transform: scale(0.95);
  }
  to { 
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes slide-in-right {
  from { 
    opacity: 0;
    transform: translateX(1rem);
  }
  to { 
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slide-in-left {
  from { 
    opacity: 0;
    transform: translateX(-1rem);
  }
  to { 
    opacity: 1;
    transform: translateX(0);
  }
}

// Animation classes
.animate-fade-in {
  animation: fade-in 300ms ease-out forwards;
}

.animate-fade-in-up {
  animation: fade-in-up 400ms ease-out forwards;
}

.animate-fade-in-down {
  animation: fade-in-down 400ms ease-out forwards;
}

.animate-fade-in-scale {
  animation: fade-in-scale 300ms ease-out forwards;
}

.animate-slide-in-right {
  animation: slide-in-right 400ms ease-out forwards;
}

.animate-slide-in-left {
  animation: slide-in-left 400ms ease-out forwards;
}

// Delay utilities
.delay-75 { animation-delay: 75ms; }
.delay-150 { animation-delay: 150ms; }
.delay-300 { animation-delay: 300ms; }
.delay-500 { animation-delay: 500ms; }
`;