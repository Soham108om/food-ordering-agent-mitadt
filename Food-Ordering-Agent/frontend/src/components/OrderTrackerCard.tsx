'use client';

import React from 'react';
import { Bike, CheckCircle2, Clock } from 'lucide-react';

interface TrackingSummary {
  status?: string | null;
  estimated_delivery?: string | null;
  message?: string | null;
}

interface OrderTrackerCardProps {
  orderId?: string;
  orderStatus?: string;
  trackingSummary?: TrackingSummary | null;
  trackingError?: string | null;
}

const getProgressStage = (status?: string | null): number => {
  const normalized = (status || '').toLowerCase().replace(/[\s-]+/g, '_');
  if (!normalized) return -1;
  if (/cancel|reject|fail/.test(normalized)) return -2;
  if (/deliver|complete/.test(normalized)) return 3;
  if (/out_for_delivery|picked_up|in_transit|on_the_way/.test(normalized)) return 2;
  if (/prepar|cook|ready/.test(normalized)) return 1;
  if (/placed|confirm|accept|received/.test(normalized)) return 0;
  return -1;
};

export const OrderTrackerCard: React.FC<OrderTrackerCardProps> = ({
  orderId,
  orderStatus,
  trackingSummary,
  trackingError
}) => {
  if (!orderId && !trackingSummary && !trackingError) return null;
  const status = trackingSummary?.status;
  const progressStage = getProgressStage(status);
  const milestones = ['Order confirmed', 'Preparing', 'Out for delivery', 'Delivered'];

  return (
    <section className="bg-white border border-sand-dark rounded-3xl p-6 shadow-warm-md mb-10">
      <div className="flex items-center space-x-3 mb-4 border-b border-sand-dark pb-4">
        <div className="w-10 h-10 rounded-full bg-olive-light border border-olive-border/60 flex items-center justify-center text-olive">
          <Bike className="w-5 h-5" />
        </div>
        <div>
          <h2 className="font-serif text-xl font-bold text-espresso">Order tracking</h2>
          <p className="text-xs text-espresso-muted">
            Order ID: <span className="font-mono font-bold text-espresso">{orderId || 'Active Swiggy Order'}</span>
          </p>
        </div>
      </div>

      <div className="bg-sand-light p-4 rounded-2xl border border-sand-dark/60 mb-5 space-y-3 text-sm">
        {orderStatus && (
          <div className="flex items-center gap-2 text-xs">
            <CheckCircle2 className="w-4 h-4 text-olive" />
            <span className="font-semibold text-espresso">Order placement:</span>
            <span className="font-mono bg-olive-light text-olive border border-olive-border/60 px-2.5 py-0.5 rounded-full font-bold">
              {orderStatus}
            </span>
          </div>
        )}
        {status ? (
          <p className="font-semibold text-espresso">
            Latest Swiggy status: <span className="font-mono">{status}</span>
          </p>
        ) : (
          <p className="text-espresso-muted">Swiggy has not provided a readable tracking status.</p>
        )}
        {trackingSummary?.estimated_delivery && (
          <p className="flex items-center gap-2 text-xs text-espresso-muted">
            <Clock className="w-3.5 h-3.5 text-terracotta" />
            <span>Estimated delivery: <strong className="text-espresso">{trackingSummary.estimated_delivery}</strong></span>
          </p>
        )}
        {trackingSummary?.message && (
          <p className="text-xs text-espresso-muted">{trackingSummary.message}</p>
        )}
        {trackingError && (
          <p role="status" className="text-xs text-warmamber">{trackingError}</p>
        )}
      </div>

      {progressStage >= 0 && (
        <div className="space-y-2" aria-label="Order progress">
          <div className="flex justify-between gap-2 text-[10px] sm:text-xs font-semibold text-espresso">
            {milestones.map((milestone, index) => (
              <span key={milestone} className={index <= progressStage ? 'text-olive' : 'text-espresso-muted'}>
                {milestone}
              </span>
            ))}
          </div>
          <div
            className="h-2 w-full bg-sand rounded-full overflow-hidden"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={((progressStage + 1) / milestones.length) * 100}
            aria-label="Provider-reported order progress"
          >
            <div
              className="h-full bg-olive rounded-full transition-all"
              style={{ width: `${((progressStage + 1) / milestones.length) * 100}%` }}
            />
          </div>
        </div>
      )}

      {progressStage === -2 && (
        <p className="text-sm font-semibold text-warmamber">The provider reports that this order was cancelled or failed.</p>
      )}
    </section>
  );
};
