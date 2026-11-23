/**
 * API client for the mini-project extension modules.
 *
 *  Unit-3 : Long-Term Memory + Feedback Loop   -> /memory/*
 *  Unit-4 : Multi-Agent System                 -> /specialists/*
 */

import { API_BASE } from './api';

/* ------------------------------------------------------------------ */
/* Unit-3 : Long-Term Memory + Feedback Loop                          */
/* ------------------------------------------------------------------ */

export interface Weights {
  w1: number;
  w2: number;
  w3: number;
}

export interface MemoryProfile {
  user_id: string;
  weights: Weights;
  preferences: Record<string, any>;
  interaction_count: number;
  accept_count: number;
  reject_count: number;
  cold_start: boolean;
  recent_feedback: FeedbackEvent[];
  created_at?: string;
  updated_at?: string;
}

export interface FeedbackEvent {
  id: number;
  target_type: string;
  target_name: string;
  accepted: boolean;
  reason: string;
  attributes: Weights;
  weights_before: Weights;
  weights_after: Weights;
  created_at: string;
}

export interface FeedbackResponse {
  user_id: string;
  accepted: boolean;
  attributes: Weights;
  weights_before: Weights;
  weights_after: Weights;
  delta: Weights;
}

export interface WeightSpec {
  utility_function: string;
  dimensions: Record<string, string>;
  cold_start_weights: Weights;
  learning_rate: number;
  update_rule: string;
}

export async function fetchWeightSpec(): Promise<WeightSpec> {
  const res = await fetch(`${API_BASE}/memory/demo/weights`, { credentials: 'include' });
  if (!res.ok) throw new Error('Failed to fetch weight spec');
  return res.json();
}

export async function fetchMemoryProfile(userId: string): Promise<MemoryProfile> {
  const res = await fetch(`${API_BASE}/memory/${encodeURIComponent(userId)}`, {
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to fetch memory profile');
  return res.json();
}

export async function fetchFeedbackHistory(userId: string): Promise<FeedbackEvent[]> {
  const res = await fetch(`${API_BASE}/memory/${encodeURIComponent(userId)}/history`, {
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to fetch feedback history');
  const data = await res.json();
  return data.events || [];
}

export async function recordFeedback(
  userId: string,
  payload: {
    accepted: boolean;
    target_name?: string;
    reason?: string;
    price?: number;
    eta?: number;
    rating?: number;
  }
): Promise<FeedbackResponse> {
  const res = await fetch(`${API_BASE}/memory/${encodeURIComponent(userId)}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to record feedback' }));
    throw new Error(err.detail || 'Failed to record feedback');
  }
  return res.json();
}

export async function observeRequest(
  userId: string,
  requirements: Record<string, any>
): Promise<{ user_id: string; preferences: Record<string, any>; weights: Weights }> {
  const res = await fetch(`${API_BASE}/memory/${encodeURIComponent(userId)}/observe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(requirements),
  });
  if (!res.ok) throw new Error('Failed to observe request');
  return res.json();
}

export async function resetMemory(userId: string): Promise<{ user_id: string; weights: Weights }> {
  const res = await fetch(`${API_BASE}/memory/${encodeURIComponent(userId)}/reset`, {
    method: 'POST',
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to reset memory');
  return res.json();
}

/* ------------------------------------------------------------------ */
/* Unit-4 : Multi-Agent System                                        */
/* ------------------------------------------------------------------ */

export interface SpecialistInfo {
  name: string;
  dimension: string;
  constraint_type: 'HARD' | 'SOFT';
  join_weight: number;
}

export interface SpecialistRegistry {
  supervisor: string;
  execution_model: string;
  specialist_count: number;
  specialists: SpecialistInfo[];
}

export interface Verdict {
  specialist: string;
  dimension: string;
  passed: boolean;
  is_hard_constraint: boolean;
  score: number;
  reason: string;
  weight: number;
  metadata: Record<string, any>;
}

export interface RankedItem {
  rank: number;
  item_id: string;
  name: string;
  utility: number;
  price: number;
  eta: number;
  rating: number;
}

export interface RejectedItem {
  item_id: string;
  name: string;
  reason: string;
}

export interface SpecialistStats {
  dimension: string;
  hard_constraint: boolean;
  weight: number;
  evaluated: number;
  passed: number;
  failed: number;
  avg_score: number;
}

export interface SupervisorReport {
  supervisor: string;
  specialist_count: number;
  specialists: string[];
  context: Record<string, any>;
  total_candidates: number;
  accepted_count: number;
  rejected_count: number;
  ranking: RankedItem[];
  rejections: RejectedItem[];
  per_specialist_stats: Record<string, SpecialistStats>;
  winner: {
    candidate: any;
    verdicts: Verdict[];
    utility: number;
    decision: string;
    explanation: string;
  } | null;
  elapsed_ms: number;
  context_description?: string;
}

export async function fetchSpecialistRegistry(): Promise<SpecialistRegistry> {
  const res = await fetch(`${API_BASE}/specialists/registry`, { credentials: 'include' });
  if (!res.ok) throw new Error('Failed to fetch specialist registry');
  return res.json();
}

export async function fetchSpecialistDemo(): Promise<SupervisorReport> {
  const res = await fetch(`${API_BASE}/specialists/demo`, { credentials: 'include' });
  if (!res.ok) throw new Error('Failed to run specialist demo');
  return res.json();
}
