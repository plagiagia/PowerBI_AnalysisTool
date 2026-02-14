(function () {
  "use strict";

  function setupSidebar() {
    const toggle = document.getElementById("wbSidebarToggle");
    const backdrop = document.getElementById("wbBackdrop");
    const body = document.body;

    if (!toggle || !backdrop) {
      return;
    }

    toggle.addEventListener("click", function () {
      body.classList.toggle("sidebar-open");
    });

    backdrop.addEventListener("click", function () {
      body.classList.remove("sidebar-open");
    });
  }

  function setupCardReveal() {
    const cards = document.querySelectorAll(".wb-card");
    if (!cards.length) {
      return;
    }

    if (!("IntersectionObserver" in window)) {
      cards.forEach((card) => card.classList.add("wb-card-visible"));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("wb-card-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.05,
        rootMargin: "40px",
      }
    );

    cards.forEach((card) => observer.observe(card));
  }

  function ensureNotificationContainer() {
    let container = document.getElementById("notificationContainer");
    if (!container) {
      container = document.createElement("div");
      container.id = "notificationContainer";
      container.className = "notification-container";
      document.body.appendChild(container);
    }
    return container;
  }

  function showNotification(message, type, duration) {
    const notificationType = type || "info";
    const removeAfter = typeof duration === "number" ? duration : 2800;
    const container = ensureNotificationContainer();

    const toast = document.createElement("div");
    toast.className = "notification notification-" + notificationType;

    const iconByType = {
      success: "fa-check-circle",
      error: "fa-circle-exclamation",
      warning: "fa-triangle-exclamation",
      info: "fa-circle-info",
    };

    toast.innerHTML = [
      '<i class="fas ',
      iconByType[notificationType] || iconByType.info,
      '"></i><span></span>',
    ].join("");
    toast.querySelector("span").textContent = message;
    container.appendChild(toast);

    setTimeout(function () {
      toast.classList.add("visible");
    }, 10);

    setTimeout(function () {
      toast.classList.remove("visible");
      setTimeout(function () {
        toast.remove();
      }, 220);
    }, removeAfter);
  }

  function debounce(func, wait) {
    let timeout;
    const delay = typeof wait === "number" ? wait : 300;
    return function executedFunction() {
      const args = arguments;
      const later = function () {
        clearTimeout(timeout);
        func.apply(null, args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, delay);
    };
  }

  function formatNumber(num) {
    return Number(num || 0).toLocaleString("en-US");
  }

  document.addEventListener("DOMContentLoaded", function () {
    setupSidebar();
    setupCardReveal();
  });

  window.PowerBIExplorer = {
    showNotification: showNotification,
    debounce: debounce,
    formatNumber: formatNumber,
  };
})();
