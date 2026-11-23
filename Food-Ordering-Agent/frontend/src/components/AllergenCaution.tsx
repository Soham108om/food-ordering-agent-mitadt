'use client';

import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface AllergenCautionProps {
  allergens: string[];
  compact?: boolean;
}

export const AllergenCaution: React.FC<AllergenCautionProps> = ({
  allergens,
  compact = false
}) => {
  if (allergens.length === 0) return null;

  return (
    <div className={`flex items-start gap-2.5 bg-warmamber-light border border-warmamber-border text-warmamber rounded-2xl ${
      compact ? 'p-3 text-[11px]' : 'p-4 text-xs'
    }`}>
      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
      <p className="leading-relaxed">
        <strong>Allergen information is unavailable.</strong> These menu items cannot be verified against{' '}
        <strong>{allergens.join(', ')}</strong>. Confirm ingredients and cross-contact risk directly with the restaurant before ordering.
      </p>
    </div>
  );
};
