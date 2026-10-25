'use client';

import React from 'react';
import { Brain, Map, Search, Filter, Trophy, CheckCircle, ShoppingCart, CreditCard, ShieldAlert, Bike, RotateCcw } from 'lucide-react';

interface AgentTimelineProps {
  currentStep?: string;
  needsUserInput?: boolean;
  replanningRequired?: boolean;
}

const STEPS = [
  { id: 'UNDERSTAND', label: 'Understanding', icon: Brain },
  { id: 'PLAN', label: 'Planning', icon: Map },
  { id: 'SEARCH_RESTAURANTS', label: 'Finding Places', icon: Search },
  { id: 'FILTER_RESTAURANTS', label: 'Filtering', icon: Filter },
  { id: 'RANK_RESTAURANTS', label: 'Ranking', icon: Trophy },
  { id: 'SELECT_RESTAURANT', label: 'Selecting Place', icon: CheckCircle },
  { id: 'SEARCH_MENU', label: 'Reading Menu', icon: Search },
  { id: 'FILTER_MENU', label: 'Filtering Menu', icon: Filter },
  { id: 'RANK_MENU', label: 'Ranking Menu', icon: Trophy },
  { id: 'SELECT_ITEM', label: 'Selecting Dish', icon: CheckCircle },
  { id: 'CART', label: 'Cart Sync', icon: ShoppingCart },
  { id: 'PAYMENT', label: 'Payment Options', icon: CreditCard },
  { id: 'CONFIRM_ORDER', label: 'Human Confirm', icon: ShieldAlert },
  { id: 'PLACE_ORDER', label: 'Order Placement', icon: ShieldAlert },
  { id: 'TRACK', label: 'Live Tracking', icon: Bike },
  { id: 'REPLAN', label: 'Re-Planning', icon: RotateCcw },
];

export const AgentTimeline: React.FC<AgentTimelineProps> = ({
  currentStep = 'START',
  needsUserInput = false,
  replanningRequired = false,
}) => {
  const currentIdx = STEPS.findIndex((s) => s.id === currentStep);

  return (
    <div className="bg-white border border-sand-dark/70 rounded-3xl p-5 shadow-warm-sm mb-8">
      {/* Activity Journey Header */}
      <div className="flex items-center justify-between mb-3.5 border-b border-sand/80 pb-3">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-terracotta animate-ping" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-espresso-muted">
            Agent Activity Journey
          </h2>
        </div>

        <div className="text-xs font-medium">
          {replanningRequired || currentStep === 'REPLAN' ? (
            <span className="bg-warmred-light text-warmred border border-warmred-border px-3 py-1 rounded-full flex items-center gap-1.5 font-semibold">
              <RotateCcw className="w-3.5 h-3.5" /> Re-Planning Required
            </span>
          ) : needsUserInput ? (
            <span className="bg-warmamber-light text-warmamber border border-warmamber-border px-3 py-1 rounded-full font-semibold animate-pulse">
              Paused for Your Action
            </span>
          ) : (
            <span className="bg-sand-light text-espresso-muted border border-sand-dark/60 px-3 py-1 rounded-full font-mono text-[11px]">
              {currentStep}
            </span>
          )}
        </div>
      </div>

      {/* Lightweight Responsive Stepper */}
      <div className="overflow-x-auto pb-1">
        <div className="flex items-center min-w-max space-x-2">
          {STEPS.filter(s => s.id !== 'REPLAN' || currentStep === 'REPLAN' || replanningRequired).map((step, idx) => {
            const Icon = step.icon;
            
            let isFinished = false;
            if (currentStep === 'TRACK') {
              isFinished = true;
            } else if (currentStep === 'REPLAN' || replanningRequired) {
              const replanSteps = ['UNDERSTAND', 'PLAN', 'SEARCH_RESTAURANTS', 'FILTER_RESTAURANTS', 'RANK_RESTAURANTS', 'SEARCH_MENU', 'FILTER_MENU'];
              isFinished = replanSteps.includes(step.id);
            } else if (currentIdx >= 0 && idx < currentIdx) {
              isFinished = true;
            }

            const isCurrent = currentStep === step.id;

            return (
              <div key={step.id} className="flex items-center space-x-2">
                <div
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                    isCurrent
                      ? 'bg-terracotta text-white font-semibold shadow-warm-sm scale-105'
                      : isFinished
                      ? 'bg-olive-light text-olive border border-olive-border/60 font-medium'
                      : 'bg-sand-light text-espresso-light border border-sand-dark/40'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5 shrink-0" />
                  <span>{step.label}</span>
                </div>

                {idx < STEPS.length - 1 && (
                  <div
                    className={`h-0.5 w-3 rounded-full ${
                      isFinished ? 'bg-olive/40' : 'bg-sand-dark/40'
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
