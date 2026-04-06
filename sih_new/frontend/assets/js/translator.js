document.addEventListener('DOMContentLoaded', () => {
    const languageSelector = document.getElementById('language-selector');

    const translations = {};

    async function loadTranslations(lang) {
        try {
            const response = await fetch(`assets/lang/${lang}.json`);
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
                // This handles elements that might have other child elements (like the hero title span)
                const elementToUpdate = element.querySelector('.translate-text') || element;
                elementToUpdate.textContent = langData[key];
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

    if (languageSelector) {
        languageSelector.addEventListener('change', (event) => {
            setLanguage(event.target.value);
        });
    }

    const savedLang = localStorage.getItem('selectedLanguage') || 'en';
    setLanguage(savedLang);
});