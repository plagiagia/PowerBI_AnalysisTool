/**
 * Power BI Explorer - Ultra Modern JavaScript
 * Enhanced functionality for the vibing modern interface
 */

(function () {
  "use strict";

  // DOM Elements
  const body = document.body;
  const sidebar = document.querySelector(".sidebar");
  const themeToggle = document.querySelector(".theme-toggle");
  const helpButton = document.querySelector(".help-button");

  // State
  let darkMode = true; // Default to dark mode for modern vibes
  
  // Check for saved theme preference or default to dark mode
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "light") {
    darkMode = false;
  }

  /**
   * Initialize the application
   */
  function init() {
    // Set initial theme
    if (!darkMode) {
      body.classList.add("light-mode");
    }

    // Set up event listeners
    setupEventListeners();

    // Initialize datetime display
    initDateTime();

    // Initialize animations
    initAnimations();

    // Add loaded class for animation purposes
    setTimeout(() => {
      body.classList.add("app-loaded");
    }, 100);

    // Initialize particle background
    initParticleBackground();
  }

  /**
   * Set up event listeners for interactive elements
   */
  function setupEventListeners() {
    // Theme toggle
    if (themeToggle) {
      themeToggle.addEventListener("click", toggleTheme);
    }

    // Help button
    if (helpButton) {
      helpButton.addEventListener("click", showHelp);
    }

    // Sidebar toggle
    const sidebarToggle = document.querySelector(".sidebar-toggle");
    if (sidebarToggle) {
      sidebarToggle.addEventListener("click", toggleSidebar);
    }

    // Initialize counters
    initCounters();

    // Add hover effects
    initHoverEffects();

    // Mobile menu close on outside click
    document.addEventListener("click", (e) => {
      if (window.innerWidth <= 768 && sidebar && sidebar.classList.contains("open")) {
        if (!sidebar.contains(e.target) && !e.target.closest(".sidebar-toggle")) {
          sidebar.classList.remove("open");
        }
      }
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener("click", function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute("href"));
        if (target) {
          target.scrollIntoView({
            behavior: "smooth",
            block: "start"
          });
        }
      });
    });
  }

  /**
   * Initialize and start the datetime display
   */
  function initDateTime() {
    updateDateTime();
    setInterval(updateDateTime, 1000);
  }

  /**
   * Update the current date and time display
   */
  function updateDateTime() {
    const datetimeElement = document.getElementById("current-datetime");
    if (datetimeElement) {
      const now = new Date();
      const options = {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      };
      datetimeElement.textContent = now.toLocaleDateString("en-US", options);
    }
  }

  /**
   * Toggle theme between dark and light mode
   */
  function toggleTheme() {
    darkMode = !darkMode;
    
    if (darkMode) {
      body.classList.remove("light-mode");
      localStorage.setItem("theme", "dark");
    } else {
      body.classList.add("light-mode");
      localStorage.setItem("theme", "light");
    }

    // Update theme toggle icon
    if (themeToggle) {
      const icon = themeToggle.querySelector("i");
      if (icon) {
        icon.className = darkMode ? "fas fa-sun" : "fas fa-moon";
      }
      themeToggle.setAttribute("aria-label", darkMode ? "Switch to light mode" : "Switch to dark mode");
    }

    // Trigger theme change event
    document.dispatchEvent(new CustomEvent("themeChanged", { 
      detail: { theme: darkMode ? "dark" : "light" } 
    }));
  }

  /**
   * Toggle sidebar visibility (mobile)
   */
  function toggleSidebar() {
    if (sidebar) {
      sidebar.classList.toggle("open");
      
      // Add backdrop for mobile
      let backdrop = document.querySelector(".sidebar-backdrop");
      if (!backdrop) {
        backdrop = document.createElement("div");
        backdrop.className = "sidebar-backdrop";
        document.body.appendChild(backdrop);
      }
      
      if (sidebar.classList.contains("open")) {
        backdrop.classList.add("active");
        backdrop.addEventListener("click", () => {
          sidebar.classList.remove("open");
          backdrop.classList.remove("active");
        });
      } else {
        backdrop.classList.remove("active");
      }
    }
  }

  /**
   * Show help by opening GitHub repository
   */
  function showHelp() {
    const githubUrl = "https://github.com/plagiagia/PowerBI_AnalysisTool";
    window.open(githubUrl, "_blank");
    showNotification("Documentation opened in a new tab", "info");
  }

  /**
   * Initialize counters with smooth animation
   */
  function initCounters() {
    const counters = document.querySelectorAll(".metric-value[data-value]");
    
    const observerOptions = {
      threshold: 0.5,
      rootMargin: "0px"
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const counter = entry.target;
          const target = parseInt(counter.getAttribute("data-value"), 10) || 0;
          animateCounter(counter, 0, target, 2000);
          observer.unobserve(counter);
        }
      });
    }, observerOptions);

    counters.forEach(counter => observer.observe(counter));
  }

  /**
   * Animate a counter from start to target with easing
   */
  function animateCounter(element, start, target, duration) {
    if (!element) return;

    let startTime = null;
    const easeOutQuart = t => 1 - Math.pow(1 - t, 4);

    const animate = (currentTime) => {
      if (!startTime) startTime = currentTime;
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easedProgress = easeOutQuart(progress);
      const current = Math.floor(start + (target - start) * easedProgress);
      
      element.textContent = formatNumber(current);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }

  /**
   * Initialize hover effects and micro-interactions
   */
  function initHoverEffects() {
    // Tool cards 3D tilt effect
    const cards = document.querySelectorAll(".modern-tool-card, .metric-card-enhanced");
    cards.forEach(card => {
      card.addEventListener("mousemove", handleCardTilt);
      card.addEventListener("mouseleave", resetCardTilt);
    });

    // Button ripple effect
    const buttons = document.querySelectorAll(".modern-button, .action-button");
    buttons.forEach(button => {
      button.addEventListener("click", createRipple);
    });

    // Navigation items
    const navItems = document.querySelectorAll(".nav-link");
    navItems.forEach(item => {
      item.addEventListener("mouseenter", () => {
        item.style.setProperty("--hover-scale", "1.02");
      });
      item.addEventListener("mouseleave", () => {
        item.style.setProperty("--hover-scale", "1");
      });
    });
  }

  /**
   * Handle 3D card tilt effect
   */
  function handleCardTilt(e) {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = (y - centerY) / 10;
    const rotateY = (centerX - x) / 10;

    card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(10px)`;
  }

  /**
   * Reset card tilt
   */
  function resetCardTilt(e) {
    const card = e.currentTarget;
    card.style.transform = "perspective(1000px) rotateX(0) rotateY(0) translateZ(0)";
  }

  /**
   * Create ripple effect on button click
   */
  function createRipple(e) {
    const button = e.currentTarget;
    const ripple = document.createElement("span");
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;

    ripple.style.width = ripple.style.height = size + "px";
    ripple.style.left = x + "px";
    ripple.style.top = y + "px";
    ripple.classList.add("ripple");

    button.appendChild(ripple);

    setTimeout(() => {
      ripple.remove();
    }, 600);
  }

  /**
   * Initialize animations
   */
  function initAnimations() {
    // Intersection Observer for fade-in animations
    const animatedElements = document.querySelectorAll(".metric-card-enhanced, .modern-tool-card");
    
    const animationObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
          setTimeout(() => {
            entry.target.classList.add("animate-in");
          }, index * 100);
          animationObserver.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: "50px"
    });

    animatedElements.forEach(element => {
      element.style.opacity = "0";
      element.style.transform = "translateY(30px)";
      animationObserver.observe(element);
    });
  }

  /**
   * Initialize particle background effect
   */
  function initParticleBackground() {
    const particleCount = 50;
    const container = document.createElement("div");
    container.className = "particle-container";
    container.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: -1;
      overflow: hidden;
    `;

    for (let i = 0; i < particleCount; i++) {
      const particle = document.createElement("div");
      particle.className = "particle";
      particle.style.cssText = `
        position: absolute;
        width: ${Math.random() * 4 + 1}px;
        height: ${Math.random() * 4 + 1}px;
        background: rgba(102, 126, 234, ${Math.random() * 0.3 + 0.1});
        border-radius: 50%;
        left: ${Math.random() * 100}%;
        top: ${Math.random() * 100}%;
        animation: particleFloat ${Math.random() * 20 + 10}s linear infinite;
      `;
      container.appendChild(particle);
    }

    document.body.appendChild(container);
  }

  /**
   * Show a notification message
   */
  function showNotification(message, type = "info", duration = 3000) {
    let container = document.querySelector(".notification-container");
    
    if (!container) {
      container = document.createElement("div");
      container.className = "notification-container";
      document.body.appendChild(container);
    }

    const notification = document.createElement("div");
    notification.className = `notification notification-${type}`;

    const icons = {
      success: "fa-check-circle",
      error: "fa-exclamation-circle",
      warning: "fa-exclamation-triangle",
      info: "fa-info-circle"
    };

    notification.innerHTML = `
      <div class="notification-icon">
        <i class="fas ${icons[type] || icons.info}"></i>
      </div>
      <div class="notification-message">${message}</div>
      <button class="notification-close" aria-label="Close notification">
        <i class="fas fa-times"></i>
      </button>
    `;

    container.appendChild(notification);

    // Trigger reflow and add visible class
    notification.offsetHeight;
    setTimeout(() => notification.classList.add("visible"), 10);

    // Close button functionality
    const closeButton = notification.querySelector(".notification-close");
    closeButton.addEventListener("click", () => removeNotification(notification));

    // Auto-remove after duration
    setTimeout(() => removeNotification(notification), duration);
  }

  /**
   * Remove a notification with animation
   */
  function removeNotification(notification) {
    notification.classList.remove("visible");
    setTimeout(() => notification.remove(), 300);
  }

  /**
   * Format a number with commas
   */
  function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  /**
   * Debounce function for performance
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
   * Export functionality for use in other scripts
   */
  window.PowerBIExplorer = {
    showNotification,
    debounce,
    formatNumber,
    toggleTheme
  };

  // Initialize when DOM is ready
  document.addEventListener("DOMContentLoaded", init);

  // Add CSS for animations
  const style = document.createElement("style");
  style.textContent = `
    .animate-in {
      opacity: 1 !important;
      transform: translateY(0) !important;
      transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .ripple {
      position: absolute;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.4);
      transform: scale(0);
      animation: ripple-animation 0.6s linear;
      pointer-events: none;
    }

    @keyframes ripple-animation {
      to {
        transform: scale(4);
        opacity: 0;
      }
    }

    @keyframes particleFloat {
      0% {
        transform: translateY(100vh) translateX(0);
        opacity: 0;
      }
      10% {
        opacity: 1;
      }
      90% {
        opacity: 1;
      }
      100% {
        transform: translateY(-100vh) translateX(100px);
        opacity: 0;
      }
    }

    .sidebar-backdrop {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.5);
      backdrop-filter: blur(5px);
      z-index: 1400;
      opacity: 0;
      visibility: hidden;
      transition: all 0.3s ease;
    }

    .sidebar-backdrop.active {
      opacity: 1;
      visibility: visible;
    }
  `;
  document.head.appendChild(style);
})();
