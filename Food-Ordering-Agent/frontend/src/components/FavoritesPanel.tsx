'use client';

import React from 'react';
import { Heart, Trash2 } from 'lucide-react';

export interface FavoriteEntry {
  type: 'restaurant' | 'dish';
  id: string;
  name: string;
  restaurantName?: string;
  lastSeenPrice?: number;
}

export function isFavoriteEntry(value: unknown): value is FavoriteEntry {
  if (!value || typeof value !== 'object') return false;
  const entry = value as Record<string, unknown>;
  return (
    (entry.type === 'restaurant' || entry.type === 'dish') &&
    typeof entry.id === 'string' &&
    typeof entry.name === 'string' &&
    (entry.restaurantName === undefined || typeof entry.restaurantName === 'string') &&
    (entry.lastSeenPrice === undefined || (typeof entry.lastSeenPrice === 'number' && Number.isFinite(entry.lastSeenPrice)))
  );
}

interface FavoritesPanelProps {
  favorites: FavoriteEntry[];
  onRemove: (favorite: FavoriteEntry) => void;
  storageWarning?: string | null;
}

export const FavoritesPanel: React.FC<FavoritesPanelProps> = ({
  favorites,
  onRemove,
  storageWarning
}) => {
  if (favorites.length === 0 && !storageWarning) return null;

  return (
    <section className="bg-white border border-sand-dark rounded-3xl p-5 mb-6 shadow-warm-sm">
      <div className="flex items-start gap-3 mb-4">
        <div className="w-9 h-9 rounded-full bg-terracotta/10 border border-terracotta/30 flex items-center justify-center text-terracotta shrink-0">
          <Heart className="w-4 h-4 fill-current" />
        </div>
        <div>
          <h2 className="font-serif text-lg font-bold text-espresso">Your favorites</h2>
          <p className="text-xs text-espresso-muted mt-0.5">
            Saved in this browser. Availability and prices can change.
          </p>
        </div>
      </div>

      {storageWarning && (
        <p role="status" className="text-xs text-warmamber mb-3">{storageWarning}</p>
      )}

      {favorites.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {favorites.map((favorite) => (
            <article key={`${favorite.type}:${favorite.id}`} className="flex items-center justify-between gap-3 bg-sand-light/70 border border-sand-dark/60 rounded-2xl p-3">
              <div className="min-w-0">
                <span className="text-[10px] uppercase tracking-wider font-bold text-terracotta">
                  {favorite.type === 'dish' ? 'Dish' : 'Restaurant'}
                </span>
                <p className="font-semibold text-sm text-espresso truncate">{favorite.name}</p>
                {favorite.type === 'dish' && favorite.restaurantName && (
                  <p className="text-xs text-espresso-muted truncate">{favorite.restaurantName}</p>
                )}
                {favorite.type === 'dish' && typeof favorite.lastSeenPrice === 'number' && (
                  <p className="text-[11px] font-mono text-espresso-muted mt-0.5">
                    Last seen ₹{favorite.lastSeenPrice.toFixed(0)}
                  </p>
                )}
              </div>
              <button
                type="button"
                aria-label={`Remove ${favorite.name} from favorites`}
                onClick={() => onRemove(favorite)}
                className="w-8 h-8 rounded-full hover:bg-white flex items-center justify-center text-espresso-muted hover:text-warmred transition shrink-0"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  );
};
