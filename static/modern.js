/**
 * Power BI Analysis Tool - Essential JavaScript
 * Minimal, functional code for BI developers
 */

(function () {
  "use strict";

  const sidebar = document.querySelector(".sidebar");

  function init() {
    setupSidebarToggle();
  }

  /**
   * Mobile sidebar toggle
   */
  function setupSidebarToggle() {
    const sidebarToggle = document.querySelector(".sidebar-toggle");

    if (sidebarToggle && sidebar) {
      sidebarToggle.addEventListener("click", function() {
        sidebar.classList.toggle("open");
      });

      // Close on outside click (mobile)
      document.addEventListener("click", function(e) {
        if (window.innerWidth <= 768 && sidebar.classList.contains("open")) {
          if (!sidebar.contains(e.target) && !e.target.closest(".sidebar-toggle")) {
            sidebar.classList.remove("open");
          }
        }
      });
    }
  }

  /**
   * Show notification message
   */
  function showNotification(message, type, duration) {
    type = type || "info";
    duration = duration || 3000;

    var container = document.querySelector(".notification-container");
    if (!container) {
      container = document.createElement("div");
      container.className = "notification-container";
      document.body.appendChild(container);
    }

    var notification = document.createElement("div");
    notification.className = "notification notification-" + type;

    var icons = {
      success: "fa-check-circle",
      error: "fa-exclamation-circle",
      warning: "fa-exclamation-triangle",
      info: "fa-info-circle"
    };

    notification.innerHTML =
      '<div class="notification-icon"><i class="fas ' + (icons[type] || icons.info) + '"></i></div>' +
      '<div class="notification-message">' + message + '</div>' +
      '<button class="notification-close"><i class="fas fa-times"></i></button>';

    container.appendChild(notification);

    setTimeout(function() {
      notification.classList.add("visible");
    }, 10);

    notification.querySelector(".notification-close").addEventListener("click", function() {
      notification.remove();
    });

    setTimeout(function() {
      notification.remove();
    }, duration);
  }

  /**
   * Format number with commas
   */
  function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  /**
   * Debounce utility
   */
  function debounce(func, wait) {
    var timeout;
    wait = wait || 300;
    return function() {
      var args = arguments;
      var context = this;
      clearTimeout(timeout);
      timeout = setTimeout(function() {
        func.apply(context, args);
      }, wait);
    };
  }

  // Export utilities
  window.PowerBIExplorer = {
    showNotification: showNotification,
    formatNumber: formatNumber,
    debounce: debounce
  };

  document.addEventListener("DOMContentLoaded", init);
})();
