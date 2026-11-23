'use client';

import React from 'react';
import { ShieldCheck, ArrowRight, X, MapPin, CreditCard } from 'lucide-react';
import { AllergenCaution } from './AllergenCaution';

interface HumanConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirmOrder: (paymentMethod: string) => void;
  restaurantName?: string;
  itemName?: string;
  itemPrice?: number;
  addressId?: string;
  addressLabel?: string;
  addressDetails?: string;
  cartPricing?: {
    total_amount?: number | null;
    item_subtotal?: number | null;
    charges?: { label: string; amount: number }[];
  };
  allergens?: string[];
  isLoading?: boolean;
}

export const HumanConfirmationModal: React.FC<HumanConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirmOrder,
  restaurantName,
  itemName,
  itemPrice,
  addressId,
  addressLabel,
  addressDetails,
  cartPricing,
  allergens = [],
  isLoading = false
}) => {
  if (!isOpen) return null;
  const providerTotal = cartPricing?.total_amount;
  const itemSubtotal = cartPricing?.item_subtotal ?? itemPrice ?? 0;

  return (
    <div className="fixed inset-0 z-50 bg-espresso/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-cream border border-sand-dark rounded-3xl max-w-md w-full p-6 shadow-warm-lg">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-sand-dark pb-4 mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-olive-light border border-olive-border/60 flex items-center justify-center text-olive">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-serif font-bold text-xl text-espresso">
                Ready when you are.
              </h3>
              <p className="text-xs text-espresso-muted">
                Human Confirmation Checkpoint
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-sand hover:bg-sand-dark flex items-center justify-center text-espresso transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <p className="text-sm font-medium text-espresso mb-5 leading-relaxed">
          "The order is ready. I'll place it once you confirm."
        </p>

        {/* Order Details Breakdown */}
        <div className="bg-white p-4 rounded-2xl border border-sand-dark/70 space-y-3 mb-6 shadow-warm-sm text-xs">
          <div className="flex justify-between font-medium">
            <span className="text-espresso-muted">Restaurant:</span>
            <span className="font-bold text-espresso">{restaurantName || 'Selected Restaurant'}</span>
          </div>

          <div className="flex justify-between font-medium">
            <span className="text-espresso-muted">Selected Item:</span>
            <span className="font-bold text-espresso">{itemName || 'Selected Item'} (1x)</span>
          </div>

          {addressId && (
            <div className="flex justify-between items-center font-medium">
              <span className="text-espresso-muted flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-terracotta" /> Address:
              </span>
              <span className="text-right text-espresso truncate max-w-[220px]">
                <strong>{addressLabel || 'Saved address'}</strong>
                {addressDetails && <span className="block text-[10px] text-espresso-muted font-normal">{addressDetails}</span>}
              </span>
            </div>
          )}

          {cartPricing?.charges?.map((charge) => (
            <div key={charge.label} className="flex justify-between font-medium text-espresso-muted">
              <span>{charge.label}:</span>
              <span className="font-mono">₹{charge.amount.toFixed(0)}</span>
            </div>
          ))}

          {allergens.length > 0 && <AllergenCaution allergens={allergens} compact />}

          <div className="flex justify-between font-medium">
            <span className="text-espresso-muted flex items-center gap-1">
              <CreditCard className="w-3.5 h-3.5 text-terracotta" /> Payment Method:
            </span>
            <span className="font-bold text-espresso">Pay on Delivery (COD)</span>
          </div>

          <div className="flex justify-between items-center pt-2 border-t border-sand/80 text-sm font-bold">
            <span className="text-espresso">{providerTotal != null ? 'Swiggy cart total:' : 'Item subtotal:'}</span>
            <span className="font-serif text-lg text-terracotta">
              ₹{(providerTotal ?? itemSubtotal).toFixed(0)}
            </span>
          </div>
          {providerTotal == null && (
            <p className="text-[10px] text-warmamber">
              Final taxes and fees may be added by Swiggy; a complete total is not available yet.
            </p>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-3">
          <button
            onClick={onClose}
            className="w-1/3 bg-sand hover:bg-sand-dark text-espresso font-semibold py-3 rounded-full text-xs transition"
          >
            Not yet
          </button>

          <button
            onClick={() => onConfirmOrder('COD')}
            disabled={isLoading}
            className="w-2/3 bg-terracotta hover:bg-terracotta-hover text-white font-bold py-3 rounded-full flex items-center justify-center space-x-2 text-xs transition shadow-warm-sm disabled:opacity-50"
          >
            <span>{isLoading ? 'Placing Order...' : 'Confirm order'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
