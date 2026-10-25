import os
import sys
import random
import time
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

random.seed(42)

num_trials = 100
items_pool = [
    ("Margherita Pizza", 199, True),
    ("Veggie Supreme Pizza", 399, True),
    ("Chicken Pepperoni Pizza", 450, False),
    ("Garlic Breadsticks", 129, True),
    ("Paneer Butter Masala", 280, True),
    ("Non-Veg Feast Pizza", 599, False),
    ("Farmhouse Pizza", 349, True),
    ("Paneer Tikka Pizza", 389, True),
    ("Cheese Burst Pizza", 499, True),
    ("Gourmet Truffle Pizza", 650, True)
]

reflex_stats = {"success": 0, "total_time": 0, "violations": 0, "avg_rating": [], "avg_delivery": [], "avg_price": []}
goal_stats = {"success": 0, "total_time": 0, "violations": 0, "avg_rating": [], "avg_delivery": [], "avg_price": []}
utility_stats = {"success": 0, "total_time": 0, "violations": 0, "avg_rating": [], "avg_delivery": [], "avg_price": []}

for trial in range(num_trials):
    req_budget = 500
    req_time = 30
    req_veg = True
    
    restaurants = []
    for r_idx in range(8):
        name = f"Rest_{r_idx}"
        rating = round(random.uniform(3.2, 4.9), 1)
        delivery_time = random.randint(15, 45)
        menu = random.sample(items_pool, random.randint(2, 4))
        restaurants.append({"name": name, "rating": rating, "delivery_time": delivery_time, "menu": menu})
        
    # 1. REFLEX AGENT
    t0 = time.perf_counter()
    reflex_choice = None
    for r in restaurants:
        for name, price, is_veg in r["menu"]:
            if "pizza" in name.lower() and price <= req_budget:
                reflex_choice = (r, name, price, is_veg)
                break
        if reflex_choice:
            break
    t1 = time.perf_counter()
    reflex_stats["total_time"] += (t1 - t0) * 1000
    
    if reflex_choice:
        r, name, price, is_veg = reflex_choice
        if r["delivery_time"] <= req_time and is_veg:
            reflex_stats["success"] += 1
            reflex_stats["avg_rating"].append(r["rating"])
            reflex_stats["avg_delivery"].append(r["delivery_time"])
            reflex_stats["avg_price"].append(price)
        else:
            reflex_stats["violations"] += 1
            
    # 2. GOAL-BASED AGENT
    t0 = time.perf_counter()
    goal_choice = None
    for r in restaurants:
        if r["delivery_time"] <= req_time:
            for name, price, is_veg in r["menu"]:
                if "pizza" in name.lower() and price <= req_budget and is_veg:
                    goal_choice = (r, name, price, is_veg)
                    break
        if goal_choice:
            break
    t1 = time.perf_counter()
    goal_stats["total_time"] += (t1 - t0) * 1000
    
    if goal_choice:
        r, name, price, is_veg = goal_choice
        goal_stats["success"] += 1
        goal_stats["avg_rating"].append(r["rating"])
        goal_stats["avg_delivery"].append(r["delivery_time"])
        goal_stats["avg_price"].append(price)
        
    # 3. UTILITY-BASED / LANGGRAPH AGENT (OUR AGENT)
    t0 = time.perf_counter()
    utility_choice = None
    best_u = -9999
    for r in restaurants:
        if r["delivery_time"] <= req_time:
            for name, price, is_veg in r["menu"]:
                if "pizza" in name.lower() and price <= req_budget and is_veg:
                    score = (r["rating"] * 20) + (50 - r["delivery_time"]) + (50 - price / 10)
                    if score > best_u:
                        best_u = score
                        utility_choice = (r, name, price, is_veg)
    t1 = time.perf_counter()
    utility_stats["total_time"] += (t1 - t0) * 1000
    
    if utility_choice:
        r, name, price, is_veg = utility_choice
        utility_stats["success"] += 1
        utility_stats["avg_rating"].append(r["rating"])
        utility_stats["avg_delivery"].append(r["delivery_time"])
        utility_stats["avg_price"].append(price)

print("=== COMPARATIVE SIMULATION RESULTS ===")
print(f"Reflex Agent: Success={reflex_stats['success']}%, Avg Time={(reflex_stats['total_time']/num_trials):.4f}ms, Violations={reflex_stats['violations']}")
print(f"Goal-Based Agent: Success={goal_stats['success']}%, Avg Time={(goal_stats['total_time']/num_trials):.4f}ms, Violations={goal_stats['violations']}")
print(f"Utility LangGraph Agent: Success={utility_stats['success']}%, Avg Time={(utility_stats['total_time']/num_trials):.4f}ms, Violations={utility_stats['violations']}")

print(f"Reflex Avg Rating: {sum(reflex_stats['avg_rating'])/max(1, len(reflex_stats['avg_rating'])):.2f} stars, Delivery: {sum(reflex_stats['avg_delivery'])/max(1, len(reflex_stats['avg_delivery'])):.1f} min, Price: Rs {sum(reflex_stats['avg_price'])/max(1, len(reflex_stats['avg_price'])):.0f}")
print(f"Goal Avg Rating: {sum(goal_stats['avg_rating'])/max(1, len(goal_stats['avg_rating'])):.2f} stars, Delivery: {sum(goal_stats['avg_delivery'])/max(1, len(goal_stats['avg_delivery'])):.1f} min, Price: Rs {sum(goal_stats['avg_price'])/max(1, len(goal_stats['avg_price'])):.0f}")
print(f"Utility Avg Rating: {sum(utility_stats['avg_rating'])/max(1, len(utility_stats['avg_rating'])):.2f} stars, Delivery: {sum(utility_stats['avg_delivery'])/max(1, len(utility_stats['avg_delivery'])):.1f} min, Price: Rs {sum(utility_stats['avg_price'])/max(1, len(utility_stats['avg_price'])):.0f}")
