/**
 * Power BI Explorer - Modern JavaScript
 * Core functionality for the modern interface
 */

(function () {
  "use strict";

  // DOM Elements
  const body = document.body;
  const sidebar = document.querySelector(".sidebar");
  const helpButton = document.querySelector(".help-button");

  /**
   * Initialize the application
   */
  function init() {
    console.log("Modern Analytics UI initialized");

    // Initialize dynamic features
    initDateTime();
    initCounters();

    // Setup event listeners
    setupEventListeners();
  }

  /**
   * Setup event listeners for interactive elements
   */
  function setupEventListeners() {
    // Sidebar toggle for mobile
    const sidebarToggle = document.querySelector(".sidebar-toggle");
    if (sidebarToggle) {
      sidebarToggle.addEventListener("click", toggleSidebar);
    }

    // Help button
    if (helpButton) {
      helpButton.addEventListener("click", showHelp);
    }
  }

  /**
   * Initialize and start the datetime display
   */
  function initDateTime() {
    updateDateTime();
    // Update every second
    setInterval(updateDateTime, 1000);
  }

  /**
   * Update the current date and time display
   */
  function updateDateTime() {
    const datetimeElement = document.getElementById('current-datetime');
    if (datetimeElement) {
      const now = new Date();
      const options = {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      };
      datetimeElement.textContent = now.toLocaleDateString('en-US', options);
    }
  }

  /**
   * Toggle sidebar visibility (mobile)
   */
  function toggleSidebar() {
    const sidebar = document.querySelector(".sidebar");
    if (sidebar) {
      sidebar.classList.toggle("open");
    }
  }

  /**
   * Show help by opening GitHub repository
   */
  function showHelp() {
    // GitHub repository URL
    const githubUrl = "https://github.com/plagiagia/PowerBI_AnalysisTool";

    // Open GitHub repository in a new tab
    window.open(githubUrl, "_blank");

    // Show notification
    showNotification("Documentation opened in a new tab", "info");
  }

  /**
   * Initialize counters with animation
   */
  function initCounters() {
    document.querySelectorAll(".metric-value").forEach((counter) => {
      const target = parseInt(counter.getAttribute("data-value"), 10) || 0;
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

      if (
        (increment > 0 && current >= target) ||
        (increment < 0 && current <= target)
      ) {
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
  function showNotification(message, type = "info", duration = 3000) {
    const container = document.querySelector(".notification-container");

    if (!container) return;

    // Create notification element
    const notification = document.createElement("div");
    notification.className = `notification notification-${type}`;

    // Icon based on type
    let icon = "";
    switch (type) {
      case "success":
        icon = '<i class="fas fa-check-circle"></i>';
        break;
      case "error":
        icon = '<i class="fas fa-exclamation-circle"></i>';
        break;
      case "warning":
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
      notification.classList.add("visible");
    }, 10);

    // Close button functionality
    const closeButton = notification.querySelector(".notification-close");
    if (closeButton) {
      closeButton.addEventListener("click", () => {
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
    notification.classList.remove("visible");

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
    return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1,");
  }

  /**
   * Export functionality for use in other scripts
   */
  window.PowerBIExplorer = {
    showNotification,
    debounce,
    formatNumber,
  };

  // Initialize when DOM is ready
  document.addEventListener("DOMContentLoaded", init);
})();
