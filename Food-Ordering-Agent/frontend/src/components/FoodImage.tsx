'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { Utensils } from 'lucide-react';

interface FoodImageProps {
  src?: string | null;
  alt: string;
  className: string;
}

const isTrustedSwiggyImage = (src?: string | null): src is string => {
  if (!src) return false;
  try {
    const url = new URL(src);
    return (
      url.protocol === 'https:' &&
      !url.username &&
      !url.password &&
      (url.hostname === 'swiggy.com' || url.hostname.endsWith('.swiggy.com'))
    );
  } catch {
    return false;
  }
};

export const FoodImage: React.FC<FoodImageProps> = ({ src, alt, className }) => {
  const [failed, setFailed] = useState(false);
  const trustedSrc = isTrustedSwiggyImage(src) ? src : null;

  if (!trustedSrc || failed) {
    return (
      <div
        role="img"
        aria-label={`${alt}: photo unavailable`}
        className={`flex items-center justify-center rounded-2xl bg-sand-light border border-sand-dark/60 text-espresso-light ${className}`}
      >
        <div className="flex flex-col items-center gap-1">
          <Utensils className="w-6 h-6" aria-hidden="true" />
          <span className="text-[10px] font-medium">Photo unavailable</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative overflow-hidden rounded-2xl bg-sand-light ${className}`}>
      <Image
        src={trustedSrc}
        alt={alt}
        fill
        unoptimized
        sizes="(max-width: 768px) 100vw, 50vw"
        className="object-cover"
        onError={() => setFailed(true)}
      />
    </div>
  );
};
