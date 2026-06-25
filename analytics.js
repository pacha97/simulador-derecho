/**
 * Vercel Web Analytics Integration
 * Initializes analytics tracking for the application
 */

(function() {
    'use strict';
    
    // Initialize Vercel Analytics queue
    if (typeof window !== 'undefined') {
        window.va = window.va || function() {
            (window.vaq = window.vaq || []).push(arguments);
        };
    }
    
    // Load the Vercel Analytics script
    (function() {
        var script = document.createElement('script');
        script.defer = true;
        
        // Use production script by default
        // For debugging, you can change this to 'script.debug.js'
        script.src = 'https://cdn.vercel-insights.com/v1/script.js';
        
        // Handle script load errors gracefully
        script.onerror = function() {
            console.warn('Vercel Analytics: Failed to load analytics script');
        };
        
        document.head.appendChild(script);
    })();
})();
