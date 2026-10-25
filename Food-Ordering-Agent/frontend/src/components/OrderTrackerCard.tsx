'use client';

import React from 'react';
import { Bike, CheckCircle2, Clock } from 'lucide-react';

interface OrderTrackerCardProps {
  orderId?: string;
  orderStatus?: string;
  trackingResult?: any;
}

export const OrderTrackerCard: React.FC<OrderTrackerCardProps> = ({
  orderId,
  orderStatus,
  trackingResult
}) => {
  if (!orderId && !trackingResult) return null;

  return (
    <section className="bg-white border border-sand-dark rounded-3xl p-6 shadow-warm-md mb-10">
      <div className="flex items-center space-x-3 mb-4 border-b border-sand-dark pb-4">
        <div className="w-10 h-10 rounded-full bg-olive-light border border-olive-border/60 flex items-center justify-center text-olive">
          <Bike className="w-5 h-5" />
        </div>
        <div>
          <h2 className="font-serif text-xl font-bold text-espresso">
            Your food is on its way.
          </h2>
          <p className="text-xs text-espresso-muted">
            Order ID: <span className="font-mono font-bold text-espresso">{orderId || 'Active Swiggy Order'}</span>
          </p>
        </div>
      </div>

      <div className="bg-sand-light p-4 rounded-2xl border border-sand-dark/60 mb-5 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-olive" />
          <span className="font-semibold text-espresso">Order Status:</span>
          <span className="font-mono bg-olive-light text-olive border border-olive-border/60 px-2.5 py-0.5 rounded-full font-bold">
            {orderStatus || 'PLACED'}
          </span>
        </div>

        <div className="flex items-center space-x-1.5 text-espresso-muted">
          <Clock className="w-3.5 h-3.5 text-terracotta" />
          <span>Live Swiggy MCP Tracking</span>
        </div>
      </div>

      {/* Delivery Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs font-semibold text-espresso">
          <span>Order Confirmed</span>
          <span>Preparing</span>
          <span>Out for Delivery</span>
        </div>
        <div className="h-2 w-full bg-sand rounded-full overflow-hidden">
          <div className="h-full bg-olive rounded-full w-3/4 animate-pulse" />
        </div>
      </div>
    </section>
  );
};
