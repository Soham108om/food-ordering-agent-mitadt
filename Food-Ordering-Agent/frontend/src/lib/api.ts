export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function fetchAuthStatus() {
  const res = await fetch(`${API_BASE}/auth/status`, { credentials: 'include' });
  if (!res.ok) throw new Error('Failed to fetch auth status');
  return res.json();
}

export async function initiateSwiggyLogin() {
  const res = await fetch(`${API_BASE}/auth/login`, { credentials: 'include' });
  if (!res.ok) throw new Error('Failed to initiate login');
  return res.json();
}

export async function fetchAddresses() {
  const res = await fetch(`${API_BASE}/agent/addresses`, { credentials: 'include' });
  if (!res.ok) throw new Error('Failed to fetch Swiggy addresses');
  return res.json();
}

export async function startAgent(userRequest: string, addressId?: string) {
  const res = await fetch(`${API_BASE}/agent/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      user_request: userRequest,
      selected_address_id: addressId
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to start agent' }));
    throw new Error(err.detail || 'Failed to start agent');
  }
  return res.json();
}

export async function fetchAgentState(sessionId: string) {
  const res = await fetch(`${API_BASE}/agent/state/${sessionId}`, { credentials: 'include' });
  if (!res.ok) throw new Error('Failed to fetch agent state');
  return res.json();
}

export async function respondToAgent(paymentMethod?: string, relaxedConstraints?: Record<string, any>) {
  const res = await fetch(`${API_BASE}/agent/respond`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      payment_method: paymentMethod,
      relaxed_constraints: relaxedConstraints
    }),
  });
  if (!res.ok) throw new Error('Failed to submit user response');
  return res.json();
}

export async function confirmOrder(paymentMethod: string = 'COD') {
  const res = await fetch(`${API_BASE}/agent/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      user_confirmation: true,
      payment_method: paymentMethod
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Order placement failed' }));
    throw new Error(err.detail || 'Order placement failed');
  }
  return res.json();
}
