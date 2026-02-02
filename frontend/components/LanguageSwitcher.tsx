'use client';

import { useLanguage } from '../app/context/LanguageContext';
import { useTranslations } from 'next-intl';

export default function LanguageSwitcher() {
  const { language, setLanguage, isLoading } = useLanguage();
  const t = useTranslations('common');

  return (
    <div className="language-switcher">
      <label htmlFor="language-select">{t('language')}:</label>
      <select
        id="language-select"
        value={language}
        onChange={(e) => setLanguage(e.target.value as 'cs' | 'en')}
        disabled={isLoading}
        className="language-select"
      >
        <option value="cs">🇨🇿 Česky</option>
        <option value="en">🇬🇧 English</option>
      </select>
      
      <style jsx>{`
        .language-switcher {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .language-switcher label {
          font-size: 0.9rem;
          color: #666;
          white-space: nowrap;
        }

        .language-select {
          padding: 0.5rem 1rem;
          border: 2px solid #e0e0e0;
          border-radius: 6px;
          font-size: 0.9rem;
          background: white;
          cursor: pointer;
          transition: border-color 0.2s;
          min-width: 120px;
        }

        .language-select:focus {
          outline: none;
          border-color: #667eea;
        }

        .language-select:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        @media (max-width: 768px) {
          .language-switcher {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.25rem;
          }

          .language-select {
            min-width: 100px;
            padding: 0.4rem 0.8rem;
            font-size: 0.8rem;
          }

          .language-switcher label {
            font-size: 0.8rem;
          }
        }
      `}</style>
    </div>
  );
}