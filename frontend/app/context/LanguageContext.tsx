'use client';

import { createContext, useContext, useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import ApiClient from '../lib/api';

interface LanguageContextType {
  language: 'cs' | 'en';
  setLanguage: (lang: 'cs' | 'en') => Promise<void>;
  isLoading: boolean;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  
  const [language, setLanguageState] = useState<'cs' | 'en'>('cs');
  const [isLoading, setIsLoading] = useState(false);

  const setLanguage = async (newLang: 'cs' | 'en') => {
    setIsLoading(true);
    
    try {
      // Update backend
      await ApiClient.updateUserLanguage(newLang);
      
      // Update local state
      setLanguageState(newLang);
      
      // Store in localStorage for persistence
      localStorage.setItem('preferred_language', newLang);
      
      // Navigate to new locale
      let newPath = pathname;
      console.log('LanguageContext: Current pathname:', pathname);
      
      // Handle locale prefix
      if (pathname.startsWith('/en/')) {
        newPath = pathname.replace('/en/', '/');
      } else if (pathname.startsWith('/cs/')) {
        newPath = pathname.replace('/cs/', '/');
      }
      
      if (newLang === 'en' && !pathname.startsWith('/en/')) {
        newPath = `/en${newPath}`;
      } else if (newLang === 'cs' && pathname.startsWith('/en/')) {
        newPath = pathname.replace('/en/', '/');
      }
      
      console.log('LanguageContext: New path for', newLang, ':', newPath);
      router.push(newPath);
      router.refresh();
    } catch (error) {
      console.error('Failed to update language:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Load language from user profile or localStorage on mount
  useEffect(() => {
    const loadLanguage = async () => {
      try {
        console.log('LanguageContext: Loading language from API...');
        // Try to get from API first
        const userProfile = await ApiClient.getUserProfile();
        console.log('LanguageContext: User profile from API:', userProfile);
        const apiLanguage = userProfile.preferred_language;
        console.log('LanguageContext: API language:', apiLanguage);
        
        if (apiLanguage && (apiLanguage === 'cs' || apiLanguage === 'en')) {
          console.log('LanguageContext: Setting language from API:', apiLanguage);
          setLanguageState(apiLanguage);
          localStorage.setItem('preferred_language', apiLanguage);
        } else {
          // Fallback to localStorage
          const storedLanguage = localStorage.getItem('preferred_language');
          console.log('LanguageContext: Using localStorage language:', storedLanguage);
          if (storedLanguage && (storedLanguage === 'cs' || storedLanguage === 'en')) {
            setLanguageState(storedLanguage as 'cs' | 'en');
          }
        }
      } catch (error) {
        console.error('LanguageContext: Failed to load language preference:', error);
        // Fallback to localStorage
        const storedLanguage = localStorage.getItem('preferred_language');
        console.log('LanguageContext: Using localStorage language due to error:', storedLanguage);
        if (storedLanguage && (storedLanguage === 'cs' || storedLanguage === 'en')) {
          setLanguageState(storedLanguage as 'cs' | 'en');
        }
      }
    };

    loadLanguage();
  }, []);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, isLoading }}>
      {children}
    </LanguageContext.Provider>
  );
}

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
};