/**
 * AI-powered features for lineage view
 */

document.addEventListener("DOMContentLoaded", function () {
  // DOM Elements
  const optimizedTab = document.getElementById("optimizedTab");
  const explanationTab = document.getElementById("explanationTab");
  const optimizedDefinition = document.getElementById("optimizedDefinition");
  const explanationDefinition = document.getElementById("explanationDefinition");
  const optimizedCode = document.getElementById("optimizedCode");
  const explanationContent = document.getElementById("explanationContent");
  const optimizedLoading = document.getElementById("optimizedLoading");
  const explanationLoading = document.getElementById("explanationLoading");
  const measureName = document.getElementById("measureName");
  const originalCode = document.getElementById("originalCode");
  
  // Set up event listeners for AI tabs
  if (optimizedTab) {
    optimizedTab.addEventListener("click", function () {
      switchTab("optimized");
      // Load optimized version if not already loaded
      if (optimizedCode && optimizedCode.textContent.includes("Select a measure")) {
        loadOptimizedDefinition();
      }
    });
  }
  
  if (explanationTab) {
    explanationTab.addEventListener("click", function () {
      switchTab("explanation");
      // Load explanation if not already loaded
      if (explanationContent && explanationContent.querySelector(".placeholder-text")) {
        loadExplanation();
      }
    });
  }
  
  /**
   * Switch between tabs in the measure details card
   * @param {string} tabName - Name of the tab to switch to
   */
  function switchTab(tabName) {
    // Get all tab elements
    const tabs = document.querySelectorAll(".measure-tab");
    const contents = document.querySelectorAll(".tab-content");
    
    // Remove active class from all tabs and content
    tabs.forEach(tab => tab.classList.remove("active"));
    contents.forEach(content => content.classList.remove("active"));
    
    // Add active class to selected tab and content
    if (tabName === "original") {
      document.getElementById("originalTab").classList.add("active");
      document.getElementById("originalDefinition").classList.add("active");
    } else if (tabName === "expanded") {
      document.getElementById("expandedTab").classList.add("active");
      document.getElementById("expandedDefinition").classList.add("active");
    } else if (tabName === "optimized") {
      document.getElementById("optimizedTab").classList.add("active");
      document.getElementById("optimizedDefinition").classList.add("active");
    } else if (tabName === "explanation") {
      document.getElementById("explanationTab").classList.add("active");
      document.getElementById("explanationDefinition").classList.add("active");
    }
  }
  
  /**
   * Load optimized definition using AI
   */
  function loadOptimizedDefinition() {
    if (!optimizedCode || !optimizedLoading || !measureName) return;
    
    const currentMeasureName = measureName.textContent;
    const daxExpression = originalCode.textContent;
    
    if (!daxExpression || daxExpression.includes("Select a measure")) {
      return;
    }
    
    // Show loading indicator
    optimizedLoading.style.display = "flex";
    optimizedCode.textContent = "Optimizing...";
    
    // Call the API to optimize the DAX
    fetch('/api/optimize-dax', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        dax: daxExpression,
        measureName: currentMeasureName
      }),
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      // Hide loading indicator
      optimizedLoading.style.display = "none";
      
      // Update the optimized code
      if (data.optimized_dax) {
        optimizedCode.textContent = data.optimized_dax;
      } else {
        optimizedCode.textContent = "Failed to optimize the measure.";
      }
    })
    .catch(error => {
      console.error('Error optimizing DAX:', error);
      optimizedLoading.style.display = "none";
      optimizedCode.textContent = "Error: Failed to optimize the measure. Please try again.";
    });
  }
  
  /**
   * Load explanation using AI
   */
  function loadExplanation() {
    if (!explanationContent || !explanationLoading || !measureName) return;
    
    const currentMeasureName = measureName.textContent;
    const daxExpression = originalCode.textContent;
    
    if (!daxExpression || daxExpression.includes("Select a measure")) {
      return;
    }
    
    // Show loading indicator
    explanationLoading.style.display = "flex";
    explanationContent.innerHTML = "<div class='loading-text'>Generating explanation...</div>";
    
    // Call the API to explain the DAX
    fetch('/api/explain-dax', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        dax: daxExpression,
        measureName: currentMeasureName
      }),
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      // Hide loading indicator
      explanationLoading.style.display = "none";
      
      // Update the explanation content
      if (data.explanation) {
        // Convert markdown to HTML
        const converter = new showdown.Converter();
        const html = converter.makeHtml(data.explanation);
        explanationContent.innerHTML = html;
      } else {
        explanationContent.innerHTML = "<div class='error-text'>Failed to generate explanation.</div>";
      }
    })
    .catch(error => {
      console.error('Error explaining DAX:', error);
      explanationLoading.style.display = "none";
      explanationContent.innerHTML = "<div class='error-text'>Error: Failed to generate explanation. Please try again.</div>";
    });
  }
  
  // Expose functions to global scope for use in other scripts
  window.LineageAI = {
    switchTab,
    loadOptimizedDefinition,
    loadExplanation
  };
});
