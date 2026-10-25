'use client';

import React from 'react';
import { X, Star, Clock, Sparkles } from 'lucide-react';

interface Restaurant {
  restaurant_id: string;
  name: string;
  rating: number;
  delivery_minutes: number;
  cost_for_two?: string;
  score?: number;
}

interface RestaurantCompareModalProps {
  isOpen: boolean;
  onClose: () => void;
  restaurants: Restaurant[];
}

export const RestaurantCompareModal: React.FC<RestaurantCompareModalProps> = ({
  isOpen,
  onClose,
  restaurants
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-espresso/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-cream rounded-3xl border border-sand-dark max-w-4xl w-full p-6 shadow-warm-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b border-sand-dark pb-4 mb-6">
          <div>
            <h3 className="font-serif text-xl font-bold text-espresso">
              Compare Matching Places
            </h3>
            <p className="text-xs text-espresso-muted mt-0.5">
              Side-by-side breakdown of rated candidates
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-sand hover:bg-sand-dark flex items-center justify-center text-espresso transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {restaurants.slice(0, 6).map((rest, idx) => (
            <div key={rest.restaurant_id} className="bg-white border border-sand-dark/70 rounded-2xl p-4 shadow-warm-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-terracotta bg-terracotta/10 px-2 py-0.5 rounded-full">
                    Rank #{idx + 1}
                  </span>
                  {idx === 0 && (
                    <span className="text-[10px] font-bold text-olive bg-olive-light border border-olive-border/60 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <Sparkles className="w-3 h-3" /> Top Pick
                    </span>
                  )}
                </div>
                <h4 className="font-serif font-bold text-espresso text-base mb-3">
                  {rest.name}
                </h4>
              </div>

              <div className="space-y-2 border-t border-sand/80 pt-3 text-xs">
                <div className="flex items-center justify-between text-espresso-muted">
                  <span>Rating:</span>
                  <span className="font-semibold text-amber-700 flex items-center gap-1">
                    <Star className="w-3.5 h-3.5 fill-amber-500 text-amber-500" /> {rest.rating}★
                  </span>
                </div>
                <div className="flex items-center justify-between text-espresso-muted">
                  <span>Delivery Speed:</span>
                  <span className="font-semibold text-espresso flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-terracotta" /> {rest.delivery_minutes} min
                  </span>
                </div>
                {rest.score !== undefined && (
                  <div className="flex items-center justify-between text-espresso-muted">
                    <span>Relevance Score:</span>
                    <span className="font-mono font-bold text-terracotta">{rest.score.toFixed(1)}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
