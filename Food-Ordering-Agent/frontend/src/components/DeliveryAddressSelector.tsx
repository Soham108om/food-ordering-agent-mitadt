'use client';

import React from 'react';
import { ChevronDown, MapPin } from 'lucide-react';

export interface SavedAddress {
  id: string;
  label: string;
  details: string;
}

interface DeliveryAddressSelectorProps {
  addresses: SavedAddress[];
  selectedAddressId: string;
  onSelect: (addressId: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export const DeliveryAddressSelector: React.FC<DeliveryAddressSelectorProps> = ({
  addresses,
  selectedAddressId,
  onSelect,
  isLoading = false,
  disabled = false
}) => (
  <section className="bg-white border border-sand-dark rounded-3xl p-5 mb-6 shadow-warm-sm">
    <div className="flex items-start gap-3">
      <div className="w-9 h-9 rounded-full bg-terracotta/10 border border-terracotta/30 flex items-center justify-center text-terracotta shrink-0">
        <MapPin className="w-4 h-4" />
      </div>
      <div className="min-w-0 flex-1">
        <label htmlFor="delivery-address" className="block font-serif text-lg font-bold text-espresso">
          Delivering to
        </label>
        <p className="text-xs text-espresso-muted mt-0.5 mb-3">
          Choose where this order should arrive.
        </p>

        {isLoading ? (
          <p className="text-sm text-espresso-muted">Loading your saved addresses...</p>
        ) : addresses.length > 0 ? (
          <>
            <div className="relative">
              <select
                id="delivery-address"
                value={selectedAddressId}
                onChange={(event) => onSelect(event.target.value)}
                disabled={disabled}
                className="w-full appearance-none bg-sand-light border border-sand-dark rounded-xl px-4 py-3 pr-10 text-sm font-semibold text-espresso focus:outline-none focus:ring-2 focus:ring-terracotta/30 disabled:opacity-60"
              >
                {addresses.map((address) => (
                  <option key={address.id} value={address.id}>
                    {address.label}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-espresso-muted absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
            {addresses.find((address) => address.id === selectedAddressId)?.details && (
              <p className="text-xs text-espresso-muted mt-2 leading-relaxed">
                {addresses.find((address) => address.id === selectedAddressId)?.details}
              </p>
            )}
            {disabled && (
              <p className="text-xs text-espresso-light mt-2">
                Finish the current order before changing its delivery address.
              </p>
            )}
          </>
        ) : (
          <p className="text-sm text-espresso-muted">
            No saved Swiggy addresses were found. Add an address to your Swiggy account, then reconnect.
          </p>
        )}
      </div>
    </div>
  </section>
);
