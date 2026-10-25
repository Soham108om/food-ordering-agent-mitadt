'use client';

import React from 'react';
import { ShoppingBag, ArrowRight, MapPin, CheckCircle2 } from 'lucide-react';

interface CartSummaryProps {
  restaurantName?: string;
  selectedItem?: {
    name: string;
    price: number;
  };
  addressId?: string;
  onProceedToPayment: () => void;
}

export const CartSummary: React.FC<CartSummaryProps> = ({
  restaurantName,
  selectedItem,
  addressId,
  onProceedToPayment
}) => {
  if (!selectedItem || !selectedItem.name) return null;

  return (
    <section className="bg-white border border-sand-dark rounded-3xl p-6 shadow-warm-md mb-10">
      <div className="flex items-center justify-between border-b border-sand-dark pb-4 mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-full bg-terracotta/10 border border-terracotta/30 flex items-center justify-center text-terracotta">
            <ShoppingBag className="w-4 h-4" />
          </div>
          <div>
            <h2 className="font-serif text-xl font-bold text-espresso">
              Your order
            </h2>
            <p className="text-xs text-espresso-muted">
              {restaurantName || 'Selected Restaurant'}
            </p>
          </div>
        </div>

        <span className="bg-olive-light text-olive border border-olive-border/60 px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5">
          <CheckCircle2 className="w-3.5 h-3.5" />
          Live Cart · Swiggy
        </span>
      </div>

      <div className="space-y-3 mb-6">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-2">
            <span className="bg-sand px-2 py-0.5 rounded text-xs font-bold text-espresso font-mono">1x</span>
            <span className="font-semibold text-espresso">{selectedItem.name}</span>
          </div>
          <span className="font-mono font-bold text-espresso">₹{selectedItem.price.toFixed(0)}</span>
        </div>

        {addressId && (
          <div className="flex items-center space-x-2 text-xs text-espresso-muted pt-2 border-t border-sand/80">
            <MapPin className="w-3.5 h-3.5 text-terracotta shrink-0" />
            <span>Delivering to address: <strong className="font-mono">{addressId}</strong></span>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-sand-dark">
        <div>
          <p className="text-xs text-espresso-muted uppercase tracking-wider font-semibold">Total Amount</p>
          <p className="font-serif text-2xl font-bold text-espresso">₹{selectedItem.price.toFixed(0)}</p>
        </div>

        <button
          onClick={onProceedToPayment}
          className="bg-terracotta hover:bg-terracotta-hover text-white font-bold px-6 py-3 rounded-full flex items-center space-x-2 text-sm transition shadow-warm-sm"
        >
          <span>Choose payment</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </section>
  );
};
