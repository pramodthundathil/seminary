// ---------- Timezone List (Limited curated set) ----------
window.TIMEZONE_LIST = [
    "UTC-12:00",
    "UTC-11:00",
    "UTC-10:00",
    "UTC-09:00",
    "UTC-08:00",
    "UTC-07:00",
    "UTC-06:00",
    "UTC-05:00",
    "UTC-04:00",
    "UTC-03:00",
    "UTC-02:00",
    "UTC-01:00",
    "UTC+00:00",
    "UTC+01:00",
    "UTC+02:00",
    "UTC+03:00",
    "UTC+04:00",
    "UTC+05:00",
    "UTC+05:30",
    "UTC+06:00",
    "UTC+07:00",
    "UTC+08:00",
    "UTC+09:00",
    "UTC+10:00",
    "UTC+11:00",
    "UTC+12:00"
];

const TIMEZONE_LABELS = {
    "UTC-12:00": "(UTC-12:00) International Date Line West",
    "UTC-11:00": "(UTC-11:00) Coordinated Universal Time-11",
    "UTC-10:00": "(UTC-10:00) Hawaii",
    "UTC-09:00": "(UTC-09:00) Alaska",
    "UTC-08:00": "(UTC-08:00) Pacific Time (US & Canada)",
    "UTC-07:00": "(UTC-07:00) Mountain Time (US & Canada)",
    "UTC-06:00": "(UTC-06:00) Central Time (US & Canada)",
    "UTC-05:00": "(UTC-05:00) Eastern Time (US & Canada)",
    "UTC-04:00": "(UTC-04:00) Atlantic Time (Canada)",
    "UTC-03:00": "(UTC-03:00) Buenos Aires",
    "UTC-02:00": "(UTC-02:00) Mid-Atlantic",
    "UTC-01:00": "(UTC-01:00) Azores",
    "UTC+00:00": "(UTC+00:00) Dublin, London",
    "UTC+01:00": "(UTC+01:00) Amsterdam, Berlin, Paris",
    "UTC+02:00": "(UTC+02:00) Athens, Istanbul",
    "UTC+03:00": "(UTC+03:00) Moscow, St. Petersburg",
    "UTC+04:00": "(UTC+04:00) Abu Dhabi, Muscat",
    "UTC+05:00": "(UTC+05:00) Islamabad, Karachi",
    "UTC+05:30": "(UTC+05:30) India Standard Time",
    "UTC+06:00": "(UTC+06:00) Dhaka",
    "UTC+07:00": "(UTC+07:00) Bangkok, Hanoi",
    "UTC+08:00": "(UTC+08:00) Beijing, Singapore",
    "UTC+09:00": "(UTC+09:00) Tokyo, Seoul",
    "UTC+10:00": "(UTC+10:00) Sydney",
    "UTC+11:00": "(UTC+11:00) Solomon Islands",
    "UTC+12:00": "(UTC+12:00) Auckland, Wellington"
};

// Map old tz format/aliases to UTC format for compatibility
const TIMEZONE_MAPPING_ALIASES = {
    "UTC": "UTC+00:00",
    "GMT": "UTC+00:00",
    "Asia/Kolkata": "UTC+05:30",
    "Asia/Calcutta": "UTC+05:30",
    "Asia/Dubai": "UTC+04:00",
    "Asia/Singapore": "UTC+08:00",
    "Europe/London": "UTC+00:00",
    "America/New_York": "UTC-05:00",
    "America/Chicago": "UTC-06:00",
    "America/Denver": "UTC-07:00",
    "America/Los_Angeles": "UTC-08:00",
    "Africa/Nairobi": "UTC+03:00",
    "Australia/Sydney": "UTC+10:00"
};

// Inject CSS styles for the themed searchable dropdown
function injectDropdownStyles() {
    if (document.getElementById("custom-tz-styles")) return;

    const styles = `
        .custom-tz-container {
            position: relative;
            width: 100%;
            font-family: inherit;
            box-sizing: border-box;
        }
        .custom-tz-trigger {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            padding: 0.625rem 0.75rem;
            font-size: 0.875rem;
            font-weight: 500;
            color: #1e293b;
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 0.375rem;
            cursor: pointer;
            text-align: left;
            transition: all 0.2s;
            box-sizing: border-box;
        }
        .custom-tz-trigger:focus, .custom-tz-container.open .custom-tz-trigger {
            outline: none;
            border-color: #00CED1;
            box-shadow: 0 0 0 3px rgba(0, 206, 209, 0.15);
        }
        .custom-tz-trigger-text {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .custom-tz-arrow {
            width: 0;
            height: 0;
            margin-left: 8px;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #64748b;
            transition: transform 0.2s ease;
            flex-shrink: 0;
        }
        .custom-tz-container.open .custom-tz-arrow {
            transform: rotate(180deg);
        }
        .custom-tz-dropdown {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            z-index: 99999;
            display: none;
            margin-top: 4px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 0.5rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            overflow: hidden;
            animation: tzFadeIn 0.15s ease-out;
        }
        @keyframes tzFadeIn {
            from { opacity: 0; transform: translateY(-4px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .custom-tz-container.open .custom-tz-dropdown {
            display: block;
        }
        .custom-tz-search-box {
            display: flex;
            align-items: center;
            padding: 8px 12px;
            border-bottom: 1px solid #e2e8f0;
            background: #f8fafc;
        }
        .custom-tz-search-icon {
            width: 16px;
            height: 16px;
            fill: #94a3b8;
            margin-right: 8px;
            flex-shrink: 0;
        }
        .custom-tz-search-input {
            width: 100%;
            border: none;
            background: transparent;
            font-size: 0.875rem;
            color: #1e293b;
            outline: none;
            padding: 4px 0;
        }
        .custom-tz-options {
            list-style: none;
            margin: 0;
            padding: 4px 0;
            max-height: 200px;
            overflow-y: auto;
        }
        .custom-tz-options::-webkit-scrollbar {
            width: 6px;
        }
        .custom-tz-options::-webkit-scrollbar-track {
            background: #f1f5f9;
        }
        .custom-tz-options::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 3px;
        }
        .custom-tz-options::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }
        .custom-tz-option {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 12px;
            font-size: 0.875rem;
            color: #334155;
            cursor: pointer;
            transition: background 0.15s;
        }
        .custom-tz-option:hover {
            background: #f1f5f9;
            color: #1e293b;
        }
        .custom-tz-option.selected {
            background: #E0F7F7;
            color: #00CED1;
            font-weight: 600;
        }
        .custom-tz-option-check {
            display: none;
            color: #00CED1;
            font-weight: bold;
            font-size: 0.875rem;
        }
        .custom-tz-option.selected .custom-tz-option-check {
            display: block;
        }
        .custom-tz-no-results {
            padding: 12px;
            text-align: center;
            font-size: 0.875rem;
            color: #94a3b8;
            display: none;
        }
        .custom-tz-hidden-select {
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
            opacity: 0 !important;
        }
        /* Page form layout size adapters */
        .form-select + .custom-tz-container .custom-tz-trigger,
        .form-control + .custom-tz-container .custom-tz-trigger {
            padding: 12px 16px;
            height: 50px;
            border-radius: 8px;
            font-size: 15px;
            color: #374151;
            border-color: #d1d5db;
        }
        .form-control-custom + .custom-tz-container .custom-tz-trigger {
            padding: 11px 14px;
            border-radius: 10px;
            font-size: 0.9rem;
            color: #1e293b;
            background-color: #f8fafc;
            border-color: #cbd5e1;
        }
        /* Prevent clipping in Bootstrap modals and elevate active container */
        .modal-body {
            position: relative !important;
            z-index: 1055 !important;
            overflow: visible !important;
        }
        .modal-content {
            overflow: visible !important;
        }
        .custom-tz-container.open {
            z-index: 99999 !important;
        }
        /* Elevate all ancestors of the open custom timezone dropdown to prevent grid stacking issues */
        .modal-body:has(.custom-tz-container.open),
        .row:has(.custom-tz-container.open),
        .col-md-6:has(.custom-tz-container.open),
        .col-md-4:has(.custom-tz-container.open),
        .form-group:has(.custom-tz-container.open) {
            position: relative !important;
            z-index: 99999 !important;
            overflow: visible !important;
        }
    `;

    const styleEl = document.createElement("style");
    styleEl.id = "custom-tz-styles";
    styleEl.textContent = styles;
    document.head.appendChild(styleEl);
}

// Transform regular select to premium searchable dropdown
function createSearchableDropdown(selectEl) {
    if (selectEl.dataset.tzDropdownInitialized === "true") return;
    selectEl.dataset.tzDropdownInitialized = "true";

    // Read initial selection or pre-selected values
    let selectedVal = selectEl.value;
    if (!selectedVal) {
        const parent = selectEl.closest("div") || selectEl.parentNode;
        const hiddenInput = parent ? parent.querySelector('#selected_timezone, input[type="hidden"]') : null;
        if (hiddenInput && hiddenInput.value) {
            selectedVal = hiddenInput.value;
        }
    }

    if (selectedVal && typeof selectedVal === 'string') {
        selectedVal = selectedVal.trim();
    }

    // Aliases normalization
    if (selectedVal && TIMEZONE_MAPPING_ALIASES[selectedVal]) {
        selectedVal = TIMEZONE_MAPPING_ALIASES[selectedVal];
    }

    // Empty and populate selectEl with target offset options
    selectEl.innerHTML = "";
    const defaultOpt = document.createElement("option");
    defaultOpt.value = "";
    defaultOpt.textContent = selectEl.getAttribute("placeholder") || "--- Select Timezone ---";
    selectEl.appendChild(defaultOpt);

    window.TIMEZONE_LIST.forEach(tzVal => {
        const option = document.createElement("option");
        option.value = tzVal;
        option.textContent = TIMEZONE_LABELS[tzVal];
        if (selectedVal === tzVal) {
            option.selected = true;
        }
        selectEl.appendChild(option);
    });

    if (selectedVal) {
        selectEl.value = selectedVal;
    }


    // Create wrapper container
    const container = document.createElement("div");
    container.className = "custom-tz-container";

    // Create trigger button
    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "custom-tz-trigger";

    const triggerText = document.createElement("span");
    triggerText.className = "custom-tz-trigger-text";
    triggerText.textContent = TIMEZONE_LABELS[selectedVal] || defaultOpt.textContent;
    trigger.appendChild(triggerText);

    const arrow = document.createElement("span");
    arrow.className = "custom-tz-arrow";
    trigger.appendChild(arrow);
    container.appendChild(trigger);

    // Create dropdown wrapper
    const dropdown = document.createElement("div");
    dropdown.className = "custom-tz-dropdown";

    // Create search input box
    const searchBox = document.createElement("div");
    searchBox.className = "custom-tz-search-box";
    searchBox.innerHTML = `
        <svg class="custom-tz-search-icon" viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
    `;
    const searchInput = document.createElement("input");
    searchInput.type = "text";
    searchInput.className = "custom-tz-search-input";
    searchInput.placeholder = "Search timezone...";
    searchBox.appendChild(searchInput);
    dropdown.appendChild(searchBox);

    // Create options list container
    const optionsList = document.createElement("ul");
    optionsList.className = "custom-tz-options";

    const noResults = document.createElement("div");
    noResults.className = "custom-tz-no-results";
    noResults.textContent = "No timezones found";
    dropdown.appendChild(noResults);

    // Populate the dropdown options
    const optionItems = [];

    // Add default select item
    const defaultItem = document.createElement("li");
    defaultItem.className = `custom-tz-option ${!selectedVal ? "selected" : ""}`;
    defaultItem.dataset.value = "";
    defaultItem.innerHTML = `
        <span>${defaultOpt.textContent}</span>
        <span class="custom-tz-option-check">✓</span>
    `;
    optionsList.appendChild(defaultItem);
    optionItems.push(defaultItem);

    window.TIMEZONE_LIST.forEach(tzVal => {
        const item = document.createElement("li");
        item.className = `custom-tz-option ${selectedVal === tzVal ? "selected" : ""}`;
        item.dataset.value = tzVal;
        item.innerHTML = `
            <span>${TIMEZONE_LABELS[tzVal]}</span>
            <span class="custom-tz-option-check">✓</span>
        `;
        optionsList.appendChild(item);
        optionItems.push(item);
    });

    dropdown.appendChild(optionsList);
    container.appendChild(dropdown);

    // Insert custom container in DOM
    selectEl.classList.add("custom-tz-hidden-select");
    selectEl.parentNode.insertBefore(container, selectEl.nextSibling);

    // Event handler: Trigger click
    trigger.addEventListener("click", (e) => {
        e.stopPropagation();
        const isOpen = container.classList.contains("open");
        
        // Close other custom timezone dropdowns
        document.querySelectorAll(".custom-tz-container").forEach(c => c.classList.remove("open"));

        if (!isOpen) {
            container.classList.add("open");
            searchInput.value = "";
            filterOptions("");
            searchInput.focus();
        }
    });

    // Event handler: Option item click
    optionsList.addEventListener("click", (e) => {
        const item = e.target.closest(".custom-tz-option");
        if (!item) return;

        const val = item.dataset.value;
        const text = item.querySelector("span").textContent;

        // Update selected class
        optionItems.forEach(opt => opt.classList.remove("selected"));
        item.classList.add("selected");

        // Update trigger display
        triggerText.textContent = text;

        // Set value on original select element & trigger events
        selectEl.value = val;
        selectEl.dispatchEvent(new Event("change", { bubbles: true }));
        selectEl.dispatchEvent(new Event("input", { bubbles: true }));

        // Close dropdown
        container.classList.remove("open");
    });

    // Event handler: Search input keypress
    searchInput.addEventListener("input", (e) => {
        filterOptions(e.target.value);
    });

    // Filter timezones dynamically
    function filterOptions(query) {
        query = query.toLowerCase().trim();
        let matchCount = 0;

        optionItems.forEach(item => {
            const text = item.querySelector("span").textContent.toLowerCase();
            if (text.includes(query)) {
                item.style.display = "flex";
                matchCount++;
            } else {
                item.style.display = "none";
            }
        });

        if (matchCount === 0) {
            noResults.style.display = "block";
        } else {
            noResults.style.display = "none";
        }
    }

    // Sync if original select changes externally
    selectEl.addEventListener("change", () => {
        let currentVal = selectEl.value;
        if (currentVal && TIMEZONE_MAPPING_ALIASES[currentVal]) {
            currentVal = TIMEZONE_MAPPING_ALIASES[currentVal];
        }

        const matchedItem = optionItems.find(opt => opt.dataset.value === currentVal);
        if (matchedItem) {
            optionItems.forEach(opt => opt.classList.remove("selected"));
            matchedItem.classList.add("selected");
            triggerText.textContent = matchedItem.querySelector("span").textContent;
        } else if (!currentVal) {
            optionItems.forEach(opt => opt.classList.remove("selected"));
            defaultItem.classList.add("selected");
            triggerText.textContent = defaultItem.querySelector("span").textContent;
        }
    });

    // Listen to form reset if parent is a form
    const form = selectEl.closest("form");
    if (form) {
        form.addEventListener("reset", () => {
            setTimeout(() => {
                let currentVal = selectEl.value;
                if (currentVal && TIMEZONE_MAPPING_ALIASES[currentVal]) {
                    currentVal = TIMEZONE_MAPPING_ALIASES[currentVal];
                }

                const matchedItem = optionItems.find(opt => opt.dataset.value === currentVal);
                if (matchedItem) {
                    optionItems.forEach(opt => opt.classList.remove("selected"));
                    matchedItem.classList.add("selected");
                    triggerText.textContent = matchedItem.querySelector("span").textContent;
                } else {
                    optionItems.forEach(opt => opt.classList.remove("selected"));
                    defaultItem.classList.add("selected");
                    triggerText.textContent = defaultItem.querySelector("span").textContent;
                }
            }, 0);
        });
    }
}

// Scan and setup all timezone elements on page
function setupTimezoneSelects() {
    // Select selectors matching timezone fields
    const selectors = [
        'select[name="timezone"]',
        'select#timezone',
        'select#timezoneSelect',
        'select#editTimezone',
        'select#rescheduleTimezone'
    ].join(",");

    const selectElements = document.querySelectorAll(selectors);
    selectElements.forEach(selectEl => {
        createSearchableDropdown(selectEl);
    });

    // Special check for inputs named timezone to convert them
    const textInputs = document.querySelectorAll('input[type="text"][name="timezone"]');
    textInputs.forEach(inputEl => {
        // Replace text input with select
        const selectEl = document.createElement("select");
        selectEl.name = inputEl.name;
        selectEl.id = inputEl.id || "";
        selectEl.className = inputEl.className;
        selectEl.required = inputEl.required;
        selectEl.value = inputEl.value;

        // Copy styles or placeholders
        if (inputEl.placeholder) selectEl.setAttribute("placeholder", inputEl.placeholder);

        inputEl.parentNode.replaceChild(selectEl, inputEl);
        createSearchableDropdown(selectEl);
    });
}

// Global click handler to close dropdowns when clicking outside
document.addEventListener("click", (e) => {
    if (!e.target.closest(".custom-tz-container")) {
        document.querySelectorAll(".custom-tz-container").forEach(c => c.classList.remove("open"));
    }
});

// Run automatically on page load
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
        injectDropdownStyles();
        setupTimezoneSelects();
    });
} else {
    injectDropdownStyles();
    setupTimezoneSelects();
}

// Expose functions globally for dynamic/AJAX rendering or manual refresh
window.initCustomTimezoneDropdowns = function() {
    setupTimezoneSelects();
};
