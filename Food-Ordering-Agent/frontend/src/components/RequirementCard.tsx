'use client';

import React from 'react';
import { Sparkles } from 'lucide-react';

interface RequirementCardProps {
  userRequest?: string;
  requirements?: {
    food?: string;
    cuisine?: string;
    food_components?: string[];
    vegetarian?: boolean;
    max_budget?: number;
    max_delivery_minutes?: number;
  };
}

export const RequirementCard: React.FC<RequirementCardProps> = ({
  userRequest,
  requirements
}) => {
  if (!requirements || Object.keys(requirements).length === 0) return null;

  const food = requirements.food;
  const cuisine = requirements.cuisine;
  const components = requirements.food_components || [];
  const isVeg = requirements.vegetarian;
  const budget = requirements.max_budget;
  const delivery = requirements.max_delivery_minutes;

  return (
    <div className="bg-white border border-sand-dark/70 rounded-3xl p-6 shadow-warm-sm mb-8">
      <div className="flex items-center space-x-2 text-terracotta text-xs font-semibold uppercase tracking-wider mb-2">
        <Sparkles className="w-4 h-4 shrink-0" />
        <span>You asked for</span>
      </div>

      {userRequest && (
        <p className="font-serif italic text-lg text-espresso mb-4">
          "{userRequest}"
        </p>
      )}

      <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-sand/80">
        {food && (
          <span className="bg-terracotta/10 text-terracotta border border-terracotta/20 px-3 py-1 rounded-full text-xs font-semibold capitalize">
            {food}
          </span>
        )}
        {cuisine && (
          <span className="bg-sand text-espresso-muted border border-sand-dark/60 px-3 py-1 rounded-full text-xs font-medium capitalize">
            {cuisine}
          </span>
        )}
        {components.map((comp, idx) => (
          <span key={idx} className="bg-sand-light text-espresso-muted border border-sand-dark/60 px-3 py-1 rounded-full text-xs font-medium capitalize">
            + {comp}
          </span>
        ))}
        {isVeg !== undefined && (
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${isVeg ? 'bg-olive-light text-olive border border-olive-border/60' : 'bg-sand text-espresso-muted'}`}>
            {isVeg ? 'Vegetarian' : 'Non-Veg Allowed'}
          </span>
        )}
        {budget && (
          <span className="bg-sand-light text-espresso-muted border border-sand-dark/60 px-3 py-1 rounded-full text-xs font-medium">
            ₹{budget} max
          </span>
        )}
        {delivery && (
          <span className="bg-sand-light text-espresso-muted border border-sand-dark/60 px-3 py-1 rounded-full text-xs font-medium">
            {delivery} min delivery
          </span>
        )}
      </div>
    </div>
  );
};
