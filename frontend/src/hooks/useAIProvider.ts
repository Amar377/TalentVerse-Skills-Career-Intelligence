import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { ProviderInfo } from '../types';

const STORAGE_KEY = 'talentverse_ai_provider';
const PROVIDER_CHANGE_EVENT = 'talentverse-ai-provider-change';

export function useAIProvider() {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [preferredProvider, setPreferredProvider] = useState(
    () => localStorage.getItem(STORAGE_KEY) || 'groq',
  );
  const [loadingProviders, setLoadingProviders] = useState(true);

  useEffect(() => {
    let active = true;
    const syncSelection = () => {
      setPreferredProvider(localStorage.getItem(STORAGE_KEY) || 'groq');
    };
    window.addEventListener(PROVIDER_CHANGE_EVENT, syncSelection);
    api.system.getStatus()
      .then((status) => {
        if (!active) return;
        const configuredProviders = status.providers.filter((provider) => provider.configured);
        setProviders(configuredProviders);
        const storedProvider = localStorage.getItem(STORAGE_KEY) || 'groq';
        if (!configuredProviders.some((provider) => provider.name === storedProvider)) {
          const defaultProvider = configuredProviders.find((provider) => provider.name === 'groq')
            || configuredProviders[0];
          if (defaultProvider) {
            setPreferredProvider(defaultProvider.name);
            localStorage.setItem(STORAGE_KEY, defaultProvider.name);
          }
        }
      })
      .catch((error: unknown) => {
        console.error('Failed to load configured AI models', error);
      })
      .finally(() => {
        if (active) setLoadingProviders(false);
      });

    return () => {
      active = false;
      window.removeEventListener(PROVIDER_CHANGE_EVENT, syncSelection);
    };
  }, []);

  const selectProvider = (provider: string) => {
    setPreferredProvider(provider);
    localStorage.setItem(STORAGE_KEY, provider);
    window.dispatchEvent(new Event(PROVIDER_CHANGE_EVENT));
  };

  return {
    providers,
    preferredProvider,
    selectProvider,
    loadingProviders,
  };
}
