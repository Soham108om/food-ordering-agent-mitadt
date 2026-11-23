'use client';

import React from 'react';
import { ArrowRight, RotateCcw } from 'lucide-react';

export interface ReorderEntry {
  orderId: string;
  orderedAt: string;
  restaurantId: string;
  restaurantName: string;
  itemId: string;
  itemName: string;
  isVeg: boolean;
  lastSeenPrice: number;
}

export function isReorderEntry(value: unknown): value is ReorderEntry {
  if (!value || typeof value !== 'object') return false;
  const entry = value as Record<string, unknown>;
  return (
    typeof entry.orderId === 'string' &&
    typeof entry.orderedAt === 'string' &&
    typeof entry.restaurantId === 'string' &&
    typeof entry.restaurantName === 'string' &&
    typeof entry.itemId === 'string' &&
    typeof entry.itemName === 'string' &&
    typeof entry.isVeg === 'boolean' &&
    typeof entry.lastSeenPrice === 'number' &&
    Number.isFinite(entry.lastSeenPrice)
  );
}

interface ReorderPanelProps {
  orders: ReorderEntry[];
  onReorder: (order: ReorderEntry) => void;
  disabled?: boolean;
  storageWarning?: string | null;
}

export const ReorderPanel: React.FC<ReorderPanelProps> = ({
  orders,
  onReorder,
  disabled = false,
  storageWarning
}) => {
  if (orders.length === 0 && !storageWarning) return null;

  return (
    <section className="bg-white border border-sand-dark rounded-3xl p-5 mb-6 shadow-warm-sm">
      <div className="flex items-start gap-3 mb-4">
        <div className="w-9 h-9 rounded-full bg-olive-light border border-olive-border/60 flex items-center justify-center text-olive shrink-0">
          <RotateCcw className="w-4 h-4" />
        </div>
        <div>
          <h2 className="font-serif text-lg font-bold text-espresso">Order again</h2>
          <p className="text-xs text-espresso-muted mt-0.5">
            We&apos;ll check the current menu and price at your selected address. Nothing is ordered automatically.
          </p>
        </div>
      </div>

      {storageWarning && (
        <p role="status" className="text-xs text-warmamber mb-3">{storageWarning}</p>
      )}

      {orders.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {orders.map((order) => (
            <article key={order.orderId} className="flex items-center justify-between gap-3 bg-sand-light/70 border border-sand-dark/60 rounded-2xl p-3">
              <div className="min-w-0">
                <p className="font-semibold text-sm text-espresso truncate">{order.itemName}</p>
                <p className="text-xs text-espresso-muted truncate">{order.restaurantName}</p>
                <p className="text-[11px] font-mono text-espresso-muted mt-0.5">
                  Last ordered ₹{order.lastSeenPrice.toFixed(0)}
                </p>
              </div>
              <button
                type="button"
                disabled={disabled}
                onClick={() => onReorder(order)}
                className="inline-flex items-center gap-1.5 shrink-0 bg-terracotta hover:bg-terracotta-hover text-white font-semibold px-3 py-2 rounded-full text-xs transition disabled:opacity-50"
              >
                <span>Check again</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
};
