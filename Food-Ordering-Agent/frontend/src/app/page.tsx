'use client';

import React, { useState, useEffect } from 'react';
import { Sparkles, ArrowRight, ShieldAlert, AlertCircle } from 'lucide-react';

import { Navbar } from '../components/Navbar';
import { AgentTimeline } from '../components/AgentTimeline';
import { RequirementCard } from '../components/RequirementCard';
import { RestaurantGrid } from '../components/RestaurantGrid';
import { RestaurantCompareModal } from '../components/RestaurantCompareModal';
import { MenuGrid } from '../components/MenuGrid';
import { AgentInsightBanner } from '../components/AgentInsightBanner';
import { CartSummary } from '../components/CartSummary';
import { ReplanningModal } from '../components/ReplanningModal';
import { PaymentSelectionModal } from '../components/PaymentSelectionModal';
import { HumanConfirmationModal } from '../components/HumanConfirmationModal';
import { OrderTrackerCard } from '../components/OrderTrackerCard';
import { DeliveryAddressSelector } from '../components/DeliveryAddressSelector';
import type { SavedAddress } from '../components/DeliveryAddressSelector';
import { FoodSafetyPreferences } from '../components/FoodSafetyPreferences';
import { FavoritesPanel, isFavoriteEntry } from '../components/FavoritesPanel';
import type { FavoriteEntry } from '../components/FavoritesPanel';
import { ReorderPanel, isReorderEntry } from '../components/ReorderPanel';
import type { ReorderEntry } from '../components/ReorderPanel';
import type { Restaurant } from '../components/RestaurantGrid';
import type { MenuItem } from '../components/MenuGrid';

import {
  fetchAuthStatus,
  initiateSwiggyLogin,
  logoutSwiggy,
  fetchAddresses,
  startAgent,
  respondToAgent,
  confirmOrder,
  type ReorderContext,
  API_BASE
} from '../lib/api';

export default function Home() {
  const [authenticated, setAuthenticated] = useState<boolean>(false);
  const [addressId, setAddressId] = useState<string>('');
  const [savedAddresses, setSavedAddresses] = useState<SavedAddress[]>([]);
  const [addressesLoading, setAddressesLoading] = useState<boolean>(false);
  const [vegetarianOnly, setVegetarianOnly] = useState<boolean>(false);
  const [allergens, setAllergens] = useState<string[]>([]);
  const [preferencesLoaded, setPreferencesLoaded] = useState<boolean>(false);
  const [preferencesLoadWarning, setPreferencesLoadWarning] = useState<string | null>(null);
  const [preferencesSaveWarning, setPreferencesSaveWarning] = useState<string | null>(null);
  const [favorites, setFavorites] = useState<FavoriteEntry[]>([]);
  const [favoritesLoaded, setFavoritesLoaded] = useState<boolean>(false);
  const [favoritesLoadWarning, setFavoritesLoadWarning] = useState<string | null>(null);
  const [favoritesSaveWarning, setFavoritesSaveWarning] = useState<string | null>(null);
  const [orderHistory, setOrderHistory] = useState<ReorderEntry[]>([]);
  const [orderHistoryLoaded, setOrderHistoryLoaded] = useState<boolean>(false);
  const [orderHistoryLoadWarning, setOrderHistoryLoadWarning] = useState<string | null>(null);
  const [orderHistorySaveWarning, setOrderHistorySaveWarning] = useState<string | null>(null);
  const [prompt, setPrompt] = useState<string>(
    'I want a vegetarian pizza under ₹500 delivered within 30 minutes.'
  );

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [agentState, setAgentState] = useState<any>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [isLoggingOut, setIsLoggingOut] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Modals
  const [isCompareOpen, setIsCompareOpen] = useState<boolean>(false);
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState<boolean>(false);
  const [isConfirmOpen, setIsConfirmOpen] = useState<boolean>(false);
  const [isPlacingOrder, setIsPlacingOrder] = useState<boolean>(false);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem('food-agent-food-safety-v1');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed && typeof parsed === 'object') {
          setVegetarianOnly(parsed.vegetarianOnly === true);
          const savedAllergens = Array.isArray(parsed.allergens)
            ? parsed.allergens.filter((value: unknown): value is string => typeof value === 'string')
              .map((value: string) => value.trim().slice(0, 60))
              .filter(Boolean)
            : [];
          setAllergens(Array.from(new Map<string, string>(
            savedAllergens.map((value: string): [string, string] => [value.toLowerCase(), value])
          ).values()).slice(0, 20));
        }
      }
    } catch {
      setPreferencesLoadWarning('Could not load saved preferences from this browser; defaults are being used.');
    } finally {
      setPreferencesLoaded(true);
    }
  }, []);

  useEffect(() => {
    if (!preferencesLoaded) return;
    try {
      window.localStorage.setItem(
        'food-agent-food-safety-v1',
        JSON.stringify({ vegetarianOnly, allergens })
      );
      setPreferencesSaveWarning(null);
    } catch {
      setPreferencesSaveWarning('Could not save preferences in this browser.');
    }
  }, [vegetarianOnly, allergens, preferencesLoaded]);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem('food-agent-favorites-v1');
      if (saved) {
        const parsed: unknown = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          setFavorites(parsed.filter(isFavoriteEntry));
        }
      }
    } catch {
      setFavoritesLoadWarning('Could not load favorites from this browser.');
    } finally {
      setFavoritesLoaded(true);
    }
  }, []);

  useEffect(() => {
    if (!favoritesLoaded) return;
    try {
      window.localStorage.setItem('food-agent-favorites-v1', JSON.stringify(favorites));
      setFavoritesSaveWarning(null);
    } catch {
      setFavoritesSaveWarning('Could not save favorites in this browser.');
    }
  }, [favorites, favoritesLoaded]);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem('food-agent-order-history-v1');
      if (saved) {
        const parsed: unknown = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          setOrderHistory(parsed.filter(isReorderEntry).slice(0, 20));
        }
      }
    } catch {
      setOrderHistoryLoadWarning('Could not load previous orders from this browser.');
    } finally {
      setOrderHistoryLoaded(true);
    }
  }, []);

  useEffect(() => {
    if (!orderHistoryLoaded) return;
    try {
      window.localStorage.setItem('food-agent-order-history-v1', JSON.stringify(orderHistory));
      setOrderHistorySaveWarning(null);
    } catch {
      setOrderHistorySaveWarning('Could not save order history in this browser.');
    }
  }, [orderHistory, orderHistoryLoaded]);

  useEffect(() => {
    if (
      !orderHistoryLoaded ||
      agentState.current_step !== 'TRACK' ||
      !agentState.order_id ||
      !agentState.selected_restaurant?.restaurant_id ||
      !agentState.selected_restaurant?.name ||
      !agentState.selected_item?.item_id ||
      !agentState.selected_item?.name ||
      typeof agentState.selected_item?.price !== 'number'
    ) return;

    const completedOrder: ReorderEntry = {
      orderId: String(agentState.order_id),
      orderedAt: new Date().toISOString(),
      restaurantId: String(agentState.selected_restaurant.restaurant_id),
      restaurantName: String(agentState.selected_restaurant.name),
      itemId: String(agentState.selected_item.item_id),
      itemName: String(agentState.selected_item.name),
      isVeg: agentState.selected_item.is_veg === true,
      lastSeenPrice: agentState.selected_item.price
    };

    setOrderHistory((current) => current.some((entry) => entry.orderId === completedOrder.orderId)
      ? current
      : [completedOrder, ...current].slice(0, 20));
  }, [agentState, orderHistoryLoaded]);

  // Check auth status on load
  useEffect(() => {
    fetchAuthStatus()
      .then((res) => {
        setAuthenticated(res.authenticated);
        if (res.authenticated) {
          setAddressesLoading(true);
          fetchAddresses()
            .then((a) => {
              const addresses: SavedAddress[] = Array.isArray(a.addresses) ? a.addresses : [];
              if (addresses.length === 0 && a.first_address_id) {
                addresses.push({
                  id: a.first_address_id,
                  label: 'Saved address 1',
                  details: ''
                });
              }
              setSavedAddresses(addresses);
              const fallbackAddressId = addresses[0]?.id || '';
              setAddressId((current) => current || a.first_address_id || fallbackAddressId);
            })
            .catch((err) => {
              setErrorMessage(err.message || 'Failed to load saved delivery addresses');
            })
            .finally(() => setAddressesLoading(false));
        }
      })
      .catch((err) => {
        setErrorMessage(err.message || 'Failed to check Swiggy connection');
      });
  }, []);

  // Listen to live SSE updates when session is active
  useEffect(() => {
    if (!sessionId) return;

    const eventSource = new EventSource(`${API_BASE}/stream/${sessionId}`, { withCredentials: true });

    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.state) {
          setAgentState(data.state);
        }
      } catch (err) {}
    };

    eventSource.addEventListener('agent_update', (e: any) => {
      try {
        const data = JSON.parse(e.data);
        if (data.state) {
          setAgentState((prevState: any) => ({
            ...data.state,
            // Preserve user manual selection if user manually clicked a different dish
            selected_item: prevState?.user_selected_override ? prevState.selected_item : data.state.selected_item
          }));

          // Auto-trigger appropriate modal based on exact graph step
          if (data.current_step === 'PAYMENT' && data.needs_user_input) {
            setIsPaymentModalOpen(true);
            setIsConfirmOpen(false);
          } else if (data.current_step === 'CONFIRM_ORDER' && data.needs_user_input) {
            setIsPaymentModalOpen(false);
            setIsConfirmOpen(true);
          }
        }
      } catch (err) {}
    });

    eventSource.addEventListener('agent_idle', (e: any) => {
      try {
        const data = JSON.parse(e.data);
        if (['END', 'TRACK', 'ERROR'].includes(data.step)) {
          eventSource.close();
        }
      } catch {
        // Keep the connection open so EventSource can reconnect after transient errors.
      }
    });

    return () => {
      eventSource.close();
    };
  }, [sessionId]);

  // OAuth Login Click
  const handleLogin = async () => {
    try {
      const res = await initiateSwiggyLogin();
      if (res.authorization_url) {
        window.location.href = res.authorization_url;
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Login initiation failed');
    }
  };

  const handleLogout = async () => {
    setIsLoggingOut(true);
    setErrorMessage(null);
    try {
      await logoutSwiggy();
      setAuthenticated(false);
      setAddressId('');
      setSavedAddresses([]);
      setSessionId(null);
      setAgentState({});
      setIsCompareOpen(false);
      setIsPaymentModalOpen(false);
      setIsConfirmOpen(false);

      window.localStorage.removeItem('food-agent-food-safety-v1');
      window.localStorage.removeItem('food-agent-favorites-v1');
      window.localStorage.removeItem('food-agent-order-history-v1');
      setVegetarianOnly(false);
      setAllergens([]);
      setFavorites([]);
      setOrderHistory([]);
    } catch (err: any) {
      setErrorMessage(err.message || 'Logout failed');
    } finally {
      setIsLoggingOut(false);
    }
  };

  const startAgentWorkflow = async (userRequest: string, reorderContext?: ReorderContext) => {
    if (!userRequest.trim() || loading || !preferencesLoaded) return;
    // Reset workflow-specific states immediately for NEW request (preserving Swiggy OAuth & Address)
    setLoading(true);
    setErrorMessage(null);
    setIsCompareOpen(false);
    setIsPaymentModalOpen(false);
    setIsConfirmOpen(false);
    setAgentState({});
    setSessionId(null);

    try {
      const res = await startAgent(userRequest, addressId, true, true, vegetarianOnly, reorderContext);
      setSessionId(res.session_id);
      setAgentState(res.state || {});

      if (res.state?.selected_address_id) {
        setAddressId(res.state.selected_address_id);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Agent launch failed');
    } finally {
      setLoading(false);
    }
  };

  // Start a normal AI recommendation search.
  const handleStartAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    await startAgentWorkflow(prompt);
  };

  const handleReorder = async (order: ReorderEntry) => {
    const request = `Find ${order.itemName} again from ${order.restaurantName}`;
    setPrompt(request);
    await startAgentWorkflow(request, {
      restaurant_id: order.restaurantId,
      restaurant_name: order.restaurantName,
      item_id: order.itemId,
      item_name: order.itemName,
      is_veg: order.isVeg,
      last_seen_price: order.lastSeenPrice
    });
  };

  // Interactive Manual Dish Selection Override
  const handleSelectItem = (item: any) => {
    setAgentState((prev: any) => ({
      ...prev,
      selected_item: item,
      user_selected_override: true
    }));
  };

  const handleConfirmItemSelection = async () => {
    if (!selectedItem?.item_id || loading) return;

    setLoading(true);
    try {
      const res = await respondToAgent(undefined, undefined, selectedItem.item_id);
      setAgentState(res.state || {});
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to confirm dish selection');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectRestaurant = (restaurant: any) => {
    setAgentState((prev: any) => ({
      ...prev,
      selected_restaurant: restaurant,
      selected_restaurant_id: restaurant.restaurant_id
    }));
  };

  const toggleFavorite = (favorite: FavoriteEntry) => {
    if (!favoritesLoaded) return;
    setFavorites((current) => {
      const isSaved = current.some((entry) => entry.type === favorite.type && entry.id === favorite.id);
      return isSaved
        ? current.filter((entry) => entry.type !== favorite.type || entry.id !== favorite.id)
        : [...current, favorite];
    });
  };

  const favoriteRestaurantIds = favorites
    .filter((favorite) => favorite.type === 'restaurant')
    .map((favorite) => favorite.id);
  const favoriteDishIds = favorites
    .filter((favorite) => favorite.type === 'dish')
    .map((favorite) => favorite.id);

  const handleConfirmRestaurantSelection = async () => {
    if (!selectedRest?.restaurant_id || loading) return;

    setLoading(true);
    try {
      const res = await respondToAgent(undefined, undefined, undefined, selectedRest.restaurant_id);
      setAgentState(res.state || {});
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to confirm restaurant selection');
    } finally {
      setLoading(false);
    }
  };

  // User Selects Payment Method -> Resumes Graph to CONFIRM_ORDER
  const handleSelectPaymentMethod = async (method: string) => {
    setLoading(true);
    setIsPaymentModalOpen(false);
    try {
      const res = await respondToAgent(method);
      setAgentState((prev: any) => ({
        ...(res.state || {}),
        selected_item: prev?.user_selected_override ? prev.selected_item : res.state?.selected_item
      }));
      if (res.state?.current_step === 'CONFIRM_ORDER') {
        setIsConfirmOpen(true);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to submit payment method');
    } finally {
      setLoading(false);
    }
  };

  // Constraint Relaxation Action (Re-plan)
  const handleRelaxConstraints = async (newConstraints: {
    max_budget?: number;
    max_delivery_minutes?: number;
    food?: string;
    vegetarian?: boolean;
  }) => {
    setLoading(true);
    try {
      const res = await respondToAgent(undefined, newConstraints);
      setAgentState(res.state || {});
    } catch (err: any) {
      setErrorMessage(err.message || 'Replanning failed');
    } finally {
      setLoading(false);
    }
  };

  // Order Placement Action (Explicit Human Confirmation)
  const handleConfirmOrder = async (paymentMethod: string) => {
    setIsPlacingOrder(true);
    try {
      const res = await confirmOrder(paymentMethod);
      setAgentState((prev: any) => ({
        ...(res.state || {}),
        selected_item: prev?.user_selected_override ? prev.selected_item : res.state?.selected_item
      }));
      setIsConfirmOpen(false);
    } catch (err: any) {
      setErrorMessage(err.message || 'Order placement failed');
    } finally {
      setIsPlacingOrder(false);
    }
  };

  const requirements = agentState.requirements;
  const currentStep = agentState.current_step || 'START';
  const addressChangeLocked = Boolean(
    sessionId && !['TRACK', 'END', 'ERROR'].includes(currentStep)
  );
  const dietaryFilterLocked = Boolean(
    sessionId && !['TRACK', 'END', 'ERROR'].includes(currentStep)
  );
  const selectedAddress = savedAddresses.find((address) => address.id === addressId);
  const needsUserInput = agentState.needs_user_input;
  const replanningRequired = agentState.replanning_required;
  // Errors raised by the backend graph itself (not by the HTTP layer) surface
  // through agent_state.error_message rather than errorMessage.
  const agentError = agentState.error_message || null;

  const restaurants = agentState.ranked_restaurants || agentState.parsed_restaurants || [];
  const selectedRest = agentState.selected_restaurant;
  const menuItems = agentState.ranked_menu_items || agentState.filtered_menu_items || [];
  const selectedItem = agentState.selected_item;

  // Determine if Replanning modal should be open
  const isReplanOpen = Boolean(
    replanningRequired ||
    currentStep === 'REPLAN' ||
    (needsUserInput && (currentStep === 'REPLAN' || currentStep === 'FILTER_RESTAURANTS' || currentStep === 'FILTER_MENU'))
  );

  // Determine if Cart summary should be visible (only when workflow reached cart/payment/order)
  const showCartSummary = Boolean(
    selectedItem &&
    selectedItem.name &&
    ['CART', 'PAYMENT', 'CONFIRM_ORDER', 'PLACE_ORDER', 'TRACK'].includes(currentStep)
  );

  return (
    <div className="min-h-screen bg-cream text-espresso pb-20">
      {/* Editorial Header */}
      <Navbar
        authenticated={authenticated}
        onLoginClick={handleLogin}
        onLogoutClick={handleLogout}
        isLoggingOut={isLoggingOut}
        selectedAddressLabel={selectedAddress?.label}
      />

      <main className="max-w-[1440px] mx-auto px-6 md:px-10 pt-8">
        {/* Swiggy Auth Warning Banner if not connected */}
        {!authenticated && (
          <div className="bg-warmamber-light border border-warmamber-border rounded-3xl p-5 mb-8 flex items-center justify-between shadow-warm-sm">
            <div className="flex items-center space-x-3 text-warmamber">
              <ShieldAlert className="w-6 h-6 shrink-0 text-warmamber" />
              <div className="text-xs text-espresso-muted">
                <p className="font-serif font-bold text-espresso text-sm">Swiggy OAuth Required for Live MCP Tools</p>
                <p>Connect your Swiggy account to perform real restaurant searches, cart sync, and order placement.</p>
              </div>
            </div>
            <button
              onClick={handleLogin}
              className="bg-terracotta hover:bg-terracotta-hover text-white font-bold text-xs px-5 py-2.5 rounded-full transition shadow-warm-sm shrink-0"
            >
              Connect Swiggy
            </button>
          </div>
        )}

        {/* Global Error Banner */}
        {errorMessage && (
          <div className="bg-warmred-light border border-warmred-border text-warmred p-4 rounded-2xl mb-8 text-xs flex items-center justify-between shadow-warm-sm">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 shrink-0 text-warmred" />
              <span className="font-mono">{errorMessage}</span>
            </div>
            <button onClick={() => setErrorMessage(null)} className="text-xs font-bold underline">
              Dismiss
            </button>
          </div>
        )}

        {/* Backend Graph Error Banner */}
        {agentError && (
          <div className="bg-warmred-light border border-warmred-border text-warmred p-4 rounded-2xl mb-8 text-xs flex items-center justify-between shadow-warm-sm">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 shrink-0 text-warmred" />
              <span className="font-mono">Agent failed at step {currentStep}: {agentError}</span>
            </div>
          </div>
        )}

        {/* Section 4: Main Request Area (Editorial Food Concierge) */}
        <section className="mb-10">
          <FoodSafetyPreferences
            vegetarianOnly={vegetarianOnly}
            onVegetarianOnlyChange={setVegetarianOnly}
            allergens={allergens}
            onAddAllergen={(allergen) => {
              setAllergens((current) => {
                if (current.some((value) => value.toLowerCase() === allergen.toLowerCase())) return current;
                return [...current, allergen].slice(0, 20);
              });
            }}
            onRemoveAllergen={(allergen) => {
              setAllergens((current) => current.filter((value) => value !== allergen));
            }}
            isLoading={!preferencesLoaded}
            dietaryDisabled={dietaryFilterLocked}
            activeVegetarianOverride={Boolean(
              agentState.vegetarian_preference && requirements?.vegetarian === false
            )}
            storageWarning={preferencesLoadWarning || preferencesSaveWarning}
          />
          {authenticated && (
            <DeliveryAddressSelector
              addresses={savedAddresses}
              selectedAddressId={addressId}
              onSelect={(nextAddressId) => {
                if (nextAddressId === addressId) return;
                setAddressId(nextAddressId);
                if (sessionId && !addressChangeLocked) {
                  setSessionId(null);
                  setAgentState({});
                  setErrorMessage(null);
                  setIsCompareOpen(false);
                  setIsPaymentModalOpen(false);
                  setIsConfirmOpen(false);
                }
              }}
              isLoading={addressesLoading}
              disabled={addressChangeLocked}
            />
          )}
          {favoritesLoaded && (
            <FavoritesPanel
              favorites={favorites}
              onRemove={(favorite) => toggleFavorite(favorite)}
              storageWarning={favoritesLoadWarning || favoritesSaveWarning}
            />
          )}
          {orderHistoryLoaded && (
            <ReorderPanel
              orders={orderHistory}
              onReorder={handleReorder}
              disabled={loading || !preferencesLoaded}
              storageWarning={orderHistoryLoadWarning || orderHistorySaveWarning}
            />
          )}
          <div className="max-w-3xl mb-4">
            <h2 className="font-serif text-3xl md:text-4xl font-bold text-espresso tracking-tight mb-2">
              What are you craving?
            </h2>
            <p className="text-xs md:text-sm text-espresso-muted font-medium">
              Tell our intelligent agent what food you'd like to order, budget limits, or delivery constraints.
            </p>
          </div>

          <form onSubmit={handleStartAgent}>
            <div className="bg-white border border-sand-dark rounded-3xl p-3 shadow-warm-md flex flex-col md:flex-row items-center space-y-3 md:space-y-0 md:space-x-3">
              <div className="flex items-center space-x-3 w-full px-3 py-1">
                <Sparkles className="w-5 h-5 text-terracotta shrink-0" />
                <input
                  type="text"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g., 'I want a vegetarian pizza under ₹500 in 30 min'..."
                  className="w-full bg-transparent border-none text-espresso placeholder-espresso-light focus:outline-none text-sm md:text-base font-medium"
                />
              </div>

              <button
                type="submit"
                disabled={loading || !preferencesLoaded}
                className="w-full md:w-auto bg-terracotta hover:bg-terracotta-hover text-white font-bold px-8 py-3.5 rounded-full flex items-center justify-center space-x-2 text-sm transition shadow-warm-sm shrink-0 disabled:opacity-50"
              >
                <span>{!preferencesLoaded ? 'Loading preferences...' : loading ? 'Finding food...' : 'Find my food'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </form>
        </section>

        {/* Section 5: Lightweight Agent Execution Pipeline */}
        <AgentTimeline
          currentStep={currentStep}
          needsUserInput={needsUserInput}
          replanningRequired={replanningRequired || currentStep === 'REPLAN'}
        />

        {/* Section 6: Editorial Gemini Requirements Summary */}
        {requirements && Object.keys(requirements).length > 0 && (
          <RequirementCard userRequest={agentState.user_request || prompt} requirements={requirements} />
        )}

        {agentState.reorder_item_unavailable && (
          <div className="bg-warmamber-light border border-warmamber-border text-warmamber p-4 rounded-2xl mb-8 text-sm">
            The previous dish could not be matched in the current menu; it may be unavailable or excluded by your dietary filter. Choose an available alternative below. Nothing will be ordered without your confirmation.
          </div>
        )}

        {/* Section 7: Editorial Agent Recommendation Rationale */}
        {selectedRest && selectedRest.name && (
          <AgentInsightBanner
            restaurantName={selectedRest?.name}
            itemName={selectedItem?.name}
            itemPrice={selectedItem?.price}
            deliveryMinutes={selectedRest?.delivery_minutes}
            maxBudget={requirements?.max_budget}
            maxDelivery={requirements?.max_delivery_minutes}
            isVeg={requirements?.vegetarian}
          />
        )}

        {/* Section 8: Places That Fit (Restaurant Grid) */}
        {restaurants.length > 0 && (
          <RestaurantGrid
            restaurants={restaurants}
            selectedRestaurantId={selectedRest?.restaurant_id}
            onCompareClick={() => setIsCompareOpen(true)}
            onSelectRestaurant={handleSelectRestaurant}
            canConfirmSelection={currentStep === 'SELECT_RESTAURANT' && needsUserInput && !loading}
            isConfirmingSelection={loading && currentStep === 'SELECT_RESTAURANT'}
            onConfirmSelection={handleConfirmRestaurantSelection}
            favoriteRestaurantIds={favoriteRestaurantIds}
            favoritesEnabled={favoritesLoaded}
            onToggleFavorite={(restaurant: Restaurant) => toggleFavorite({
              type: 'restaurant',
              id: restaurant.restaurant_id,
              name: restaurant.name
            })}
          />
        )}

        {/* Section 9: Something You'll Love (Menu Grid with Interactive Override Selection) */}
        {menuItems.length > 0 && (
          <MenuGrid
            menuItems={menuItems}
            selectedItem={selectedItem}
            onSelectItem={handleSelectItem}
            canConfirmSelection={currentStep === 'SELECT_ITEM' && needsUserInput && !loading}
            isConfirmingSelection={loading && currentStep === 'SELECT_ITEM'}
            onConfirmSelection={handleConfirmItemSelection}
            allergens={allergens}
            favoriteDishIds={favoriteDishIds}
            favoritesEnabled={favoritesLoaded}
            previouslyOrderedItemId={agentState.reorder_item_id}
            previouslyOrderedItemName={agentState.reorder_item_name}
            onToggleFavorite={(item: MenuItem) => toggleFavorite({
              type: 'dish',
              id: item.item_id,
              name: item.name,
              restaurantName: selectedRest?.name,
              lastSeenPrice: item.price
            })}
          />
        )}

        {/* Section 10: Your Order (Cart Summary) */}
        {showCartSummary && (
          <CartSummary
            restaurantName={selectedRest?.name}
            selectedItem={selectedItem}
            addressId={addressId}
            addressLabel={selectedAddress?.label}
            addressDetails={selectedAddress?.details}
            cartPricing={agentState.cart_pricing}
            allergens={allergens}
            onProceedToPayment={() => {
              if (agentState.payment_method) {
                setIsConfirmOpen(true);
              } else {
                setIsPaymentModalOpen(true);
              }
            }}
          />
        )}

        {/* Section 14: Order / Tracking Status */}
        {currentStep === 'TRACK' && (
          <OrderTrackerCard
            orderId={agentState.order_id}
            orderStatus={agentState.order_status}
            trackingSummary={agentState.tracking_summary}
            trackingError={agentState.tracking_error}
          />
        )}
      </main>

      {/* Side-by-Side Restaurant Compare Modal */}
      <RestaurantCompareModal
        isOpen={isCompareOpen}
        onClose={() => setIsCompareOpen(false)}
        restaurants={restaurants}
      />

      {/* Section 11: Payment Method Selection Modal */}
      <PaymentSelectionModal
        isOpen={isPaymentModalOpen || (currentStep === 'PAYMENT' && needsUserInput)}
        onSelectPayment={handleSelectPaymentMethod}
        isLoading={loading}
      />

      {/* Section 13: Conversational Re-planning Modal */}
      <ReplanningModal
        isOpen={isReplanOpen}
        onRelaxConstraints={handleRelaxConstraints}
        userRequest={agentState.user_request || prompt}
        currentFood={requirements?.food}
        currentBudget={requirements?.max_budget}
        currentDelivery={requirements?.max_delivery_minutes}
        errorMessage={agentState.error_message}
        noMatchDetails={agentState.no_match_details}
      />

      {/* Section 12: Ready When You Are (Human Confirmation Modal) */}
      <HumanConfirmationModal
        isOpen={isConfirmOpen || (currentStep === 'CONFIRM_ORDER' && needsUserInput)}
        onClose={() => setIsConfirmOpen(false)}
        onConfirmOrder={handleConfirmOrder}
        restaurantName={selectedRest?.name}
        itemName={selectedItem?.name}
        itemPrice={selectedItem?.price}
        addressId={addressId}
        addressLabel={selectedAddress?.label}
        addressDetails={selectedAddress?.details}
        cartPricing={agentState.cart_pricing}
        allergens={allergens}
        isLoading={isPlacingOrder}
      />
    </div>
  );
}
