'use client';

import React from 'react';
import { Sparkles, CheckCircle2, Bot, Star, Heart, RotateCcw } from 'lucide-react';
import { AllergenCaution } from './AllergenCaution';
import { FoodImage } from './FoodImage';

export interface MenuItem {
  item_id: string;
  name: string;
  price: number;
  is_veg: boolean;
  is_bestseller?: boolean;
  rating?: number | null;
  rating_count?: number | null;
  serving_label?: string | null;
  score?: number;
  image_url?: string | null;
}

interface MenuGridProps {
  menuItems: MenuItem[];
  selectedItem?: MenuItem;
  onSelectItem?: (item: MenuItem) => void;
  canConfirmSelection?: boolean;
  isConfirmingSelection?: boolean;
  onConfirmSelection?: () => void;
  allergens?: string[];
  favoriteDishIds?: string[];
  onToggleFavorite?: (item: MenuItem) => void;
  favoritesEnabled?: boolean;
  previouslyOrderedItemId?: string;
  previouslyOrderedItemName?: string;
}

export const MenuGrid: React.FC<MenuGridProps> = ({
  menuItems,
  selectedItem,
  onSelectItem,
  canConfirmSelection = false,
  isConfirmingSelection = false,
  onConfirmSelection,
  allergens = [],
  favoriteDishIds = [],
  onToggleFavorite,
  favoritesEnabled = true,
  previouslyOrderedItemId,
  previouslyOrderedItemName
}) => {
  if (!menuItems || menuItems.length === 0) return null;

  // The first item in ranked_menu_items is always the AI's top recommendation
  const aiRecommendedItem = menuItems[0];

  return (
    <section className="mb-10">
      {/* Section Header */}
      <div className="flex items-end justify-between mb-5">
        <div>
          <h2 className="font-serif text-2xl font-bold text-espresso">
            Something you'll love
          </h2>
          <p className="text-xs text-espresso-muted mt-1">
            Top dishes evaluated by the AI agent. Click any dish to choose it for your order.
          </p>
        </div>
      </div>

      {allergens.length > 0 && (
        <div className="mb-4">
          <AllergenCaution allergens={allergens} />
        </div>
      )}

      {/* Responsive Menu Grid (2 col desktop, 1 col mobile) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {menuItems.map((item, idx) => {
          const isSelected = selectedItem && (selectedItem.item_id === item.item_id || selectedItem.name === item.name);
          const isAiPick = aiRecommendedItem && (aiRecommendedItem.item_id === item.item_id || aiRecommendedItem.name === item.name);
          const isFavorite = favoriteDishIds.includes(item.item_id);
          const isPreviousOrder = item.item_id === previouslyOrderedItemId ||
            (Boolean(previouslyOrderedItemName) && item.name.toLowerCase() === previouslyOrderedItemName?.toLowerCase());

          return (
            <div
              key={item.item_id || item.name || idx}
              onClick={() => canConfirmSelection && onSelectItem && onSelectItem(item)}
              role={canConfirmSelection ? 'button' : undefined}
              tabIndex={canConfirmSelection ? 0 : undefined}
              onKeyDown={(event) => {
                if (event.target === event.currentTarget && canConfirmSelection && (event.key === 'Enter' || event.key === ' ')) {
                  event.preventDefault();
                  onSelectItem?.(item);
                }
              }}
              className={`bg-white rounded-2xl p-5 border transition-all duration-200 shadow-warm-sm flex items-start justify-between ${
                isSelected
                  ? 'border-terracotta ring-2 ring-terracotta/20 bg-terracotta-light/30'
                  : `border-sand-dark/60 ${canConfirmSelection ? 'cursor-pointer hover:border-terracotta/60 hover:shadow-warm-md hover:bg-sand-light/50' : 'cursor-default'}`
              }`}
            >
              <FoodImage
                src={item.image_url}
                alt={item.name}
                className="h-24 w-24 shrink-0"
              />
              <div className="min-w-0 flex-1 pr-4">
                <div className="flex flex-wrap items-center gap-1.5 mb-2">
                  {/* Veg indicator dot */}
                  <div className={`w-4 h-4 rounded-sm border flex items-center justify-center p-0.5 ${item.is_veg ? 'border-olive' : 'border-warmred'}`}>
                    <div className={`w-2 h-2 rounded-full ${item.is_veg ? 'bg-olive' : 'bg-warmred'}`} />
                  </div>

                  {/* AI Recommended Badge */}
                  {isAiPick && (
                    <span className="bg-olive-light text-olive border border-olive-border/60 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full flex items-center gap-1 shadow-xs">
                      <Bot className="w-3 h-3" />
                      Best Match (AI Pick)
                    </span>
                  )}

                  {isPreviousOrder && (
                    <span className="bg-warmamber-light text-warmamber border border-warmamber-border text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full flex items-center gap-1">
                      <RotateCcw className="w-3 h-3" />
                      Previously ordered
                    </span>
                  )}

                  {/* User Selected Badge */}
                  {isSelected && (
                    <span className="bg-terracotta text-white text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full flex items-center gap-1 shadow-sm">
                      <Sparkles className="w-3 h-3" />
                      {isAiPick ? 'Selected' : 'Your Choice'}
                    </span>
                  )}

                  {item.is_bestseller && !isAiPick && !isSelected && (
                    <span className="bg-sand text-espresso-muted text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full">
                      Bestseller
                    </span>
                  )}
                </div>

                <h3 className="font-serif font-bold text-base text-espresso leading-snug mb-1">
                  {item.name}
                </h3>

                <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                  <p className="text-sm font-semibold text-espresso font-mono">
                    ₹{item.price.toFixed(0)}
                  </p>
                  {item.serving_label && (
                    <span className="text-[11px] text-espresso-muted bg-sand-light border border-sand-dark/50 px-2 py-0.5 rounded-full">
                      {item.serving_label}
                    </span>
                  )}
                  {typeof item.rating === 'number' && item.rating > 0 && (
                    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-700">
                      <Star className="w-3 h-3 fill-amber-500 text-amber-500" />
                      {item.rating.toFixed(1)}
                      {typeof item.rating_count === 'number' && ` (${item.rating_count})`}
                    </span>
                  )}
                </div>
              </div>

              <button
                type="button"
                aria-label={`${isFavorite ? 'Remove' : 'Add'} ${item.name} ${isFavorite ? 'from' : 'to'} favorites`}
                aria-pressed={isFavorite}
                disabled={!favoritesEnabled}
                onClick={(event) => {
                  event.stopPropagation();
                  onToggleFavorite?.(item);
                }}
                className={`w-8 h-8 rounded-full flex items-center justify-center transition shrink-0 ${
                  isFavorite ? 'text-terracotta bg-terracotta/10' : 'text-espresso-light hover:text-terracotta hover:bg-terracotta/10'
                }`}
              >
                <Heart className={`w-4 h-4 ${isFavorite ? 'fill-current' : ''}`} />
              </button>

              {isSelected ? (
                <CheckCircle2 className="w-5 h-5 text-terracotta shrink-0 mt-1" />
              ) : (
                <span className="text-xs text-espresso-light font-medium opacity-0 hover:opacity-100 transition mt-1">
                  Select →
                </span>
              )}
            </div>
          );
        })}
      </div>
      {canConfirmSelection && (
        <div className="mt-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-olive-light/60 border border-olive-border/60 rounded-2xl p-4">
          <div>
            <p className="text-sm font-bold text-espresso">Your dish, your call</p>
            <p className="text-xs text-espresso-muted mt-0.5">
              The AI recommendation is preselected. Confirm it or choose another dish above.
            </p>
          </div>
          <button
            type="button"
            onClick={onConfirmSelection}
            disabled={!selectedItem?.item_id || isConfirmingSelection}
            className="shrink-0 bg-terracotta hover:bg-terracotta-hover text-white font-bold px-5 py-3 rounded-full text-sm transition shadow-warm-sm disabled:opacity-50"
          >
            {isConfirmingSelection ? 'Updating your cart...' : 'Continue with this dish'}
          </button>
        </div>
      )}
    </section>
  );
};
