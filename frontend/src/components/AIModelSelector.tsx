import React from 'react';
import { ProviderInfo } from '../types';

interface AIModelSelectorProps {
  providers: ProviderInfo[];
  preferredProvider: string;
  onChange: (provider: string) => void;
  loading?: boolean;
  disabled?: boolean;
}

export const AIModelSelector: React.FC<AIModelSelectorProps> = ({
  providers,
  preferredProvider,
  onChange,
  loading = false,
  disabled = false,
}) => (
  <div>
    <label
      htmlFor="ai-model-selector"
      className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5"
    >
      AI Model
    </label>
    <select
      id="ai-model-selector"
      value={preferredProvider}
      onChange={(event) => onChange(event.target.value)}
      disabled={loading || disabled || providers.length === 0}
      className="w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950/70 text-slate-900 dark:text-slate-100 text-sm p-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500/40 disabled:opacity-60"
    >
      {providers.length === 0 ? (
        <option value="groq">
          {loading ? 'Loading configured models…' : 'Groq (server default)'}
        </option>
      ) : (
        providers.map((provider) => (
          <option key={provider.name} value={provider.name}>
            {provider.name.toUpperCase()} — {provider.model}
          </option>
        ))
      )}
    </select>
    <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
      Preferred model is tried first; other configured models are fallback options.
    </p>
  </div>
);
