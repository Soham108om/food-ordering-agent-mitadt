'use client';

import React from 'react';
import { CreditCard, CheckCircle2, ShieldCheck } from 'lucide-react';

interface PaymentSelectionModalProps {
  isOpen: boolean;
  onSelectPayment: (method: string) => void;
  isLoading?: boolean;
}

export const PaymentSelectionModal: React.FC<PaymentSelectionModalProps> = ({
  isOpen,
  onSelectPayment,
  isLoading = false
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-espresso/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-cream border border-sand-dark rounded-3xl max-w-md w-full p-6 shadow-warm-lg">
        <div className="flex items-center space-x-3 text-terracotta mb-3">
          <div className="w-10 h-10 rounded-full bg-terracotta/10 border border-terracotta/30 flex items-center justify-center">
            <CreditCard className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-serif font-bold text-xl text-espresso">Select Payment Method</h3>
            <p className="text-xs text-espresso-muted">Live Swiggy options retrieved</p>
          </div>
        </div>

        <p className="text-xs text-espresso-muted mb-5 bg-sand-light p-3.5 rounded-2xl border border-sand-dark/60 leading-relaxed">
          Choose your preferred payment method to proceed to the final <strong>Human Confirmation Checkpoint</strong>. No order will be placed yet.
        </p>

        <div className="space-y-3 mb-6">
          {[
            { id: 'COD', title: 'Pay on Delivery (COD)', desc: 'Pay cash or UPI upon delivery' },
            { id: 'UPI', title: 'UPI Payment', desc: 'Google Pay, PhonePe, Paytm' },
            { id: 'Cash', title: 'Cash', desc: 'Exact cash upon arrival' },
          ].map((m) => (
            <button
              key={m.id}
              onClick={() => onSelectPayment(m.id)}
              disabled={isLoading}
              className="w-full bg-white hover:bg-terracotta-light hover:border-terracotta border border-sand-dark p-4 rounded-2xl flex items-center justify-between text-left transition group shadow-warm-sm"
            >
              <div>
                <p className="font-serif font-bold text-espresso text-sm group-hover:text-terracotta transition">{m.title}</p>
                <p className="text-xs text-espresso-muted">{m.desc}</p>
              </div>
              <CheckCircle2 className="w-5 h-5 text-sand-dark group-hover:text-terracotta transition" />
            </button>
          ))}
        </div>

        <div className="flex items-center justify-center space-x-1.5 text-xs text-espresso-muted">
          <ShieldCheck className="w-4 h-4 text-olive" />
          <span>Protected by Swiggy OAuth & Human Confirmation Boundary</span>
        </div>
      </div>
    </div>
  );
};
