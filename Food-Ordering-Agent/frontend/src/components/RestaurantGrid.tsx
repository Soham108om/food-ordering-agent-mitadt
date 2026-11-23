'use client';

import React from 'react';
import { Star, Clock, Sparkles, Scale, Heart } from 'lucide-react';
import { FoodImage } from './FoodImage';

export interface Restaurant {
  restaurant_id: string;
  name: string;
  rating: number;
  delivery_minutes: number;
  cost_for_two?: string;
  is_ad?: boolean;
  score?: number;
  image_url?: string | null;
}

interface RestaurantGridProps {
  restaurants: Restaurant[];
  selectedRestaurantId?: string;
  onCompareClick: () => void;
  favoriteRestaurantIds?: string[];
  onToggleFavorite?: (restaurant: Restaurant) => void;
  favoritesEnabled?: boolean;
  onSelectRestaurant?: (restaurant: Restaurant) => void;
  canConfirmSelection?: boolean;
  isConfirmingSelection?: boolean;
  onConfirmSelection?: () => void;
}

export const RestaurantGrid: React.FC<RestaurantGridProps> = ({
  restaurants,
  selectedRestaurantId,
  onCompareClick,
  favoriteRestaurantIds = [],
  onToggleFavorite,
  favoritesEnabled = true,
  onSelectRestaurant,
  canConfirmSelection = false,
  isConfirmingSelection = false,
  onConfirmSelection
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
        {restaurants.map((rest, index) => {
          const isSelected = rest.restaurant_id === selectedRestaurantId;
          const isAiPick = index === 0;
          const isFavorite = favoriteRestaurantIds.includes(rest.restaurant_id);

          return (
            <div
              key={rest.restaurant_id}
              onClick={() => canConfirmSelection && onSelectRestaurant?.(rest)}
              role={canConfirmSelection ? 'button' : undefined}
              tabIndex={canConfirmSelection ? 0 : undefined}
              onKeyDown={(event) => {
                if (event.target === event.currentTarget && canConfirmSelection && (event.key === 'Enter' || event.key === ' ')) {
                  event.preventDefault();
                  onSelectRestaurant?.(rest);
                }
              }}
              className={`bg-white rounded-3xl p-5 border transition-all duration-200 shadow-warm-sm flex flex-col justify-between relative overflow-hidden ${
                isSelected
                  ? 'border-terracotta ring-2 ring-terracotta/20 bg-terracotta-light/30'
                  : `border-sand-dark/60 ${canConfirmSelection ? 'cursor-pointer hover:border-terracotta/60 hover:shadow-warm-md' : 'cursor-default'}`
              }`}
            >
              <FoodImage
                src={rest.image_url}
                alt={`${rest.name} restaurant`}
                className="mb-4 h-40 w-full"
              />
              {/* Top Row: Name & Pick Tag */}
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-serif font-bold text-lg text-espresso leading-snug">
                    {rest.name}
                  </h3>
                  {isAiPick && (
                    <span className="bg-olive-light text-olive border border-olive-border/60 text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full shrink-0 flex items-center gap-1">
                      <Sparkles className="w-3 h-3" />
                      AI Pick
                    </span>
                  )}
                  {isSelected && (
                    <span className="bg-terracotta text-white text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full shrink-0 flex items-center gap-1 shadow-sm">
                      <Sparkles className="w-3 h-3" />
                      {isAiPick ? 'Selected' : 'Your Choice'}
                    </span>
                  )}
                  <button
                    type="button"
                    aria-label={`${isFavorite ? 'Remove' : 'Add'} ${rest.name} ${isFavorite ? 'from' : 'to'} favorites`}
                    aria-pressed={isFavorite}
                    disabled={!favoritesEnabled}
                    onClick={(event) => {
                      event.stopPropagation();
                      onToggleFavorite?.(rest);
                    }}
                    className={`w-7 h-7 rounded-full flex items-center justify-center transition shrink-0 ${
                      isFavorite ? 'text-terracotta bg-terracotta/10' : 'text-espresso-light hover:text-terracotta hover:bg-terracotta/10'
                    }`}
                  >
                    <Heart className={`w-4 h-4 ${isFavorite ? 'fill-current' : ''}`} />
                  </button>
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
      {canConfirmSelection && (
        <div className="mt-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-olive-light/60 border border-olive-border/60 rounded-2xl p-4">
          <div>
            <p className="text-sm font-bold text-espresso">Pick the place that feels right</p>
            <p className="text-xs text-espresso-muted mt-0.5">
              The AI pick is preselected. Choose another restaurant above or continue with its recommendation.
            </p>
          </div>
          <button
            type="button"
            onClick={onConfirmSelection}
            disabled={!selectedRestaurantId || isConfirmingSelection}
            className="shrink-0 bg-terracotta hover:bg-terracotta-hover text-white font-bold px-5 py-3 rounded-full text-sm transition shadow-warm-sm disabled:opacity-50"
          >
            {isConfirmingSelection ? 'Loading this menu...' : 'Continue with this restaurant'}
          </button>
        </div>
      )}
    </section>
  );
};
