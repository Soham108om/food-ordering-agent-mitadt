'use client';

import React, { useState } from 'react';
import { Plus, ShieldCheck, X } from 'lucide-react';
import { AllergenCaution } from './AllergenCaution';

interface FoodSafetyPreferencesProps {
  vegetarianOnly: boolean;
  onVegetarianOnlyChange: (value: boolean) => void;
  allergens: string[];
  onAddAllergen: (allergen: string) => void;
  onRemoveAllergen: (allergen: string) => void;
  isLoading?: boolean;
  dietaryDisabled?: boolean;
  activeVegetarianOverride?: boolean;
  storageWarning?: string | null;
}

export const FoodSafetyPreferences: React.FC<FoodSafetyPreferencesProps> = ({
  vegetarianOnly,
  onVegetarianOnlyChange,
  allergens,
  onAddAllergen,
  onRemoveAllergen,
  isLoading = false,
  dietaryDisabled = false,
  activeVegetarianOverride = false,
  storageWarning
}) => {
  const [allergenInput, setAllergenInput] = useState('');

  const handleAddAllergen = (event: React.FormEvent) => {
    event.preventDefault();
    const allergen = allergenInput.trim().slice(0, 60);
    if (!allergen) return;
    onAddAllergen(allergen);
    setAllergenInput('');
  };

  return (
    <section className="bg-white border border-sand-dark rounded-3xl p-5 mb-6 shadow-warm-sm">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-full bg-olive-light border border-olive-border/60 flex items-center justify-center text-olive shrink-0">
          <ShieldCheck className="w-4 h-4" />
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="font-serif text-lg font-bold text-espresso">Food preferences &amp; allergies</h2>
          <p className="text-xs text-espresso-muted mt-0.5 mb-4">
            Preferences are saved in this browser. The vegetarian filter applies to new searches.
          </p>

          {isLoading && <p className="text-xs text-espresso-muted mb-3">Loading saved preferences...</p>}
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={vegetarianOnly}
              disabled={isLoading || dietaryDisabled}
              onChange={(event) => onVegetarianOnlyChange(event.target.checked)}
              className="mt-0.5 h-4 w-4 accent-olive disabled:opacity-50"
            />
            <span>
              <span className="block text-sm font-semibold text-espresso">Only show vegetarian dishes</span>
              <span className="block text-xs text-espresso-muted mt-0.5">
                Uses the menu&apos;s vegetarian label as a filter.
              </span>
            </span>
          </label>
          {dietaryDisabled && (
            <p className="text-[11px] text-espresso-light mt-2 ml-7">
              Finish this search before changing its dietary filter.
            </p>
          )}
          {activeVegetarianOverride && (
            <p role="status" className="text-[11px] text-warmamber mt-2 ml-7">
              This search is including non-vegetarian results by your one-time choice. Your saved vegetarian preference remains on for future searches.
            </p>
          )}

          <form onSubmit={handleAddAllergen} className="mt-4">
            <label htmlFor="allergen-input" className="block text-xs font-semibold text-espresso mb-1.5">
              Allergies to watch for
            </label>
            <div className="flex gap-2">
              <input
                id="allergen-input"
                value={allergenInput}
                onChange={(event) => setAllergenInput(event.target.value)}
                maxLength={60}
                disabled={isLoading}
                placeholder="e.g. peanuts"
                className="flex-1 min-w-0 bg-sand-light border border-sand-dark rounded-xl px-3 py-2 text-sm text-espresso focus:outline-none focus:ring-2 focus:ring-terracotta/30"
              />
              <button
                type="submit"
                disabled={isLoading || !allergenInput.trim()}
                className="inline-flex items-center gap-1 bg-sand hover:bg-sand-dark border border-sand-dark px-3 py-2 rounded-xl text-xs font-semibold text-espresso transition disabled:opacity-50"
              >
                <Plus className="w-3.5 h-3.5" />
                Add
              </button>
            </div>
          </form>

          {allergens.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {allergens.map((allergen) => (
                <span key={allergen} className="inline-flex items-center gap-1 bg-warmamber-light border border-warmamber-border rounded-full px-3 py-1 text-xs text-warmamber font-semibold">
                  {allergen}
                  <button
                    type="button"
                    aria-label={`Remove ${allergen}`}
                    onClick={() => onRemoveAllergen(allergen)}
                    className="hover:text-espresso"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}

          <p className="text-[11px] text-espresso-muted mt-3">
            Allergy details stay in this browser and are not sent to the ordering agent.
          </p>
          {storageWarning && (
            <p role="status" className="text-xs text-warmamber mt-2">{storageWarning}</p>
          )}
          {allergens.length > 0 && (
            <div className="mt-3">
              <AllergenCaution allergens={allergens} compact />
            </div>
          )}
        </div>
      </div>
    </section>
  );
};
