from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict
from datetime import date  
from redis_connection import get_session
from redis_connection import save_session

app = FastAPI()

# Dummy data
categories = ["Fruits", "Vegetables", "Dairy"]

items = {
    "Fruits": [
        {"id": 1, "name": "Banana", "price": 20, "unit": "kg"},
        {"id": 2, "name": "Apple", "price": 30, "unit": "kg"},
    ],
    "Vegetables": [
        {"id": 3, "name": "Carrot", "price": 15, "unit": "kg"},
        {"id": 4, "name": "Potato", "price": 10, "unit": "kg"},
    ],
    "Dairy": [
        {"id": 5, "name": "Milk", "price": 50, "unit": "liter"},
        {"id": 6, "name": "Curd", "price": 40, "unit": "kg"},
    ]
}

# Flattened item map for lookup
item_map = {item["id"]: item for cat_items in items.values() for item in cat_items}

# In-memory cart (for demo, keyed by "user")
cart: Dict[str, List[Dict]] = {}

# -------- API Models --------
class CartItem(BaseModel):
    user_id: str
    item_id: int
    quantity: float

class OrderConfirm(BaseModel):
    user_id: str

class RemoveFromCart(BaseModel):
    user_id: str
    item_id: int

# -------- API Endpoints --------

@app.get("/getAllCategories")
def get_all_categories():
    return {"categories": categories}


@app.get("/getAllItems/{category}")
def get_items_by_category(category: str):
    if category not in items:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"items": items[category]}


@app.get("/getItemInfo/{item_id}")
def get_item_info(item_id: int):
    item = item_map.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item": item}


@app.post("/cart/add")
def add_to_cart(cart_item: CartItem):
    session = get_session(cart_item.user_id)
    cart = session.get("cart", [])

    # Update or append item
    for item in cart:
        if item["item_id"] == cart_item.item_id:
            item["quantity"] += cart_item.quantity
            break
    else:
        item = item_map.get(cart_item.item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        cart.append({"item_id": item["id"], "name": item["name"], "quantity": cart_item.quantity})

    # Save updated session
    session["cart"] = cart
    session["last_seen"] = date.today().isoformat()
    save_session(cart_item.user_id, session)

    return {"cart": cart}


@app.post("/cart/remove")
def remove_from_cart(remove_item: RemoveFromCart):
    session = get_session(remove_item.user_id)
    cart = session.get("cart", [])

    # Find and remove the item
    for i, item in enumerate(cart):
        if item["item_id"] == remove_item.item_id:
            del cart[i]
            break
    else:
        raise HTTPException(status_code=404, detail="Item not found in cart")

    # Save updated session
    session["cart"] = cart
    session["last_seen"] = date.today().isoformat()
    save_session(remove_item.user_id, session)

    return {"cart": cart}


@app.get("/cart")
def get_cart(user_id: str):
    return {"cart": cart.get(user_id, [])}


@app.post("/order/confirm")
def confirm_order(order: OrderConfirm):
    session = get_session(order.user_id)
    cart = session.get("cart", [])
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total = sum(item_map[i["item_id"]]["price"] * i["quantity"] for i in cart)
    session["cart"] = []
    session["last_seen"] = date.today().isoformat()
    save_session(order.user_id, session)

    return {
        "message": "Order confirmed!",
        "total_amount": total,
        "items": cart
    }

