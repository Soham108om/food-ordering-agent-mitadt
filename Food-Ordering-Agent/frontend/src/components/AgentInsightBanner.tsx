'use client';

import React from 'react';
import { Check, Sparkles } from 'lucide-react';

interface AgentInsightBannerProps {
  restaurantName?: string;
  itemName?: string;
  itemPrice?: number;
  deliveryMinutes?: number;
  maxBudget?: number;
  maxDelivery?: number;
  isVeg?: boolean;
}

export const AgentInsightBanner: React.FC<AgentInsightBannerProps> = ({
  restaurantName,
  itemName,
  itemPrice,
  deliveryMinutes,
  maxBudget,
  maxDelivery,
  isVeg
}) => {
  if (!restaurantName) return null;

  return (
    <div className="bg-sand-light border border-terracotta-border/40 rounded-3xl p-6 shadow-warm-sm mb-8 relative overflow-hidden">
      <div className="flex items-center space-x-2 text-terracotta text-xs font-semibold uppercase tracking-wider mb-2">
        <Sparkles className="w-4 h-4 shrink-0" />
        <span>Why this choice?</span>
      </div>

      <h3 className="font-serif text-xl font-bold text-espresso mb-3 leading-snug">
        "{restaurantName} is the strongest match for your preferences."
      </h3>

      <p className="text-xs text-espresso-muted mb-4 max-w-2xl leading-relaxed">
        Our agent evaluated live Swiggy options against your explicit constraints. {itemName ? `"${itemName}" was selected for maximum value and quality.` : ''}
      </p>

      {/* Verified Constraints Pills */}
      <div className="flex flex-wrap items-center gap-2.5">
        {isVeg && (
          <div className="flex items-center space-x-1.5 bg-olive-light text-olive border border-olive-border/60 px-3 py-1 rounded-full text-xs font-semibold">
            <Check className="w-3.5 h-3.5 shrink-0" />
            <span>Vegetarian Verified</span>
          </div>
        )}
        {itemPrice !== undefined && maxBudget !== undefined && itemPrice <= maxBudget && (
          <div className="flex items-center space-x-1.5 bg-olive-light text-olive border border-olive-border/60 px-3 py-1 rounded-full text-xs font-semibold">
            <Check className="w-3.5 h-3.5 shrink-0" />
            <span>₹{itemPrice} within ₹{maxBudget} budget</span>
          </div>
        )}
        {deliveryMinutes !== undefined && maxDelivery !== undefined && deliveryMinutes <= maxDelivery && (
          <div className="flex items-center space-x-1.5 bg-olive-light text-olive border border-olive-border/60 px-3 py-1 rounded-full text-xs font-semibold">
            <Check className="w-3.5 h-3.5 shrink-0" />
            <span>{deliveryMinutes} min delivery (under {maxDelivery} min)</span>
          </div>
        )}
      </div>
    </div>
  );
};
