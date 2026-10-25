'use client';

import React from 'react';
import { Utensils, CheckCircle2, ShieldAlert, MapPin } from 'lucide-react';

interface NavbarProps {
  authenticated: boolean;
  onLoginClick: () => void;
  selectedAddressId?: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  authenticated,
  onLoginClick,
  selectedAddressId
}) => {
  return (
    <header className="bg-white/90 backdrop-blur-md border-b border-sand-dark/60 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* Brand & Supporting Tech Subtext */}
        <div className="flex items-baseline space-x-3">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-full bg-terracotta/10 border border-terracotta/30 flex items-center justify-center text-terracotta">
              <Utensils className="w-4 h-4" />
            </div>
            <h1 className="font-serif text-2xl font-bold text-espresso tracking-tight">
              FOOD AGENT
            </h1>
          </div>
          <span className="text-xs text-espresso-light font-medium tracking-wide hidden sm:inline-block">
            Gemini · LangGraph · Real Swiggy
          </span>
        </div>

        {/* Address & Subtle Swiggy Auth Status */}
        <div className="flex items-center space-x-3">
          {selectedAddressId && (
            <div className="hidden md:flex items-center space-x-1.5 bg-sand-light border border-sand-dark/60 px-3 py-1.5 rounded-full text-xs text-espresso-muted">
              <MapPin className="w-3.5 h-3.5 text-terracotta shrink-0" />
              <span className="font-mono truncate max-w-[160px]">
                {selectedAddressId}
              </span>
            </div>
          )}

          {authenticated ? (
            <div className="flex items-center space-x-1.5 bg-olive-light border border-olive-border/60 text-olive px-3.5 py-1.5 rounded-full text-xs font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
              <span>Swiggy Connected</span>
            </div>
          ) : (
            <button
              onClick={onLoginClick}
              className="flex items-center space-x-1.5 bg-terracotta hover:bg-terracotta-hover text-white px-4 py-1.5 rounded-full text-xs font-semibold transition shadow-warm-sm"
            >
              <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
              <span>Connect Swiggy</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
