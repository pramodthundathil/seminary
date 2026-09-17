// ---------- Comprehensive DST-Aware Timezone List ----------
window.TIMEZONE_LIST = [
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Phoenix",
    "America/Los_Angeles",
    "America/Anchorage",
    "Pacific/Honolulu",
    "America/Halifax",
    "America/St_Johns",
    "America/Puerto_Rico",
    "America/Mexico_City",
    "America/Bogota",
    "America/Lima",
    "America/Sao_Paulo",
    "America/Argentina/Buenos_Aires",
    "America/Santiago",
    "Europe/London",
    "Europe/Lisbon",
    "Europe/Paris",
    "Europe/Helsinki",
    "Europe/Istanbul",
    "Europe/Moscow",
    "Africa/Abidjan",
    "Africa/Lagos",
    "Africa/Cairo",
    "Africa/Johannesburg",
    "Africa/Nairobi",
    "Asia/Jerusalem",
    "Asia/Riyadh",
    "Asia/Kuwait",
    "Asia/Tehran",
    "Asia/Dubai",
    "Asia/Kabul",
    "Asia/Karachi",
    "Asia/Yekaterinburg",
    "Asia/Kolkata",
    "Asia/Colombo",
    "Asia/Kathmandu",
    "Asia/Dhaka",
    "Asia/Rangoon",
    "Asia/Bangkok",
    "Asia/Singapore",
    "Asia/Manila",
    "Asia/Shanghai",
    "Asia/Taipei",
    "Asia/Hong_Kong",
    "Asia/Seoul",
    "Asia/Tokyo",
    "Australia/Perth",
    "Australia/Darwin",
    "Australia/Adelaide",
    "Australia/Sydney",
    "Australia/Brisbane",
    "Pacific/Auckland",
    "Pacific/Fiji",
    "UTC"
];

const TIMEZONE_LABELS = {
    "America/New_York": "(UTC-5/-4) US/Canada Eastern — New York, Toronto, Miami, Boston",
    "America/Chicago": "(UTC-6/-5) US/Canada Central — Chicago, Dallas, Houston, Winnipeg",
    "America/Denver": "(UTC-7/-6) US/Canada Mountain — Denver, Calgary, Salt Lake City",
    "America/Phoenix": "(UTC-7) US Mountain (no DST) — Phoenix, Arizona",
    "America/Los_Angeles": "(UTC-8/-7) US/Canada Pacific — Los Angeles, Seattle, Vancouver",
    "America/Anchorage": "(UTC-9/-8) US Alaska — Anchorage",
    "Pacific/Honolulu": "(UTC-10) US Hawaii — Honolulu",
    "America/Halifax": "(UTC-4/-3) Canada Atlantic — Halifax, Moncton",
    "America/St_Johns": "(UTC-3:30/-2:30) Canada Newfoundland — St. John's",
    "America/Puerto_Rico": "(UTC-4) Caribbean — Puerto Rico, US Virgin Islands",
    "America/Mexico_City": "(UTC-6/-5) Mexico Central — Mexico City, Guadalajara",
    "America/Bogota": "(UTC-5) Colombia — Bogotá, Medellín",
    "America/Lima": "(UTC-5) Peru — Lima",
    "America/Sao_Paulo": "(UTC-3/-2) Brazil — São Paulo, Rio de Janeiro, Brasília",
    "America/Argentina/Buenos_Aires": "(UTC-3) Argentina — Buenos Aires",
    "America/Santiago": "(UTC-4/-3) Chile — Santiago",
    "Europe/London": "(UTC+0/+1) UK & Ireland — London, Dublin, Edinburgh",
    "Europe/Lisbon": "(UTC+0/+1) Portugal — Lisbon",
    "Europe/Paris": "(UTC+1/+2) Central Europe — Paris, Berlin, Rome, Madrid, Amsterdam",
    "Europe/Helsinki": "(UTC+2/+3) Eastern Europe — Helsinki, Athens, Kyiv, Tallinn",
    "Europe/Istanbul": "(UTC+3) Turkey — Istanbul, Ankara",
    "Europe/Moscow": "(UTC+3) Russia — Moscow, St. Petersburg",
    "Africa/Abidjan": "(UTC+0) West Africa (no DST) — Accra, Dakar, Abidjan",
    "Africa/Lagos": "(UTC+1) West/Central Africa — Lagos, Kinshasa",
    "Africa/Cairo": "(UTC+2) Egypt — Cairo, Alexandria",
    "Africa/Johannesburg": "(UTC+2) South Africa — Johannesburg, Cape Town",
    "Africa/Nairobi": "(UTC+3) East Africa — Nairobi, Addis Ababa, Dar es Salaam",
    "Asia/Jerusalem": "(UTC+2/+3) Israel — Jerusalem, Tel Aviv",
    "Asia/Riyadh": "(UTC+3) Saudi Arabia — Riyadh, Jeddah, Mecca",
    "Asia/Kuwait": "(UTC+3) Kuwait, Bahrain, Qatar — Kuwait City, Doha",
    "Asia/Tehran": "(UTC+3:30/+4:30) Iran — Tehran",
    "Asia/Dubai": "(UTC+4) UAE & Oman — Dubai, Abu Dhabi, Muscat",
    "Asia/Kabul": "(UTC+4:30) Afghanistan — Kabul",
    "Asia/Karachi": "(UTC+5) Pakistan — Karachi, Lahore, Islamabad",
    "Asia/Yekaterinburg": "(UTC+5) Russia Ural — Yekaterinburg",
    "Asia/Kolkata": "(UTC+5:30) India — Mumbai, Delhi, Kolkata, Chennai, Bengaluru",
    "Asia/Colombo": "(UTC+5:30) Sri Lanka — Colombo",
    "Asia/Kathmandu": "(UTC+5:45) Nepal — Kathmandu",
    "Asia/Dhaka": "(UTC+6) Bangladesh — Dhaka, Chittagong",
    "Asia/Rangoon": "(UTC+6:30) Myanmar — Yangon, Mandalay",
    "Asia/Bangkok": "(UTC+7) Indochina — Bangkok, Ho Chi Minh City, Jakarta",
    "Asia/Singapore": "(UTC+8) Singapore, Malaysia, Brunei — Singapore, Kuala Lumpur",
    "Asia/Manila": "(UTC+8) Philippines — Manila, Cebu",
    "Asia/Shanghai": "(UTC+8) China — Beijing, Shanghai, Guangzhou",
    "Asia/Taipei": "(UTC+8) Taiwan — Taipei",
    "Asia/Hong_Kong": "(UTC+8) Hong Kong",
    "Asia/Seoul": "(UTC+9) South Korea — Seoul, Busan",
    "Asia/Tokyo": "(UTC+9) Japan — Tokyo, Osaka, Nagoya",
    "Australia/Perth": "(UTC+8) Australia Western — Perth",
    "Australia/Darwin": "(UTC+9:30) Australia Central — Darwin",
    "Australia/Adelaide": "(UTC+9:30/+10:30) Australia South — Adelaide",
    "Australia/Sydney": "(UTC+10/+11) Australia Eastern — Sydney, Melbourne, Canberra",
    "Australia/Brisbane": "(UTC+10) Australia Queensland (no DST) — Brisbane",
    "Pacific/Auckland": "(UTC+12/+13) New Zealand — Auckland, Wellington",
    "Pacific/Fiji": "(UTC+12) Fiji — Suva",
    "UTC": "(UTC+0) Coordinated Universal Time"
};

// Aliases mapping old or legacy tz representations to canonical IANA timezone names
const TIMEZONE_MAPPING_ALIASES = {
    "Asia/Calcutta": "Asia/Kolkata",
    "UTC-05:00": "America/New_York",
    "UTC-06:00": "America/Chicago",
    "UTC-07:00": "America/Denver",
    "UTC-08:00": "America/Los_Angeles",
    "UTC+00:00": "UTC",
    "UTC+05:30": "Asia/Kolkata"
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

    // Check if selectEl already has server-rendered options
    const existingOptions = Array.from(selectEl.options).filter(opt => opt.value !== "");
    let optionData = [];
    let defaultOptText = selectEl.getAttribute("placeholder") || "--- Select Timezone ---";

    if (existingOptions.length > 0) {
        // PRESERVE SERVER-RENDERED OPTIONS! Do not wipe selectEl.innerHTML!
        const firstOpt = selectEl.options[0];
        if (firstOpt && !firstOpt.value) {
            defaultOptText = firstOpt.textContent;
        }
        existingOptions.forEach(opt => {
            optionData.push({
                value: opt.value,
                label: opt.textContent.trim()
            });
        });
    } else {
        // Fallback: Populate selectEl from window.TIMEZONE_LIST
        selectEl.innerHTML = "";
        const defaultOpt = document.createElement("option");
        defaultOpt.value = "";
        defaultOpt.textContent = defaultOptText;
        selectEl.appendChild(defaultOpt);

        window.TIMEZONE_LIST.forEach(tzVal => {
            const optLabel = TIMEZONE_LABELS[tzVal] || tzVal;
            optionData.push({
                value: tzVal,
                label: optLabel
            });
            const option = document.createElement("option");
            option.value = tzVal;
            option.textContent = optLabel;
            if (selectedVal === tzVal) {
                option.selected = true;
            }
            selectEl.appendChild(option);
        });
    }

    if (selectedVal) {
        selectEl.value = selectedVal;
    }

    // Determine initial trigger text
    let initialLabel = defaultOptText;
    if (selectedVal) {
        const found = optionData.find(d => d.value === selectedVal);
        if (found) {
            initialLabel = found.label;
        } else if (TIMEZONE_LABELS[selectedVal]) {
            initialLabel = TIMEZONE_LABELS[selectedVal];
        }
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
    triggerText.textContent = initialLabel;
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
        <svg class="custom-tz-search-icon" viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 11.99 14 9.5 14z"/></svg>
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
        <span>${defaultOptText}</span>
        <span class="custom-tz-option-check">✓</span>
    `;
    optionsList.appendChild(defaultItem);
    optionItems.push(defaultItem);

    optionData.forEach(itemData => {
        const item = document.createElement("li");
        item.className = `custom-tz-option ${selectedVal === itemData.value ? "selected" : ""}`;
        item.dataset.value = itemData.value;
        item.innerHTML = `
            <span>${itemData.label}</span>
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
