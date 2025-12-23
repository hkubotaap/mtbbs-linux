import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en.json'
import ja from './locales/ja.json'

// Get saved language from localStorage or default to Japanese
const savedLanguage = localStorage.getItem('language') || 'ja'

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      ja: { translation: ja },
    },
    lng: savedLanguage,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  })

// Save language preference when it changes
i18n.on('languageChanged', (lng) => {
  localStorage.setItem('language', lng)
})

export default i18n
