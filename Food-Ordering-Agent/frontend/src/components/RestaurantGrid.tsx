'use client';

import React from 'react';
import { Star, Clock, Sparkles, Scale } from 'lucide-react';

interface Restaurant {
  restaurant_id: string;
  name: string;
  rating: number;
  delivery_minutes: number;
  cost_for_two?: string;
  is_ad?: boolean;
  score?: number;
}

interface RestaurantGridProps {
  restaurants: Restaurant[];
  selectedRestaurantId?: string;
  onCompareClick: () => void;
}

export const RestaurantGrid: React.FC<RestaurantGridProps> = ({
  restaurants,
  selectedRestaurantId,
  onCompareClick
}) => {
  if (!restaurants || restaurants.length === 0) return null;

  return (
    <section className="mb-10">
      {/* Section Header */}
      <div className="flex items-end justify-between mb-5">
        <div>
          <h2 className="font-serif text-2xl font-bold text-espresso">
            Places that fit
          </h2>
          <p className="text-xs text-espresso-muted mt-1">
            {restaurants.length} {restaurants.length === 1 ? 'restaurant' : 'restaurants'} matched your preferences
          </p>
        </div>

        {restaurants.length > 1 && (
          <button
            onClick={onCompareClick}
            className="flex items-center space-x-1.5 bg-sand hover:bg-sand-dark border border-sand-dark/80 text-espresso text-xs font-semibold px-4 py-2 rounded-full transition shadow-warm-sm"
          >
            <Scale className="w-3.5 h-3.5 text-terracotta" />
            <span>Compare Places</span>
          </button>
        )}
      </div>

      {/* Responsive Restaurant Card Grid (3 col desktop, 2 col tablet, 1 col mobile) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {restaurants.map((rest) => {
          const isSelected = rest.restaurant_id === selectedRestaurantId;

          return (
            <div
              key={rest.restaurant_id}
              className={`bg-white rounded-3xl p-5 border transition-all duration-200 shadow-warm-sm flex flex-col justify-between relative overflow-hidden ${
                isSelected
                  ? 'border-terracotta ring-2 ring-terracotta/20 bg-terracotta-light/30'
                  : 'border-sand-dark/60 hover:border-sand-dark hover:shadow-warm-md'
              }`}
            >
              {/* Top Row: Name & Pick Tag */}
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-serif font-bold text-lg text-espresso leading-snug">
                    {rest.name}
                  </h3>
                  {isSelected && (
                    <span className="bg-terracotta text-white text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full shrink-0 flex items-center gap-1 shadow-sm">
                      <Sparkles className="w-3 h-3" />
                      Agent's Pick
                    </span>
                  )}
                </div>

                <p className="text-xs text-espresso-light mb-4">
                  {rest.cost_for_two ? `₹${rest.cost_for_two}` : 'North Indian · Fast Food'}
                </p>
              </div>

              {/* Bottom Row: Metadata (Rating, Time) */}
              <div className="flex items-center justify-between pt-3 border-t border-sand/80 text-xs font-medium text-espresso-muted">
                <div className="flex items-center space-x-1 bg-amber-500/10 text-amber-700 px-2.5 py-1 rounded-full font-semibold">
                  <Star className="w-3.5 h-3.5 fill-amber-500 text-amber-500" />
                  <span>{rest.rating}★</span>
                </div>

                <div className="flex items-center space-x-1 text-espresso-muted">
                  <Clock className="w-3.5 h-3.5 text-terracotta" />
                  <span>{rest.delivery_minutes} min</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
