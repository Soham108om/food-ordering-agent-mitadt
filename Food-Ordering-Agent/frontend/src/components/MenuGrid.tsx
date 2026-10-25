'use client';

import React from 'react';
import { Sparkles, CheckCircle2, Bot } from 'lucide-react';

interface MenuItem {
  item_id: string;
  name: string;
  price: number;
  is_veg: boolean;
  is_bestseller?: boolean;
  score?: number;
}

interface MenuGridProps {
  menuItems: MenuItem[];
  selectedItem?: MenuItem;
  onSelectItem?: (item: MenuItem) => void;
}

export const MenuGrid: React.FC<MenuGridProps> = ({
  menuItems,
  selectedItem,
  onSelectItem
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

      {/* Responsive Menu Grid (2 col desktop, 1 col mobile) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {menuItems.map((item, idx) => {
          const isSelected = selectedItem && (selectedItem.item_id === item.item_id || selectedItem.name === item.name);
          const isAiPick = aiRecommendedItem && (aiRecommendedItem.item_id === item.item_id || aiRecommendedItem.name === item.name);

          return (
            <div
              key={item.item_id || item.name || idx}
              onClick={() => onSelectItem && onSelectItem(item)}
              className={`bg-white rounded-2xl p-5 border cursor-pointer transition-all duration-200 shadow-warm-sm flex items-start justify-between ${
                isSelected
                  ? 'border-terracotta ring-2 ring-terracotta/20 bg-terracotta-light/30'
                  : 'border-sand-dark/60 hover:border-terracotta/60 hover:shadow-warm-md hover:bg-sand-light/50'
              }`}
            >
              <div className="flex-1 pr-4">
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

                <p className="text-sm font-semibold text-espresso font-mono">
                  ₹{item.price.toFixed(0)}
                </p>
              </div>

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
    </section>
  );
};
