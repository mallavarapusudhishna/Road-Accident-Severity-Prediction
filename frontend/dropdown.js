// Reusable searchable dropdown (vanilla JS)
// Replaces native <select> UX with a premium overlay while preserving
// the selected value, option values, name, and form submission compatibility.

class SearchableDropdown {
  constructor(selectEl, options = {}) {
    this.selectEl = selectEl;
    this.options = options;

    this.value = this.selectEl.value;
    this.isOpen = false;
    this.highlightIndex = -1;

    this._build();
    this._syncFromSelect();
    this._attach();
  }

  _build() {
    // Create wrapper (overlay-style)
    this.root = document.createElement("div");
    this.root.className = "sdd-root";

    // Trigger button
    this.trigger = document.createElement("button");
    this.trigger.type = "button";
    this.trigger.className = "sdd-trigger";
    this.trigger.setAttribute("aria-haspopup", "listbox");
    this.trigger.setAttribute("aria-expanded", "false");
    this.trigger.setAttribute("aria-controls", `${this.selectEl.id}-list`);

    // Trigger label
    this.triggerLabel = document.createElement("span");
    this.triggerLabel.className = "sdd-trigger-label";
    this.triggerLabel.textContent = "";

    // Chevron
    const chevron = document.createElement("span");
    chevron.className = "sdd-chevron";
    chevron.textContent = "▾";

    this.trigger.appendChild(this.triggerLabel);
    this.trigger.appendChild(chevron);

    // Searchable overlay
    this.dropdown = document.createElement("div");
    this.dropdown.className = "sdd-dropdown";
    this.dropdown.id = `${this.selectEl.id}-list-wrapper`;
    this.dropdown.setAttribute("role", "dialog");
    this.dropdown.setAttribute(
      "aria-label",
      this.selectEl.name || this.selectEl.id,
    );

    const searchWrap = document.createElement("div");
    searchWrap.className = "sdd-search-wrap";

    this.searchInput = document.createElement("input");
    this.searchInput.type = "text";
    this.searchInput.className = "sdd-search";
    this.searchInput.id = `${this.selectEl.id}-search`;
    this.searchInput.name = `${this.selectEl.id}_search`;
    this.searchInput.placeholder = this.options.placeholder || "Search...";

    searchWrap.appendChild(this.searchInput);

    this.list = document.createElement("div");
    this.list.className = "sdd-list";
    this.list.setAttribute("role", "listbox");
    this.list.id = `${this.selectEl.id}-list`;
    this.list.setAttribute("tabindex", "-1");

    this.optionsEls = [];

    this.dropdown.appendChild(searchWrap);
    this.dropdown.appendChild(this.list);

    // Keep the native select for form compatibility; hide it visually.
    this.selectEl.classList.add("sdd-native-hidden");

    // Insert root where select was
    this.root.appendChild(this.trigger);
    this.root.appendChild(this.dropdown);

    this.selectEl.parentNode.insertBefore(this.root, this.selectEl);
  }

  _attach() {
    // Trigger
    this.trigger.addEventListener("click", e => {
      e.preventDefault();
      this.toggle();
    });

    // Keyboard on trigger
    this.trigger.addEventListener("keydown", e => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        this.open();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        this.open();
      }
    });

    // Search
    this.searchInput.addEventListener("input", () => {
      this._filter();
      this._resetHighlight();
    });

    this.searchInput.addEventListener("keydown", e => {
      if (!this.isOpen) return;

      if (e.key === "Escape") {
        e.preventDefault();
        this.close();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        this._moveHighlight(1);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        this._moveHighlight(-1);
      } else if (e.key === "Enter") {
        e.preventDefault();
        this._commitHighlight();
      }
    });

    // Click outside
    document.addEventListener("mousedown", e => {
      if (!this.isOpen) return;
      if (this.root.contains(e.target)) return;
      this.close();
    });

    // Refresh on select change (if ever)
    this.selectEl.addEventListener("change", () => {
      this._syncFromSelect();
    });

    // Handle form reset automatically
    const form = this.selectEl.form;
    if (form) {
      form.addEventListener("reset", () => {
        setTimeout(() => {
          this._syncFromSelect();
        }, 0);
      });
    }
  }

  _syncFromSelect() {
    this.value = this.selectEl.value;
    const selectedOption = Array.from(this.selectEl.options).find(
      o => o.value === this.value,
    );
    this.triggerLabel.textContent = selectedOption
      ? selectedOption.textContent
      : this.options.placeholder || "Select";

    // Rebuild list once on first sync
    if (this.optionsEls.length === 0) {
      this._renderOptions();
    }

    // set highlight to current selection
    const idx = this._visibleOptions().findIndex(
      o => o.dataset.value === this.value,
    );
    this.highlightIndex = idx >= 0 ? idx : 0;

    this._updatePlaceholderClass();
  }

  _updatePlaceholderClass() {
    if (this.value === "") {
      this.trigger.classList.add("is-placeholder");
    } else {
      this.trigger.classList.remove("is-placeholder");
    }
  }

  _renderOptions() {
    this.list.innerHTML = "";
    this.optionsEls = [];

    const optEls = Array.from(this.selectEl.options);
    for (const opt of optEls) {
      const optionDiv = document.createElement("button");
      optionDiv.type = "button";
      optionDiv.className = "sdd-option";
      optionDiv.setAttribute("role", "option");
      optionDiv.dataset.value = opt.value;
      optionDiv.textContent = opt.textContent;

      if (opt.disabled) optionDiv.setAttribute("aria-disabled", "true");

      optionDiv.addEventListener("click", e => {
        e.preventDefault();
        if (opt.disabled) return;
        this.selectEl.value = opt.value;
        this.selectEl.dispatchEvent(new Event("change", { bubbles: true }));
        this.close();
      });

      this.list.appendChild(optionDiv);
      this.optionsEls.push(optionDiv);
    }

    this._filter();
  }

  _visibleOptions() {
    // optionsEls are buttons; filter by display != none
    return this.optionsEls.filter(el => el.style.display !== "none");
  }

  _filter() {
    const q = (this.searchInput.value || "").trim().toLowerCase();
    for (const optEl of this.optionsEls) {
      const text = optEl.textContent.toLowerCase();
      optEl.style.display = q === "" || text.includes(q) ? "" : "none";
    }
  }

  _resetHighlight() {
    const vis = this._visibleOptions();
    if (!vis.length) {
      this.highlightIndex = -1;
      return;
    }

    // Prefer selected
    const idx = vis.findIndex(el => el.dataset.value === this.value);
    this.highlightIndex = idx >= 0 ? idx : 0;
    this._applyHighlight();
  }

  _applyHighlight() {
    for (const el of this.optionsEls) {
      el.classList.remove("is-highlighted");
      el.setAttribute("aria-selected", "false");
    }

    const vis = this._visibleOptions();
    if (this.highlightIndex < 0 || this.highlightIndex >= vis.length) return;
    const active = vis[this.highlightIndex];
    active.classList.add("is-highlighted");
    active.setAttribute("aria-selected", "true");

    // Ensure in view
    active.scrollIntoView({ block: "nearest" });
  }

  _moveHighlight(delta) {
    const vis = this._visibleOptions();
    if (!vis.length) return;

    let next = this.highlightIndex;
    if (next < 0) next = 0;
    next += delta;
    if (next < 0) next = vis.length - 1;
    if (next >= vis.length) next = 0;
    this.highlightIndex = next;
    this._applyHighlight();
  }

  _commitHighlight() {
    const vis = this._visibleOptions();
    if (!vis.length || this.highlightIndex < 0) return;
    const chosen = vis[this.highlightIndex];
    const val = chosen.dataset.value;

    this.selectEl.value = val;
    this.selectEl.dispatchEvent(new Event("change", { bubbles: true }));
    this.close();
  }

  open() {
    if (this.isOpen) return;
    this.isOpen = true;
    this.dropdown.classList.add("is-open");
    this.trigger.setAttribute("aria-expanded", "true");

    this.searchInput.value = "";
    this._filter();
    this._resetHighlight();

    // Focus search
    setTimeout(() => {
      try {
        this.searchInput.focus();
      } catch {}
    }, 0);
  }

  close() {
    if (!this.isOpen) return;
    this.isOpen = false;
    this.dropdown.classList.remove("is-open");
    this.trigger.setAttribute("aria-expanded", "false");
  }

  toggle() {
    this.isOpen ? this.close() : this.open();
  }
}

function initSearchableDropdowns() {
  const selects = document.querySelectorAll("select.a11y-select");
  selects.forEach(sel => {
    // avoid double-init
    if (sel.dataset.sddInited === "1") return;
    sel.dataset.sddInited = "1";

    const placeholder = sel.id === "state" ? "Search state..." : "Search...";
    new SearchableDropdown(sel, { placeholder });
  });
}

window.addEventListener("DOMContentLoaded", () => {
  if (!document.querySelector("select.a11y-select")) return;
  initSearchableDropdowns();
});
