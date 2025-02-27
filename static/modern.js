/**
 * Power BI Explorer - Modern JavaScript
 * Core functionality for the modern interface
 */

(function() {
  'use strict';
  
  // DOM Elements
  const body = document.body;
  const sidebar = document.querySelector('.sidebar');
  const sidebarToggle = document.querySelector('.sidebar-toggle');
  const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
  const sidebarClose = document.querySelector('.sidebar-close');
  const themeToggle = document.querySelector('.theme-toggle');
  const helpButton = document.querySelector('.help-button');
  
  // State
  let darkMode = localStorage.getItem('darkMode') === 'true';
  
  /**
   * Initialize the application
   */
  function init() {
    // Set up event listeners
    setupEventListeners();
    
    // Initialize dark mode if needed
    if (darkMode) {
      enableDarkMode();
    }
    
    // Add loaded class for animation purposes
    setTimeout(() => {
      body.classList.add('app-loaded');
    }, 100);
  }
  
  /**
   * Set up event listeners for interactive elements
   */
  function setupEventListeners() {
    // Sidebar toggle
    if (sidebarToggle) {
      sidebarToggle.addEventListener('click', toggleSidebar);
    }
    
    // Mobile menu toggle
    if (mobileMenuToggle) {
      mobileMenuToggle.addEventListener('click', toggleSidebar);
    }
    
    // Sidebar close button
    if (sidebarClose) {
      sidebarClose.addEventListener('click', closeSidebar);
    }
    
    // Theme toggle
    if (themeToggle) {
      themeToggle.addEventListener('click', toggleDarkMode);
    }
    
    // Help button
    if (helpButton) {
      helpButton.addEventListener('click', showHelp);
    }
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
      const isMobile = window.innerWidth < 768;
      
      if (isMobile && 
          sidebar && 
          sidebar.classList.contains('open') && 
          !sidebar.contains(event.target) && 
          event.target !== mobileMenuToggle) {
        closeSidebar();
      }
    });
    
    // Window resize handling for responsive design
    window.addEventListener('resize', handleResize);
    
    // Initialize counters
    initCounters();
  }
  
  /**
   * Toggle the sidebar open/closed state
   */
  function toggleSidebar() {
    if (sidebar) {
      sidebar.classList.toggle('open');
      
      if (mobileMenuToggle) {
        if (sidebar.classList.contains('open')) {
          mobileMenuToggle.innerHTML = '<i class="fas fa-times"></i>';
          mobileMenuToggle.setAttribute('aria-expanded', 'true');
        } else {
          mobileMenuToggle.innerHTML = '<i class="fas fa-bars"></i>';
          mobileMenuToggle.setAttribute('aria-expanded', 'false');
        }
      }
    }
  }
  
  /**
   * Close the sidebar
   */
  function closeSidebar() {
    if (sidebar) {
      sidebar.classList.remove('open');
      
      if (mobileMenuToggle) {
        mobileMenuToggle.innerHTML = '<i class="fas fa-bars"></i>';
        mobileMenuToggle.setAttribute('aria-expanded', 'false');
      }
    }
  }
  
  /**
   * Toggle dark mode
   */
  function toggleDarkMode() {
    darkMode = !darkMode;
    localStorage.setItem('darkMode', darkMode);
    
    if (darkMode) {
      enableDarkMode();
    } else {
      disableDarkMode();
    }
  }
  
  /**
   * Enable dark mode
   */
  function enableDarkMode() {
    body.classList.add('dark-mode');
    
    if (themeToggle) {
      themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
      themeToggle.setAttribute('aria-label', 'Switch to light mode');
    }
  }
  
  /**
   * Disable dark mode
   */
  function disableDarkMode() {
    body.classList.remove('dark-mode');
    
    if (themeToggle) {
      themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
      themeToggle.setAttribute('aria-label', 'Switch to dark mode');
    }
  }
  
  /**
   * Show help information
   */
  function showHelp() {
    showNotification('Help documentation will open in a new tab', 'info');
    // In a real app, you would open help documentation or a modal here
  }
  
  /**
   * Handle window resize events
   */
  function handleResize() {
    // Close sidebar on mobile when resizing to desktop
    if (window.innerWidth >= 768 && sidebar && sidebar.classList.contains('open')) {
      closeSidebar();
    }
  }
  
  /**
   * Initialize counters with animation
   */
  function initCounters() {
    document.querySelectorAll('.metric-value').forEach(counter => {
      const target = parseInt(counter.getAttribute('data-value'), 10) || 0;
      animateCounter(counter, 0, target, 1500);
    });
  }
  
  /**
   * Animate a counter from start to target
   * @param {HTMLElement} element - The element to update
   * @param {number} start - Starting value
   * @param {number} target - Target value
   * @param {number} duration - Duration in milliseconds
   */
  function animateCounter(element, start, target, duration) {
    if (!element) return;
    
    const range = target - start;
    const increment = target > start ? 1 : -1;
    const stepTime = Math.abs(Math.floor(duration / range));
    let current = start;
    
    const timer = setInterval(() => {
      current += increment;
      element.textContent = current;
      
      if ((increment > 0 && current >= target) || 
          (increment < 0 && current <= target)) {
        element.textContent = target;
        clearInterval(timer);
      }
    }, stepTime);
  }
  
  /**
   * Show a notification message
   * @param {string} message - Message to display
   * @param {string} type - Notification type (success, error, warning, info)
   * @param {number} duration - Duration in milliseconds
   */
  function showNotification(message, type = 'info', duration = 3000) {
    const container = document.querySelector('.notification-container');
    
    if (!container) return;
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    // Icon based on type
    let icon = '';
    switch (type) {
      case 'success':
        icon = '<i class="fas fa-check-circle"></i>';
        break;
      case 'error':
        icon = '<i class="fas fa-exclamation-circle"></i>';
        break;
      case 'warning':
        icon = '<i class="fas fa-exclamation-triangle"></i>';
        break;
      default:
        icon = '<i class="fas fa-info-circle"></i>';
    }
    
    // Create notification content
    notification.innerHTML = `
      <div class="notification-icon">${icon}</div>
      <div class="notification-message">${message}</div>
      <button class="notification-close" aria-label="Close notification">
        <i class="fas fa-times"></i>
      </button>
    `;
    
    // Add to container
    container.appendChild(notification);
    
    // Add visible class after a short delay (for animation)
    setTimeout(() => {
      notification.classList.add('visible');
    }, 10);
    
    // Close button functionality
    const closeButton = notification.querySelector('.notification-close');
    if (closeButton) {
      closeButton.addEventListener('click', () => {
        removeNotification(notification);
      });
    }
    
    // Auto-remove after duration
    setTimeout(() => {
      removeNotification(notification);
    }, duration);
  }
  
  /**
   * Remove a notification with animation
   * @param {HTMLElement} notification - The notification to remove
   */
  function removeNotification(notification) {
    notification.classList.remove('visible');
    
    // Remove from DOM after animation completes
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 300);
  }
  
  /**
   * Creates a debounced function that delays invoking func until after wait milliseconds
   * @param {Function} func - The function to debounce
   * @param {number} wait - The number of milliseconds to delay
   * @returns {Function} The debounced function
   */
  function debounce(func, wait = 300) {
    let timeout;
    
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
  
  /**
   * Format a number (e.g., 1000 -> 1,000)
   * @param {number} num - The number to format
   * @returns {string} The formatted number
   */
  function formatNumber(num) {
    return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,');
  }
  
  /**
   * Export functionality for use in other scripts
   */
  window.PowerBIExplorer = {
    showNotification,
    debounce,
    formatNumber
  };
  
  // Initialize when DOM is ready
  document.addEventListener('DOMContentLoaded', init);
})();
