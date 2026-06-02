document.addEventListener('DOMContentLoaded', () => {
    const languageSelector = document.getElementById('language-selector');

    const translations = {};

    async function loadTranslations(lang) {
        try {
            const response = await fetch(`assets/lang/${lang}.json?v=${Date.now()}`);
            if (!response.ok) {
                console.error(`Could not load translation file for: ${lang}`);
                return;
            }
            translations[lang] = await response.json();
        } catch (error) {
            console.error(`Error fetching translation file for ${lang}:`, error);
        }
    }

    function applyTranslations(lang) {
        const langData = translations[lang];
        if (!langData) return;

        document.querySelectorAll('[data-translate-key]').forEach(element => {
            const key = element.getAttribute('data-translate-key');
            if (langData[key]) {
                if (element.tagName === 'INPUT' && element.hasAttribute('placeholder')) {
                    element.placeholder = langData[key];
                } else {
                    const elementToUpdate = element.querySelector('.translate-text') || element;
                    elementToUpdate.textContent = langData[key];
                }
            }
        });
    }

    async function setLanguage(lang) {
        if (!translations[lang]) {
            await loadTranslations(lang);
        }
        applyTranslations(lang);
        localStorage.setItem('selectedLanguage', lang);
        if (languageSelector) {
            languageSelector.value = lang;
        }
    }

    window.translations = translations;

    function getTranslation(key, lang = localStorage.getItem('selectedLanguage') || 'en') {
        const langData = translations[lang];
        if (!langData) return key;
        return langData[key] || key;
    }
    window.getTranslation = getTranslation;
    window.applyTranslations = applyTranslations;
    window.setLanguage = setLanguage;

    if (languageSelector) {
        languageSelector.addEventListener('change', (event) => {
            setLanguage(event.target.value);
            // Dispatch custom event so other components know language changed
            document.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: event.target.value } }));
        });
    }

    const savedLang = localStorage.getItem('selectedLanguage') || 'en';
    setLanguage(savedLang);
});