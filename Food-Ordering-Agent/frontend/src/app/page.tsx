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

import {
  fetchAuthStatus,
  initiateSwiggyLogin,
  fetchAddresses,
  startAgent,
  respondToAgent,
  confirmOrder,
  API_BASE
} from '../lib/api';

export default function Home() {
  const [authenticated, setAuthenticated] = useState<boolean>(false);
  const [addressId, setAddressId] = useState<string>('');
  const [prompt, setPrompt] = useState<string>(
    'I want a vegetarian pizza under ₹500 delivered within 30 minutes.'
  );

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [agentState, setAgentState] = useState<any>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Modals
  const [isCompareOpen, setIsCompareOpen] = useState<boolean>(false);
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState<boolean>(false);
  const [isConfirmOpen, setIsConfirmOpen] = useState<boolean>(false);
  const [isPlacingOrder, setIsPlacingOrder] = useState<boolean>(false);

  // Check auth status on load
  useEffect(() => {
    fetchAuthStatus()
      .then((res) => {
        setAuthenticated(res.authenticated);
        if (res.authenticated) {
          fetchAddresses()
            .then((a) => {
              if (a.first_address_id) setAddressId(a.first_address_id);
            })
            .catch(() => {});
        }
      })
      .catch(() => {});
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

    eventSource.onerror = () => {
      eventSource.close();
    };

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

  // Start Agent Run (New Request Reset)
  const handleStartAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || loading) return;

    // Reset workflow-specific states immediately for NEW request (preserving Swiggy OAuth & Address)
    setLoading(true);
    setErrorMessage(null);
    setIsCompareOpen(false);
    setIsPaymentModalOpen(false);
    setIsConfirmOpen(false);
    setAgentState({});
    setSessionId(null);

    try {
      const res = await startAgent(prompt, addressId);
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

  // Interactive Manual Dish Selection Override
  const handleSelectItem = (item: any) => {
    setAgentState((prev: any) => ({
      ...prev,
      selected_item: item,
      user_selected_override: true
    }));
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
  const handleRelaxConstraints = async (newConstraints: any) => {
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
  const needsUserInput = agentState.needs_user_input;
  const replanningRequired = agentState.replanning_required;

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
        selectedAddressId={addressId}
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

        {/* Section 4: Main Request Area (Editorial Food Concierge) */}
        <section className="mb-10">
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
                disabled={loading}
                className="w-full md:w-auto bg-terracotta hover:bg-terracotta-hover text-white font-bold px-8 py-3.5 rounded-full flex items-center justify-center space-x-2 text-sm transition shadow-warm-sm shrink-0 disabled:opacity-50"
              >
                <span>{loading ? 'Finding food...' : 'Find my food'}</span>
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
          />
        )}

        {/* Section 9: Something You'll Love (Menu Grid with Interactive Override Selection) */}
        {menuItems.length > 0 && (
          <MenuGrid
            menuItems={menuItems}
            selectedItem={selectedItem}
            onSelectItem={handleSelectItem}
          />
        )}

        {/* Section 10: Your Order (Cart Summary) */}
        {showCartSummary && (
          <CartSummary
            restaurantName={selectedRest?.name}
            selectedItem={selectedItem}
            addressId={addressId}
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
            trackingResult={agentState.tracking_result}
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
        currentBudget={requirements?.max_budget}
        currentDelivery={requirements?.max_delivery_minutes}
        errorMessage={agentState.error_message}
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
        isLoading={isPlacingOrder}
      />
    </div>
  );
}
