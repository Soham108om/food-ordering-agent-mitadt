'use client';

import React, { useEffect, useState } from 'react';
import { RotateCcw } from 'lucide-react';

interface NoMatchDetails {
  stage?: string;
  candidate_count?: number;
  reasons?: Record<string, number>;
  suggestions?: string[];
}

interface RelaxedConstraints {
  max_budget?: number;
  max_delivery_minutes?: number;
  food?: string;
  vegetarian?: boolean;
}

interface ReplanningModalProps {
  isOpen: boolean;
  onRelaxConstraints: (newConstraints: RelaxedConstraints) => void;
  userRequest?: string;
  currentFood?: string | null;
  currentBudget?: number | null;
  currentDelivery?: number | null;
  errorMessage?: string | null;
  noMatchDetails?: NoMatchDetails | null;
}

const REASON_LABELS: Record<string, string> = {
  delivery_time: 'delivery estimates exceeded your time limit',
  delivery_time_unavailable: 'delivery estimates were unavailable',
  closed: 'restaurants were marked closed',
  food_mismatch: 'results did not match the requested food',
  budget: 'menu items were over your budget',
  vegetarian: 'items did not meet the vegetarian-only filter',
  no_menu_items: 'no menu items were returned',
  menu_search_failed: 'the menu search could not be completed'
};

export const ReplanningModal: React.FC<ReplanningModalProps> = ({
  isOpen,
  onRelaxConstraints,
  userRequest,
  currentFood,
  currentBudget,
  currentDelivery,
  errorMessage,
  noMatchDetails
}) => {
  const [newBudget, setNewBudget] = useState<number>((currentBudget ?? 300) + 150);
  const [newDelivery, setNewDelivery] = useState<number>((currentDelivery ?? 30) + 15);
  const [newFood, setNewFood] = useState<string>(currentFood || '');
  const [relaxVegetarian, setRelaxVegetarian] = useState<boolean>(false);

  useEffect(() => {
    if (!isOpen) return;
    setNewBudget((currentBudget ?? 300) + 150);
    setNewDelivery((currentDelivery ?? 30) + 15);
    setNewFood(currentFood || '');
    setRelaxVegetarian(false);
  }, [isOpen, currentBudget, currentDelivery, currentFood, noMatchDetails]);

  if (!isOpen) return null;

  const suggestions = noMatchDetails?.suggestions?.length
    ? noMatchDetails.suggestions
    : ['budget', 'delivery_time'];
  const showBudget = suggestions.includes('budget');
  const showDelivery = suggestions.includes('delivery_time');
  const showFood = suggestions.includes('food');
  const showVegetarian = suggestions.includes('vegetarian');
  const reasonSummary = Object.entries(noMatchDetails?.reasons || {})
    .filter(([, count]) => count > 0)
    .map(([reason, count]) => {
      const label = REASON_LABELS[reason] || reason.replace(/_/g, ' ');
      return `${count} ${label}`;
    });
  const candidateCount = noMatchDetails?.candidate_count;

  const isValid =
    (!showBudget || (Number.isFinite(newBudget) && newBudget > (currentBudget ?? 0))) &&
    (!showDelivery || (Number.isFinite(newDelivery) && newDelivery > (currentDelivery ?? 0))) &&
    (!showFood || (
      newFood.trim().length > 0 &&
      newFood.trim().toLowerCase() !== (currentFood || '').trim().toLowerCase()
    )) &&
    (!showVegetarian || relaxVegetarian);

  const submitChanges = () => {
    if (!isValid) return;
    const constraints: RelaxedConstraints = {};
    if (showBudget) constraints.max_budget = newBudget;
    if (showDelivery) constraints.max_delivery_minutes = newDelivery;
    if (showFood) constraints.food = newFood.trim();
    if (showVegetarian && relaxVegetarian) constraints.vegetarian = false;
    onRelaxConstraints(constraints);
  };

  return (
    <div className="fixed inset-0 z-50 bg-espresso/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-cream border border-sand-dark rounded-3xl max-w-md w-full p-6 shadow-warm-lg">
        <div className="flex items-center space-x-3 text-terracotta mb-3">
          <div className="w-10 h-10 rounded-full bg-terracotta/10 border border-terracotta/30 flex items-center justify-center">
            <RotateCcw className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-serif font-bold text-xl text-espresso">
              No matches for this request.
            </h3>
            <p className="text-xs text-espresso-muted">Review why and choose what to adjust</p>
          </div>
        </div>

        <p className="text-sm font-medium text-espresso mb-4 leading-relaxed">
          {typeof candidateCount === 'number' && candidateCount === 0
            ? 'The search returned no usable results.'
            : 'The available results did not meet the current filters.'}
        </p>

        {reasonSummary.length > 0 && (
          <ul className="bg-warmamber-light border border-warmamber-border rounded-2xl p-3 mb-4 space-y-1 text-xs text-warmamber">
            {reasonSummary.map((reason) => <li key={reason}>• {reason}</li>)}
          </ul>
        )}

        {errorMessage && (
          <p role="status" className="bg-warmamber-light border border-warmamber-border rounded-2xl p-3 mb-4 text-xs text-warmamber">
            Search detail: {errorMessage}
          </p>
        )}

        {userRequest && (
          <div className="bg-sand-light border border-sand-dark/60 p-3 rounded-2xl mb-4 text-xs font-mono text-espresso-muted">
            <span className="text-terracotta font-bold">Request:</span> "{userRequest}"
          </div>
        )}

        <div className="bg-white p-4 rounded-2xl border border-sand-dark/70 space-y-4 mb-5 shadow-warm-sm">
          {(showBudget || showDelivery) && (
            <div className="text-xs text-espresso-muted">
              Current limits: {showBudget && <strong>Budget ≤ ₹{currentBudget ?? 'not set'}</strong>}
              {showBudget && showDelivery && ' · '}
              {showDelivery && <strong>Delivery ≤ {currentDelivery ?? 'not set'} mins</strong>}
            </div>
          )}

          {showBudget && (
            <div>
              <label className="text-xs text-espresso font-semibold mb-1 block">
                Try a higher maximum budget (₹)
              </label>
              <input
                type="number"
                min={(currentBudget ?? 0) + 1}
                value={newBudget}
                onChange={(e) => setNewBudget(Number(e.target.value))}
                className="w-full bg-sand-light border border-sand-dark rounded-xl px-3 py-2 text-sm text-espresso font-mono focus:border-terracotta focus:outline-none"
              />
            </div>
          )}

          {showDelivery && (
            <div>
              <label className="text-xs text-espresso font-semibold mb-1 block">
                Try a longer delivery-time limit (minutes)
              </label>
              <input
                type="number"
                min={(currentDelivery ?? 0) + 1}
                value={newDelivery}
                onChange={(e) => setNewDelivery(Number(e.target.value))}
                className="w-full bg-sand-light border border-sand-dark rounded-xl px-3 py-2 text-sm text-espresso font-mono focus:border-terracotta focus:outline-none"
              />
            </div>
          )}

          {showFood && (
            <div>
              <label className="text-xs text-espresso font-semibold mb-1 block">
                Broaden or change the food search
              </label>
              <input
                type="text"
                value={newFood}
                onChange={(e) => setNewFood(e.target.value)}
                placeholder="Enter a broader or different dish or cuisine"
                className="w-full bg-sand-light border border-sand-dark rounded-xl px-3 py-2 text-sm text-espresso focus:border-terracotta focus:outline-none"
              />
            </div>
          )}

          {showVegetarian && (
            <label className="flex items-start gap-2 text-xs text-espresso">
              <input
                type="checkbox"
                checked={relaxVegetarian}
                onChange={(e) => setRelaxVegetarian(e.target.checked)}
                className="mt-0.5 accent-terracotta"
              />
              <span>For this search only, include non-vegetarian results. Your saved preference will not change.</span>
            </label>
          )}
        </div>

        <button
          type="button"
          disabled={!isValid}
          onClick={submitChanges}
          className="w-full bg-terracotta hover:bg-terracotta-hover text-white font-bold py-3.5 rounded-full flex items-center justify-center space-x-2 transition shadow-warm-sm text-xs disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Apply selected changes & try again</span>
        </button>
      </div>
    </div>
  );
};
