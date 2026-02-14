class DAXExplorer {
  constructor() {
    this.daxExpressions = this.collectDAXExpressions();
    this.filteredExpressions = [...this.daxExpressions];
    this.measureNameLookup = this.buildMeasureLookup();

    this.similarityResults = [];
    this.similarityTask = this.createSimilarityTask();
    this.similarityChunkBudgetMs = 12;

    this.highlightResetTimer = null;
    this.lastFilterState = this.getFilterState();

    this.init();
  }

  init() {
    this.setupEventListeners();
    this.applyInitialHighlighting();
    this.applyFiltersAndSearch();
    this.updateSimilarityProgress("Idle", "idle");
    this.updateSimilarityStats(this.getTotalPairCount(), 0, 0);
  }

  createSimilarityTask() {
    return {
      running: false,
      cancelled: false,
      totalPairs: 0,
      processedPairs: 0,
      i: 0,
      j: 1,
      results: [],
      highestSimilarity: 0,
    };
  }

  collectDAXExpressions() {
    const expressions = [];

    document.querySelectorAll(".dax-card").forEach((card) => {
      const name = card.getAttribute("data-measure");
      const codeElement = card.querySelector("code");
      const nameElement = card.querySelector(".measure-name");

      if (!name || !codeElement || !nameElement) {
        return;
      }

      const code = codeElement.textContent || "";
      nameElement.dataset.originalText = nameElement.textContent || name;

      expressions.push({
        name,
        nameLower: name.toLowerCase(),
        code,
        codeLower: code.toLowerCase(),
        element: card,
        codeElement,
        nameElement,
        length: parseInt(card.getAttribute("data-length") || "0", 10),
      });
    });

    return expressions;
  }

  buildMeasureLookup() {
    const lookup = new Map();
    this.daxExpressions.forEach((expr) => {
      lookup.set(expr.name.toLowerCase(), expr.name);
    });
    return lookup;
  }

  setupEventListeners() {
    const searchInput = document.getElementById("searchDax");
    const clearSearch = document.getElementById("clearSearch");
    const searchInCode = document.getElementById("searchInCode");
    const caseSensitive = document.getElementById("caseSensitive");

    const runSearch = this.debounce(() => this.applyFiltersAndSearch(), 250);

    searchInput?.addEventListener("input", () => {
      if (clearSearch) {
        clearSearch.style.display = searchInput.value ? "block" : "none";
      }
      runSearch();
    });

    clearSearch?.addEventListener("click", () => {
      if (searchInput) {
        searchInput.value = "";
      }
      clearSearch.style.display = "none";
      this.applyFiltersAndSearch();
    });

    searchInCode?.addEventListener("change", () => this.applyFiltersAndSearch());
    caseSensitive?.addEventListener("change", () => this.applyFiltersAndSearch());

    document.getElementById("functionFilter")?.addEventListener("change", () => this.applyFiltersAndSearch());
    document.getElementById("expandAll")?.addEventListener("click", () => this.toggleAllCards(true));
    document.getElementById("collapseAll")?.addEventListener("click", () => this.toggleAllCards(false));
    document.getElementById("exportDax")?.addEventListener("click", () => this.exportDAX());
    document.getElementById("clearFilters")?.addEventListener("click", () => this.clearAllFilters());

    document.getElementById("analyzeSimilarity")?.addEventListener("click", () => this.showSimilarityAnalysis());
    document.getElementById("closeSimilarity")?.addEventListener("click", () => this.hideSimilarityAnalysis());
    document.getElementById("cancelSimilarity")?.addEventListener("click", () => this.cancelSimilarityAnalysis());
    document.getElementById("similarityThreshold")?.addEventListener("input", (event) => this.updateSimilarityThreshold(event));
    document.getElementById("exportSimilarity")?.addEventListener("click", () => this.exportSimilarityResults());

    document.getElementById("daxList")?.addEventListener("click", (event) => this.handleCardAction(event));
    document.getElementById("similarityGrid")?.addEventListener("click", (event) => this.handleSimilarityAction(event));
  }

  handleCardAction(event) {
    const button = event.target.closest("button");
    if (!button) {
      return;
    }

    const card = button.closest(".dax-card");
    if (!card) {
      return;
    }

    if (button.classList.contains("toggle-expand")) {
      this.toggleCard(card);
      return;
    }

    if (button.classList.contains("copy-name")) {
      const name = button.getAttribute("data-copy") || "";
      this.copyToClipboard(name, "Measure name");
      return;
    }

    if (button.classList.contains("copy-code")) {
      const measureName = button.getAttribute("data-measure");
      const measure = this.daxExpressions.find((expr) => expr.name === measureName);
      if (measure) {
        this.copyToClipboard(measure.code, "DAX code");
      }
      return;
    }

    if (button.classList.contains("format-code")) {
      this.formatDAXCode(card);
      return;
    }

    if (button.classList.contains("analyze-dependencies")) {
      this.analyzeMeasureDependencies(card);
    }
  }
  handleSimilarityAction(event) {
    const actionButton = event.target.closest("button[data-action]");
    if (!actionButton) {
      return;
    }

    const index = Number.parseInt(actionButton.dataset.index || "", 10);
    if (!Number.isFinite(index)) {
      return;
    }

    const action = actionButton.dataset.action;
    if (action === "compare") {
      this.compareMeasures(index);
      return;
    }

    if (action === "highlight") {
      const result = this.similarityResults[index];
      if (result) {
        this.highlightMeasures(result.measure1, result.measure2);
      }
    }
  }

  getFilterState() {
    const searchInput = document.getElementById("searchDax");
    const rawQuery = searchInput?.value || "";
    const caseSensitive = Boolean(document.getElementById("caseSensitive")?.checked);
    const searchInCode = Boolean(document.getElementById("searchInCode")?.checked);
    const functionFilter = document.getElementById("functionFilter")?.value || "all";

    return {
      rawQuery,
      query: caseSensitive ? rawQuery : rawQuery.toLowerCase(),
      searchInCode,
      caseSensitive,
      functionFilter,
    };
  }

  applyFiltersAndSearch() {
    const state = this.getFilterState();
    this.lastFilterState = state;
    this.clearHighlights();

    this.filteredExpressions = this.daxExpressions.filter((expr) => {
      const searchMatch = this.matchesSearch(expr, state);
      if (!searchMatch.matches) {
        return false;
      }

      if (!this.matchesFunctionFilter(expr.code, state.functionFilter)) {
        return false;
      }

      if (state.query && searchMatch.nameMatch) {
        this.highlightNameMatch(expr, state.rawQuery, state.caseSensitive);
      }

      return true;
    });

    this.updateDisplay();
  }

  performSearch() {
    this.applyFiltersAndSearch();
  }

  applyFilters() {
    this.applyFiltersAndSearch();
  }

  matchesSearch(expr, state) {
    if (!state.query) {
      return { matches: true, nameMatch: false, codeMatch: false };
    }

    const nameSource = state.caseSensitive ? expr.name : expr.nameLower;
    const codeSource = state.caseSensitive ? expr.code : expr.codeLower;

    const nameMatch = nameSource.includes(state.query);
    const codeMatch = state.searchInCode && codeSource.includes(state.query);

    return {
      matches: nameMatch || codeMatch,
      nameMatch,
      codeMatch,
    };
  }

  matchesFunctionFilter(code, functionFilter) {
    if (functionFilter === "all") {
      return true;
    }

    if (functionFilter === "other") {
      return !/\b(CALCULATE|SUMX|AVERAGEX|FILTER|IF|SWITCH)\b/i.test(code);
    }

    if (functionFilter === "SUMX") {
      return /\b(SUMX|AVERAGEX)\b/i.test(code);
    }

    return new RegExp(`\\b${functionFilter}\\b`, "i").test(code);
  }

  highlightNameMatch(expr, query, caseSensitive) {
    const nameElement = expr.nameElement;
    const originalText = nameElement?.dataset.originalText || expr.name;
    if (!nameElement) {
      return;
    }

    nameElement.replaceChildren();
    if (!query) {
      nameElement.textContent = originalText;
      return;
    }

    const haystack = caseSensitive ? originalText : originalText.toLowerCase();
    const needle = caseSensitive ? query : query.toLowerCase();

    if (!needle || !haystack.includes(needle)) {
      nameElement.textContent = originalText;
      return;
    }

    let startIndex = 0;
    let matchIndex = haystack.indexOf(needle, startIndex);

    while (matchIndex !== -1) {
      if (matchIndex > startIndex) {
        nameElement.append(document.createTextNode(originalText.slice(startIndex, matchIndex)));
      }

      const mark = document.createElement("mark");
      mark.textContent = originalText.slice(matchIndex, matchIndex + needle.length);
      nameElement.append(mark);

      startIndex = matchIndex + needle.length;
      matchIndex = haystack.indexOf(needle, startIndex);
    }

    if (startIndex < originalText.length) {
      nameElement.append(document.createTextNode(originalText.slice(startIndex)));
    }
  }

  clearHighlights() {
    this.daxExpressions.forEach((expr) => {
      if (!expr.nameElement) {
        return;
      }
      const originalText = expr.nameElement.dataset.originalText || expr.name;
      expr.nameElement.textContent = originalText;
    });
  }

  updateDisplay() {
    this.daxExpressions.forEach((expr) => {
      expr.element.style.display = "none";
    });

    this.filteredExpressions.forEach((expr) => {
      expr.element.style.display = "";
    });

    const visibleCount = document.getElementById("visibleCount");
    const totalCount = document.getElementById("totalCount");
    if (visibleCount) {
      visibleCount.textContent = String(this.filteredExpressions.length);
    }
    if (totalCount) {
      totalCount.textContent = String(this.daxExpressions.length);
    }

    const emptyState = document.getElementById("emptyState");
    const daxList = document.getElementById("daxList");

    if (!emptyState || !daxList) {
      return;
    }

    if (this.filteredExpressions.length === 0) {
      emptyState.style.display = "flex";
      daxList.style.display = "none";
    } else {
      emptyState.style.display = "none";
      daxList.style.display = "";
    }
  }

  setCardExpanded(card, expand) {
    card.classList.toggle("expanded", expand);

    const toggleIcon = card.querySelector(".toggle-expand i");
    if (toggleIcon) {
      toggleIcon.className = expand ? "fas fa-chevron-up" : "fas fa-chevron-down";
    }

    const analysisSection = card.querySelector(".measure-analysis");
    if (analysisSection) {
      analysisSection.style.display = expand ? "grid" : "none";
    }

    if (expand) {
      this.populateMeasureAnalysis(card);
    }
  }

  toggleCard(card) {
    const expand = !card.classList.contains("expanded");
    this.setCardExpanded(card, expand);
  }

  toggleAllCards(expand) {
    this.filteredExpressions.forEach((expr) => this.setCardExpanded(expr.element, expand));
  }

  formatDAXCode(card) {
    const codeElement = card.querySelector("code");
    if (!codeElement) {
      return;
    }

    const formattedCode = this.formatDAX(codeElement.textContent || "");
    codeElement.textContent = formattedCode;

    const measure = this.daxExpressions.find((expr) => expr.element === card);
    if (measure) {
      measure.code = formattedCode;
      measure.codeLower = formattedCode.toLowerCase();
      measure.length = formattedCode.length;
    }

    if (window.Prism && typeof window.Prism.highlightElement === "function") {
      window.Prism.highlightElement(codeElement);
    }

    this.applyFiltersAndSearch();
    this.showNotification("DAX code formatted", "success");
  }

  formatDAX(code) {
    let formatted = code;
    formatted = formatted.replace(/,(?![^\(]*\))/g, ",\n    ");
    formatted = formatted.replace(/(\s*)RETURN/gi, "\n$1RETURN");
    formatted = formatted.replace(/VAR\s+(\w+)\s*=/gi, "VAR $1 =");
    formatted = formatted.replace(/(VAR\s+\w+\s*=.*?)(?=VAR|RETURN|$)/gi, "$1\n");
    formatted = formatted.replace(/CALCULATE\s*\(/gi, "CALCULATE(\n    ");
    formatted = formatted.replace(/\n\s*\n/g, "\n");
    return formatted.trim();
  }
  analyzeMeasureDependencies(card) {
    if (!card.classList.contains("expanded")) {
      this.setCardExpanded(card, true);
    }

    const summary = this.populateMeasureAnalysis(card);
    if (!summary) {
      return;
    }

    this.showNotification(
      `Dependencies analyzed: ${summary.references} references, ${summary.referencedBy} dependents.`,
      "info",
      4000
    );
  }

  populateMeasureAnalysis(card) {
    const measureName = card.getAttribute("data-measure");
    const measure = this.daxExpressions.find((expr) => expr.name === measureName);
    if (!measure) {
      return null;
    }

    const functions = this.extractFunctions(measure.code);
    const references = this.findReferencedMeasures(measure.code);
    const referencedBy = this.findMeasuresReferencingThis(measureName);

    const functionContainer = card.querySelector(".function-tags");
    const referenceContainer = card.querySelector(".reference-list");

    if (functionContainer) {
      functionContainer.replaceChildren();
      if (functions.length) {
        functions.forEach((fnName) => {
          const tag = document.createElement("span");
          tag.className = "function-tag";
          tag.textContent = fnName;
          functionContainer.append(tag);
        });
      } else {
        const empty = document.createElement("span");
        empty.className = "no-references";
        empty.textContent = "No DAX functions detected.";
        functionContainer.append(empty);
      }
    }

    if (referenceContainer) {
      referenceContainer.replaceChildren();
      if (references.length || referencedBy.length) {
        references.forEach((refName) => {
          const tag = document.createElement("span");
          tag.className = "reference-item";
          tag.textContent = `Uses [${refName}]`;
          referenceContainer.append(tag);
        });

        referencedBy.forEach((refName) => {
          const tag = document.createElement("span");
          tag.className = "reference-item";
          tag.textContent = `Used by [${refName}]`;
          referenceContainer.append(tag);
        });
      } else {
        const empty = document.createElement("span");
        empty.className = "no-references";
        empty.textContent = "No measure dependencies detected.";
        referenceContainer.append(empty);
      }
    }

    return {
      references: references.length,
      referencedBy: referencedBy.length,
    };
  }

  extractFunctions(code) {
    const functionPattern = /\b([A-Z][A-Z0-9]*(?:\.[A-Z][A-Z0-9]*)?)\s*\(/g;
    const functions = new Set();
    let match;

    while ((match = functionPattern.exec(code)) !== null) {
      functions.add(match[1]);
    }

    return Array.from(functions).slice(0, 5);
  }

  findReferencedMeasures(code) {
    const references = new Set();
    const measurePattern = /\[([^\[\]]+)\]/g;
    let match;

    while ((match = measurePattern.exec(code)) !== null) {
      const referencedName = this.measureNameLookup.get(match[1].toLowerCase());
      if (referencedName) {
        references.add(referencedName);
      }
    }

    return Array.from(references);
  }

  findMeasuresReferencingThis(measureName) {
    const referencedBy = [];
    const pattern = new RegExp(`\\[${this.escapeRegExp(measureName)}\\]`, "i");

    this.daxExpressions.forEach((expr) => {
      if (expr.name !== measureName && pattern.test(expr.code)) {
        referencedBy.push(expr.name);
      }
    });

    return referencedBy;
  }

  showSimilarityAnalysis() {
    const modal = document.getElementById("similarityModal");
    if (modal) {
      modal.style.display = "flex";
    }
    this.startSimilarityAnalysis();
  }

  hideSimilarityAnalysis() {
    const modal = document.getElementById("similarityModal");
    if (modal) {
      modal.style.display = "none";
    }
    if (this.similarityTask.running) {
      this.cancelSimilarityAnalysis(true);
    }
  }

  startSimilarityAnalysis() {
    if (this.similarityTask.running) {
      return;
    }

    const totalPairs = this.getTotalPairCount();
    this.similarityResults = [];
    this.similarityTask = {
      running: true,
      cancelled: false,
      totalPairs,
      processedPairs: 0,
      i: 0,
      j: 1,
      results: [],
      highestSimilarity: 0,
    };

    this.toggleSimilarityRunControls(true);
    this.updateSimilarityStats(totalPairs, 0, 0);
    this.updateSimilarityProgress(`Analyzing 0 / ${totalPairs.toLocaleString()} pairs`, "running");
    this.renderSimilarityMessage("Analysis in progress...");

    if (totalPairs === 0) {
      this.finishSimilarityAnalysis(false);
      return;
    }

    window.requestAnimationFrame(() => this.processSimilarityChunk());
  }

  processSimilarityChunk() {
    const task = this.similarityTask;
    if (!task.running) {
      return;
    }

    if (task.cancelled) {
      this.finishSimilarityAnalysis(true);
      return;
    }

    const startedAt = performance.now();
    const totalMeasures = this.daxExpressions.length;

    while (task.i < totalMeasures - 1) {
      if (task.j >= totalMeasures) {
        task.i += 1;
        task.j = task.i + 1;
        continue;
      }

      const left = this.daxExpressions[task.i];
      const right = this.daxExpressions[task.j];
      const similarity = this.calculateSimilarity(left.code, right.code);

      task.highestSimilarity = Math.max(task.highestSimilarity, similarity);
      task.processedPairs += 1;

      if (similarity >= 0.5) {
        task.results.push({
          measure1: left.name,
          measure2: right.name,
          code1: left.code,
          code2: right.code,
          similarity,
        });
      }

      task.j += 1;

      if (task.cancelled || performance.now() - startedAt >= this.similarityChunkBudgetMs) {
        break;
      }
    }

    this.updateSimilarityProgressFromTask(task);

    if (task.cancelled) {
      this.finishSimilarityAnalysis(true);
      return;
    }

    if (task.i >= totalMeasures - 1) {
      this.finishSimilarityAnalysis(false);
      return;
    }

    window.requestAnimationFrame(() => this.processSimilarityChunk());
  }

  updateSimilarityProgressFromTask(task) {
    const percentage = task.totalPairs
      ? Math.round((task.processedPairs / task.totalPairs) * 100)
      : 100;

    this.updateSimilarityProgress(
      `Analyzing ${task.processedPairs.toLocaleString()} / ${task.totalPairs.toLocaleString()} pairs (${percentage}%)`,
      "running"
    );
  }

  finishSimilarityAnalysis(cancelled) {
    const task = this.similarityTask;
    task.running = false;

    this.similarityResults = [...task.results].sort((a, b) => b.similarity - a.similarity);
    this.toggleSimilarityRunControls(false);

    const threshold = this.getSimilarityThreshold();
    this.updateSimilarityDisplay(threshold);

    if (cancelled) {
      const percentage = task.totalPairs
        ? Math.round((task.processedPairs / task.totalPairs) * 100)
        : 100;
      this.updateSimilarityProgress(`Cancelled at ${percentage}%`, "cancelled");
      this.showNotification("Similarity analysis cancelled. Showing partial results.", "warning");
    } else {
      this.updateSimilarityProgress("Analysis complete", "complete");
      this.showNotification("Similarity analysis completed.", "success");
    }
  }

  cancelSimilarityAnalysis(silent = false) {
    if (!this.similarityTask.running) {
      return;
    }

    this.similarityTask.cancelled = true;
    this.updateSimilarityProgress("Cancelling...", "running");

    if (!silent) {
      this.showNotification("Stopping similarity analysis...", "info", 1800);
    }
  }
  calculateSimilarity(code1, code2) {
    const normalize = (code) =>
      code
        .replace(/\/\/.*$/gm, "")
        .replace(/\s+/g, " ")
        .toLowerCase()
        .trim();

    const normalizedCode1 = normalize(code1);
    const normalizedCode2 = normalize(code2);

    const maxLen = Math.max(normalizedCode1.length, normalizedCode2.length);
    if (maxLen === 0) {
      return 1;
    }

    const lengthRatio = Math.min(normalizedCode1.length, normalizedCode2.length) / maxLen;
    if (lengthRatio < 0.5) {
      return lengthRatio;
    }

    const tokens1 = this.tokenizeDAX(normalizedCode1);
    const tokens2 = this.tokenizeDAX(normalizedCode2);
    const set1 = new Set(tokens1);
    const set2 = new Set(tokens2);

    const intersectionSize = [...set1].filter((token) => set2.has(token)).length;
    const unionSize = new Set([...set1, ...set2]).size;
    const jaccardSimilarity = unionSize === 0 ? 0 : intersectionSize / unionSize;

    const levenshteinDistance = this.levenshteinDistance(normalizedCode1, normalizedCode2);
    const levenshteinSimilarity = 1 - levenshteinDistance / maxLen;

    return jaccardSimilarity * 0.6 + levenshteinSimilarity * 0.4;
  }

  tokenizeDAX(code) {
    return code.match(/\b\w+\b/g) || [];
  }

  levenshteinDistance(str1, str2) {
    const matrix = Array(str2.length + 1)
      .fill(null)
      .map(() => Array(str1.length + 1).fill(0));

    for (let i = 0; i <= str2.length; i += 1) {
      matrix[i][0] = i;
    }
    for (let j = 0; j <= str1.length; j += 1) {
      matrix[0][j] = j;
    }

    for (let i = 1; i <= str2.length; i += 1) {
      for (let j = 1; j <= str1.length; j += 1) {
        if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j] + 1
          );
        }
      }
    }

    return matrix[str2.length][str1.length];
  }

  updateSimilarityThreshold(event) {
    const sliderValue = event?.target?.value || "70";
    const thresholdValue = document.getElementById("thresholdValue");
    if (thresholdValue) {
      thresholdValue.textContent = `${sliderValue}%`;
    }

    if (this.similarityTask.running) {
      return;
    }

    this.updateSimilarityDisplay(this.getSimilarityThreshold());
  }

  updateSimilarityDisplay(threshold) {
    const indexedResults = [];
    this.similarityResults.forEach((result, index) => {
      if (result.similarity >= threshold) {
        indexedResults.push({ result, index });
      }
    });

    const highestSimilarity = this.similarityResults.length
      ? Math.round(this.similarityResults[0].similarity * 100)
      : 0;

    this.updateSimilarityStats(this.getTotalPairCount(), indexedResults.length, highestSimilarity);
    this.renderSimilarityResults(indexedResults, threshold);
  }

  renderSimilarityResults(indexedResults, threshold) {
    const grid = document.getElementById("similarityGrid");
    if (!grid) {
      return;
    }

    grid.replaceChildren();

    if (!indexedResults.length) {
      this.renderSimilarityMessage(`No measures found with similarity above ${Math.round(threshold * 100)}%`);
      return;
    }

    const fragment = document.createDocumentFragment();
    indexedResults.forEach(({ result, index }) => {
      fragment.append(this.createSimilarityCard(result, index));
    });

    grid.append(fragment);
  }

  renderSimilarityMessage(message) {
    const grid = document.getElementById("similarityGrid");
    if (!grid) {
      return;
    }

    grid.replaceChildren();

    const empty = document.createElement("div");
    empty.className = "no-similar-measures";
    empty.textContent = message;
    grid.append(empty);
  }

  createSimilarityCard(result, resultIndex) {
    const card = document.createElement("div");
    card.className = "similarity-card";

    const header = document.createElement("div");
    header.className = "similarity-header";

    const measures = document.createElement("div");
    measures.className = "similarity-measures";

    const measure1 = document.createElement("span");
    measure1.className = "measure-1";
    measure1.textContent = result.measure1;

    const swapIcon = document.createElement("i");
    swapIcon.className = "fas fa-exchange-alt";
    swapIcon.setAttribute("aria-hidden", "true");

    const measure2 = document.createElement("span");
    measure2.className = "measure-2";
    measure2.textContent = result.measure2;

    measures.append(measure1, swapIcon, measure2);

    const score = document.createElement("div");
    score.className = `similarity-score ${this.getSimilarityClass(result.similarity)}`;
    score.textContent = `${Math.round(result.similarity * 100)}%`;

    header.append(measures, score);

    const actions = document.createElement("div");
    actions.className = "similarity-actions";
    actions.append(
      this.createSimilarityActionButton("compare", "fa-columns", "Compare", resultIndex),
      this.createSimilarityActionButton("highlight", "fa-highlighter", "Highlight", resultIndex)
    );

    card.append(header, actions);
    return card;
  }

  createSimilarityActionButton(action, iconClass, label, resultIndex) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "action-button outline small";
    button.dataset.action = action;
    button.dataset.index = String(resultIndex);

    const icon = document.createElement("i");
    icon.className = `fas ${iconClass}`;
    icon.setAttribute("aria-hidden", "true");

    button.append(icon, document.createTextNode(` ${label}`));
    return button;
  }

  getSimilarityClass(similarity) {
    if (similarity >= 0.9) {
      return "very-high";
    }
    if (similarity >= 0.8) {
      return "high";
    }
    if (similarity >= 0.7) {
      return "medium";
    }
    return "low";
  }

  compareMeasures(index) {
    const result = this.similarityResults[index];
    if (!result) {
      return;
    }

    const score = Math.round(result.similarity * 100);
    this.highlightMeasures(result.measure1, result.measure2);
    this.showNotification(
      `Highlighted ${result.measure1} and ${result.measure2} (${score}% similarity).`,
      "info",
      5000
    );
  }

  highlightMeasures(measure1, measure2) {
    this.hideSimilarityAnalysis();
    this.clearAllFilters();

    let firstMatchCard = null;
    this.daxExpressions.forEach((expr) => {
      if (expr.name === measure1 || expr.name === measure2) {
        expr.element.classList.add("highlighted");
        expr.element.classList.remove("dimmed");
        this.setCardExpanded(expr.element, true);
        if (!firstMatchCard) {
          firstMatchCard = expr.element;
        }
      } else {
        expr.element.classList.remove("highlighted");
        expr.element.classList.add("dimmed");
      }
    });

    if (firstMatchCard) {
      firstMatchCard.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    if (this.highlightResetTimer) {
      clearTimeout(this.highlightResetTimer);
    }

    this.highlightResetTimer = setTimeout(() => {
      document.querySelectorAll(".dax-card").forEach((card) => {
        card.classList.remove("highlighted", "dimmed");
      });
      this.highlightResetTimer = null;
    }, 5000);
  }
  updateSimilarityStats(totalPairs, similarPairs, highestPercent) {
    const totalPairsElement = document.getElementById("totalPairs");
    const similarPairsElement = document.getElementById("similarPairsCount");
    const highestElement = document.getElementById("highestSimilarityValue");

    if (totalPairsElement) {
      totalPairsElement.textContent = Number(totalPairs || 0).toLocaleString();
    }
    if (similarPairsElement) {
      similarPairsElement.textContent = Number(similarPairs || 0).toLocaleString();
    }
    if (highestElement) {
      highestElement.textContent = `${Math.max(0, Number(highestPercent || 0))}%`;
    }
  }

  updateSimilarityProgress(message, state) {
    const progress = document.getElementById("similarityProgress");
    if (!progress) {
      return;
    }

    progress.textContent = message;
    progress.classList.remove("running", "complete", "cancelled");
    if (state === "running") {
      progress.classList.add("running");
    } else if (state === "complete") {
      progress.classList.add("complete");
    } else if (state === "cancelled") {
      progress.classList.add("cancelled");
    }
  }

  toggleSimilarityRunControls(running) {
    const cancelButton = document.getElementById("cancelSimilarity");
    const analyzeButton = document.getElementById("analyzeSimilarity");
    const exportButton = document.getElementById("exportSimilarity");

    if (cancelButton) {
      cancelButton.disabled = !running;
    }
    if (analyzeButton) {
      analyzeButton.disabled = running;
    }
    if (exportButton) {
      exportButton.disabled = running;
    }
  }

  getTotalPairCount() {
    const n = this.daxExpressions.length;
    return (n * (n - 1)) / 2;
  }

  getSimilarityThreshold() {
    const rawValue = document.getElementById("similarityThreshold")?.value || "70";
    const numeric = Number.parseInt(rawValue, 10);
    return (Number.isFinite(numeric) ? numeric : 70) / 100;
  }

  exportSimilarityResults() {
    const threshold = this.getSimilarityThreshold();
    const results = this.similarityResults.filter((result) => result.similarity >= threshold);
    if (!results.length) {
      this.showNotification("No similarity results to export at the current threshold.", "warning");
      return;
    }

    const rows = [
      ["Measure 1", "Measure 2", "Similarity %"],
      ...results.map((result) => [
        result.measure1,
        result.measure2,
        Math.round(result.similarity * 100),
      ]),
    ];

    const csv = this.rowsToCSV(rows);
    this.downloadFile(csv, "dax_similarity_analysis.csv", "text/csv;charset=utf-8");
  }

  exportDAX() {
    const data = this.filteredExpressions.map((expr) => ({
      "Measure Name": expr.name,
      "DAX Expression": expr.code,
    }));

    const csv = this.arrayToCSV(data);
    this.downloadFile(csv, "dax_expressions.csv", "text/csv;charset=utf-8");
    this.showNotification("DAX expressions exported successfully", "success");
  }

  clearAllFilters() {
    const searchInput = document.getElementById("searchDax");
    const clearSearch = document.getElementById("clearSearch");
    const functionFilter = document.getElementById("functionFilter");
    const searchInCode = document.getElementById("searchInCode");
    const caseSensitive = document.getElementById("caseSensitive");

    if (searchInput) {
      searchInput.value = "";
    }
    if (clearSearch) {
      clearSearch.style.display = "none";
    }
    if (functionFilter) {
      functionFilter.value = "all";
    }
    if (searchInCode) {
      searchInCode.checked = true;
    }
    if (caseSensitive) {
      caseSensitive.checked = false;
    }

    this.clearHighlights();
    this.applyFiltersAndSearch();
  }

  copyToClipboard(text, label) {
    const onSuccess = () => this.showNotification(`${label} copied to clipboard`, "success");

    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      navigator.clipboard.writeText(text).then(onSuccess).catch(() => {
        this.copyToClipboardFallback(text, onSuccess);
      });
      return;
    }

    this.copyToClipboardFallback(text, onSuccess);
  }

  copyToClipboardFallback(text, onSuccess) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
    onSuccess();
  }

  showNotification(message, type = "info", duration = 3000) {
    if (window.PowerBIExplorer && typeof window.PowerBIExplorer.showNotification === "function") {
      window.PowerBIExplorer.showNotification(message, type, duration);
      return;
    }
    console.log(`${type}: ${message}`);
  }

  downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  csvEscape(value) {
    const text = value === null || value === undefined ? "" : String(value);
    if (/[",\r\n]/.test(text)) {
      return `"${text.replace(/"/g, '""')}"`;
    }
    return text;
  }

  rowsToCSV(rows) {
    return rows.map((row) => row.map((value) => this.csvEscape(value)).join(",")).join("\r\n");
  }

  arrayToCSV(data) {
    if (!data.length) {
      return "";
    }

    const headers = Object.keys(data[0]);
    const rows = [headers, ...data.map((row) => headers.map((header) => row[header] ?? ""))];
    return this.rowsToCSV(rows);
  }

  escapeRegExp(text) {
    return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  debounce(func, wait) {
    let timeout;
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func(...args), wait);
    };
  }

  applyInitialHighlighting() {
    if (window.Prism && typeof window.Prism.highlightAll === "function") {
      window.Prism.highlightAll();
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.daxExplorer = new DAXExplorer();
});
