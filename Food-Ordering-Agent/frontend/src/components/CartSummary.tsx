'use client';

import React from 'react';
import { ShoppingBag, ArrowRight, MapPin, CheckCircle2 } from 'lucide-react';
import { AllergenCaution } from './AllergenCaution';

interface CartSummaryProps {
  restaurantName?: string;
  selectedItem?: {
    name: string;
    price: number;
  };
  addressId?: string;
  addressLabel?: string;
  addressDetails?: string;
  cartPricing?: {
    total_amount?: number | null;
    item_subtotal?: number | null;
    charges?: { label: string; amount: number }[];
  };
  allergens?: string[];
  onProceedToPayment: () => void;
}

export const CartSummary: React.FC<CartSummaryProps> = ({
  restaurantName,
  selectedItem,
  addressId,
  addressLabel,
  addressDetails,
  cartPricing,
  allergens = [],
  onProceedToPayment
}) => {
  if (!selectedItem || !selectedItem.name) return null;
  const providerTotal = cartPricing?.total_amount;
  const itemSubtotal = cartPricing?.item_subtotal ?? selectedItem.price;

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

        {cartPricing?.charges?.map((charge) => (
          <div key={charge.label} className="flex items-center justify-between text-xs text-espresso-muted">
            <span>{charge.label}</span>
            <span className="font-mono">₹{charge.amount.toFixed(0)}</span>
          </div>
        ))}

        {addressId && (
          <div className="flex items-center space-x-2 text-xs text-espresso-muted pt-2 border-t border-sand/80">
            <MapPin className="w-3.5 h-3.5 text-terracotta shrink-0" />
            <span>
              Delivering to <strong className="text-espresso">{addressLabel || 'saved address'}</strong>
              {addressDetails && <span className="block mt-0.5">{addressDetails}</span>}
            </span>
          </div>
        )}
        {allergens.length > 0 && (
          <AllergenCaution allergens={allergens} compact />
        )}
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-sand-dark">
        <div>
          <p className="text-xs text-espresso-muted uppercase tracking-wider font-semibold">
            {providerTotal != null ? 'Swiggy cart total' : 'Item subtotal'}
          </p>
          <p className="font-serif text-2xl font-bold text-espresso">
            ₹{(providerTotal ?? itemSubtotal).toFixed(0)}
          </p>
          {providerTotal == null && (
            <p className="text-[11px] text-warmamber mt-1 max-w-xs">
              Final taxes and fees may be added by Swiggy; a complete total is not available yet.
            </p>
          )}
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
