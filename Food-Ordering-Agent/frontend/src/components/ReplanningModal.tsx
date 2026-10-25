'use client';

import React, { useState } from 'react';
import { RotateCcw, AlertCircle } from 'lucide-react';

interface ReplanningModalProps {
  isOpen: boolean;
  onRelaxConstraints: (newConstraints: { max_budget?: number; max_delivery_minutes?: number }) => void;
  userRequest?: string;
  currentBudget?: number | null;
  currentDelivery?: number | null;
  errorMessage?: string | null;
}

export const ReplanningModal: React.FC<ReplanningModalProps> = ({
  isOpen,
  onRelaxConstraints,
  userRequest,
  currentBudget = 300,
  currentDelivery = 30,
  errorMessage
}) => {
  const [newBudget, setNewBudget] = useState<number>((currentBudget || 300) + 150);
  const [newDelivery, setNewDelivery] = useState<number>((currentDelivery || 30) + 15);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-espresso/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-cream border border-sand-dark rounded-3xl max-w-md w-full p-6 shadow-warm-lg">
        <div className="flex items-center space-x-3 text-terracotta mb-3">
          <div className="w-10 h-10 rounded-full bg-terracotta/10 border border-terracotta/30 flex items-center justify-center">
            <RotateCcw className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-serif font-bold text-xl text-espresso">
              Let's try another way.
            </h3>
            <p className="text-xs text-espresso-muted">Preference Re-Evaluation</p>
          </div>
        </div>

        <p className="text-sm font-medium text-espresso mb-4 leading-relaxed">
          "I couldn't find an option that meets all of your preferences right now."
        </p>

        {userRequest && (
          <div className="bg-sand-light border border-sand-dark/60 p-3 rounded-2xl mb-4 text-xs font-mono text-espresso-muted">
            <span className="text-terracotta font-bold">Request:</span> "{userRequest}"
          </div>
        )}

        <div className="bg-white p-4 rounded-2xl border border-sand-dark/70 space-y-4 mb-5 shadow-warm-sm">
          <div className="text-xs text-espresso-muted mb-1">
            Current limits: <strong>Budget ≤ ₹{currentBudget || 300}</strong> · <strong>Delivery ≤ {currentDelivery || 30} mins</strong>
          </div>

          <div>
            <label className="text-xs text-espresso font-semibold mb-1 block">
              Adjust Max Budget Ceiling (₹)
            </label>
            <input
              type="number"
              value={newBudget}
              onChange={(e) => setNewBudget(Number(e.target.value))}
              className="w-full bg-sand-light border border-sand-dark rounded-xl px-3 py-2 text-sm text-espresso font-mono focus:border-terracotta focus:outline-none"
            />
          </div>

          <div>
            <label className="text-xs text-espresso font-semibold mb-1 block">
              Adjust Delivery Time Ceiling (Minutes)
            </label>
            <input
              type="number"
              value={newDelivery}
              onChange={(e) => setNewDelivery(Number(e.target.value))}
              className="w-full bg-sand-light border border-sand-dark rounded-xl px-3 py-2 text-sm text-espresso font-mono focus:border-terracotta focus:outline-none"
            />
          </div>
        </div>

        <button
          onClick={() => onRelaxConstraints({ max_budget: newBudget, max_delivery_minutes: newDelivery })}
          className="w-full bg-terracotta hover:bg-terracotta-hover text-white font-bold py-3.5 rounded-full flex items-center justify-center space-x-2 transition shadow-warm-sm text-xs"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Update preferences & try again</span>
        </button>
      </div>
    </div>
  );
};
