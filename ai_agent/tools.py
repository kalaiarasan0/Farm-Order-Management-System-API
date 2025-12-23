# --- 1. Define the Tool ---
# The @tool decorator makes this function understandable to the LLM.
# It uses the type hints and docstring to tell Llama 3.1 HOW to use it.

from langchain_core.tools import tool
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"


@tool
def create_token_order(product_id: int, customer_id: int, quantity: int) -> str:
    """
    Use this tool to VERIFY order details and GENERATE a token.
    Call this BEFORE placing an order.
    Returns: A `verification_token` and status message.
    """
    if not (
        str(product_id).isdigit()
        and str(customer_id).isdigit()
        and str(quantity).isdigit()
    ):
        return "Error: IDs and quantity must be valid integers."

    try:
        endpoint = f"{API_BASE_URL}/api/v1/ai_work/create_token_order"
        payload = {
            "product_id": int(product_id),
            "customer_id": int(customer_id),
            "quantity": int(quantity),
        }

        response = requests.post(endpoint, json=payload)

        # We might get 200 OK with "status": "error" or 4xx/5xx
        if response.status_code != 200:
            return f"Error connecting to API: {response.text}"

        result = response.json()

        if result.get("status") == "error":
            return f"Verification Failed: {result.get('message')}"

        token = result.get("verification_token")
        if not token:
            return "Error: Verification succeeded but no token returned."

        return json.dumps(
            {
                "status": "verified",
                "verification_token": token,
                "message": "Token generated successfully. Use this token to place the order.",
            }
        )

    except requests.exceptions.RequestException as e:
        return f"Verification Error accessing API: {e}"


@tool
def place_order_with_token(verification_token: str) -> str:
    """
    Use this tool to PLACE the final order using a verification token.
    You must obtain the token from `create_token_order` first.
    """
    if not verification_token:
        return "Error: Verification token is required."

    try:
        endpoint = f"{API_BASE_URL}/api/v1/ai_work/place_order"
        payload = {"verification_token": verification_token}

        response = requests.post(endpoint, json=payload)

        if response.status_code != 200:
            return f"Error placing order: {response.text}"

        result = response.json()

        if result.get("status") == "error":
            return f"Order Placement Failed: {result.get('message')}"

        return f"Order Placed Successfully! Order ID: {result.get('order_id')}, Order Number: {result.get('order_number')}"

    except requests.exceptions.RequestException as e:
        return f"Error placing order: {e}"


@tool
def search_products(query: str) -> str:
    """
    Use this tool to find products based on a search query.
    Useful when the user asks for something vague like "milk goats" or "large animals".
    It searches name, species, and description.
    """
    try:
        # 1. Fetch all products
        endpoint = f"{API_BASE_URL}/api/v1/products/list"
        response = requests.get(endpoint)
        response.raise_for_status()
        products = response.json()

        # 2. Perform simple client-side search
        query = query.lower().strip()
        matches = []

        if query == "all" or query == "":
            matches = products
        else:
            for product in products:
                # Search in name, species, and description
                text_to_search = f"{product['name']} {product['species']} {product.get('description', '')}".lower()

                if query in text_to_search:
                    matches.append(product)

        return matches

    except requests.exceptions.RequestException as e:
        return f"Error searching products: {e}"


@tool
def search_customers(query: str) -> str:
    """
    Use this tool to find a customer's ID by name, email, or phone.
    Useful when you need 'customer_id' to place an order.
    """
    try:
        # 1. Fetch all customers
        endpoint = f"{API_BASE_URL}/api/v1/customers/list"
        response = requests.get(endpoint)
        response.raise_for_status()
        customers = response.json()

        # 2. Client-side search
        query = query.lower()
        matches = []

        for cust in customers:
            text_to_search = f"{cust['first_name']} {cust['last_name']} {cust['email']} {cust['phone']}".lower()
            if query in text_to_search:
                matches.append(cust)

        # if not matches:
        #     return "No customers found matching the query."

        return matches

    except requests.exceptions.RequestException as e:
        return "Error searching customers: " + str(e)


@tool
def search_inventory_stock() -> str:
    """
    Use this tool to find a inventory stock available.
    Useful when you need to find all inventory stock available.
    """
    try:
        # 1. Fetch all customers
        endpoint = f"{API_BASE_URL}/api/v1/inventories/list"
        response = requests.get(endpoint)
        response.raise_for_status()
        inventories = response.json()

        return inventories

    except requests.exceptions.RequestException as e:
        return f"Error searching Stock Inventory: {e}"


@tool
def search_inventory_stock_list(query: str) -> str:
    """
    Use this tool to find a inventory stock.
    Useful when you need to find `inventory_id` and `product_id` for an order.
    """
    try:
        # 1. Fetch all customers
        endpoint = f"{API_BASE_URL}/api/v1/inventories/list"
        response = requests.get(endpoint)
        response.raise_for_status()
        inventories = response.json()

        # 2. Client-side search
        query = query.lower().strip()
        matches = []

        if query == "all" or query == "":
            matches = inventories
        else:
            for inventory in inventories:
                # Handle potential None for animal
                animal_name = (
                    inventory.get("animal", {}).get("name", "Unknown")
                    if inventory.get("animal")
                    else "Unknown"
                )
                # NOTE: API now returns `product_id`, so we check that first.
                prod_id = inventory.get("product_id", "")
                text_to_search = f"{inventory.get('id', '')} {prod_id} {inventory.get('quantity', '')} {inventory.get('unit_price', '')} {inventory.get('location', '')} {inventory.get('status', '')} {animal_name}".lower()
                if query in text_to_search:
                    matches.append(inventory)

        if not matches:
            return "No inventories found matching the query."

        return matches

    except requests.exceptions.RequestException as e:
        return f"Error searching Stock Inventory: {e}"


@tool
def check_inventory_for_product(product_id: int) -> str:
    """
    Use this tool to find inventory items for a specific Product ID.
    Useful when you have the `product_id` and need the `inventory_id`.
    """
    try:
        # Update endpoint to new route
        endpoint = f"{API_BASE_URL}/api/v1/inventories/product/{product_id}"
        response = requests.get(endpoint)

        if response.status_code == 404:
            return "No inventory found for this product_id."

        response.raise_for_status()
        inventories = response.json()

        if not inventories:
            return "No inventory found for this product_id."

        return inventories

    except requests.exceptions.RequestException as e:
        if e.response is not None and e.response.status_code == 404:
            return "No inventory found for this product_id."
        return f"Error searching inventory for product_id: {e}"


if __name__ == "__main__":
    # print("--- Testing search_products ---")
    # print(search_products.invoke("sheep")) # Use invoke for tools

    # # Assuming there are customers, otherwise this might return "No customers found"
    print("\n--- Testing search_customers ---")
    print(search_customers.invoke("kalai"))

    # print("--- Testing search_inventory_stock ---")
    # print(search_inventory_stock.invoke(""))

    # print("--- Testing search_inventory_stock_list ---")
    # print(search_inventory_stock_list.invoke("available stock"))

    # print("--- Testing check_inventory_for_product ---")
    # print(check_inventory_for_product.invoke("1231"))
