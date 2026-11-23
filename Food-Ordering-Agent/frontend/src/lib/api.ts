export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface ReorderContext {
  restaurant_id: string;
  restaurant_name: string;
  item_id: string;
  item_name: string;
  is_veg: boolean;
  last_seen_price: number;
}

let addressesRequest: Promise<any> | null = null;

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

export async function logoutSwiggy() {
  const res = await fetch(`${API_BASE}/auth/logout`, {
    method: 'POST',
    credentials: 'include'
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to log out of Swiggy' }));
    throw new Error(error.detail || 'Failed to log out of Swiggy');
  }
  return res.json();
}

export async function fetchAddresses() {
  if (!addressesRequest) {
    addressesRequest = (async () => {
      const res = await fetch(`${API_BASE}/agent/addresses`, { credentials: 'include' });
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to fetch Swiggy addresses' }));
        throw new Error(error.detail || 'Failed to fetch Swiggy addresses');
      }
      return res.json();
    })();
  }

  const request = addressesRequest;
  try {
    return await request;
  } finally {
    if (addressesRequest === request) {
      addressesRequest = null;
    }
  }
}

export async function startAgent(
  userRequest: string,
  addressId?: string,
  allowRestaurantSelection: boolean = true,
  allowItemSelection: boolean = true,
  vegetarianPreference: boolean = false,
  reorderContext?: ReorderContext
) {
  const res = await fetch(`${API_BASE}/agent/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      user_request: userRequest,
      selected_address_id: addressId,
      allow_restaurant_selection: allowRestaurantSelection,
      allow_item_selection: allowItemSelection,
      vegetarian_preference: vegetarianPreference,
      reorder_context: reorderContext
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

export async function respondToAgent(
  paymentMethod?: string,
  relaxedConstraints?: Record<string, any>,
  selectedMenuItemId?: string,
  selectedRestaurantId?: string
) {
  const res = await fetch(`${API_BASE}/agent/respond`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      payment_method: paymentMethod,
      relaxed_constraints: relaxedConstraints,
      selected_menu_item_id: selectedMenuItemId,
      selected_restaurant_id: selectedRestaurantId
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to submit user response' }));
    throw new Error(err.detail || 'Failed to submit user response');
  }
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
