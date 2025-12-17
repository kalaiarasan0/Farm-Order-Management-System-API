# --- 1. Define the Tool ---
# The @tool decorator makes this function understandable to the LLM.
# It uses the type hints and docstring to tell Llama 3.1 HOW to use it.

from langchain_core.tools import tool
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

@tool
def verify_order_details(product_id: int, inventory_id: int, customer_id: int) -> str:
    """
    Use this tool to VERIFY the order details BEFORE placing it.
    You MUST provide `product_id`, `inventory_id`, and `customer_id` (all integers).
    Returns a `verification_token` required for `submit_final_order`.
    """
    if not (str(product_id).isdigit() and str(inventory_id).isdigit() and str(customer_id).isdigit()):
         return "Error: IDs must be valid integers."

    # 1. Verify Inventory Existence
    try:
        # Re-use the logic from get_inventory (or call the API directly)
        endpoint = f"{API_BASE_URL}/api/v1/inventories/product/{product_id}"
        response = requests.get(endpoint)
        
        # Check for 404 explicitly
        if response.status_code == 404:
            return f"Verification Failed: No inventory found for product_id {product_id}. Cannot generate token."
            
        response.raise_for_status()
        inventories = response.json()
        
        if not inventories:
             return f"Verification Failed: Inventory list is empty for product_id {product_id}. Cannot generate token."

        # 2. Check if the specific inventory_id exists in the list
        # Convert IDs to int for comparison
        target_inv_id = int(inventory_id)
        valid_ids = [int(item['inventory_id']) for item in inventories]
        
        if target_inv_id not in valid_ids:
             return f"Verification Failed: Inventory ID {target_inv_id} does not exist for Product ID {product_id}. Valid Inventory IDs: {valid_ids}"

    except requests.exceptions.RequestException as e:
        return f"Verification Error accessing API: {e}"
    
    # 3. Generate Token if Valid
    token = f"ver_{product_id}_{customer_id}_{inventory_id}_secure"
    return json.dumps({"status": "verified", "verification_token": token, "message": "Verification valid. You may now call submit_final_order."})

@tool
def submit_final_order(product_id: int, quantity: int, inventory_id: int, customer_id: int, verification_token: str) -> str:
    """
    Use this tool to place the FINAL order.
    Requirements:
    1. `product_id`, `inventory_id`, `customer_id` MUST be integers.
    2. `verification_token` MUST be obtained from `verify_order_details`.
    """
    try:
        if not verification_token or not verification_token.startswith("ver_"):
            return "Error: Invalid or missing `verification_token`. You MUST call `verify_order_details` first to get a token."

        # 1. Define the API endpoint
        endpoint = f"{API_BASE_URL}/api/v1/orders/place-order"
        
        # 2. Construct the payload matching OrderCreate schema
        # {
        #   "customer_id": 123,
        #   "items": [ { "animal_id": 456, "inventory_id": 789, "quantity": 1 } ]
        # }
        
        payload = {
            "customer_id": int(customer_id),
            "items": [
                {
                    "animal_id": int(product_id),
                    "inventory_id": int(inventory_id),
                    "quantity": quantity
                }
            ]
        }


        # 3. Make the REST API call (POST request)
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        
        # 4. Parse the response
        order_details = response.json()
        order_id = order_details.get("id", "Unknown")
        order_number = order_details.get("order_number", "Unknown")

        return f"Order placed successfully! Order ID: {order_id}, Order Number: {order_number}."
        
    except requests.exceptions.RequestException as e:
        return f"Error placing order: {e}. Response: {e.response.text if e.response else 'No response'}"

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
        
        return json.dumps(matches)  

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
        
        if not matches:
            return "No customers found matching the query."
        
        return json.dumps(matches)    

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
        
        return json.dumps(inventories)

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
                animal_name = inventory.get('animal', {}).get('name', "Unknown") if inventory.get('animal') else "Unknown"
                # NOTE: API now returns `product_id`, so we check that first.
                prod_id = inventory.get('product_id', '')
                text_to_search = f"{inventory.get('id', '')} {prod_id} {inventory.get('quantity', '')} {inventory.get('unit_price', '')} {inventory.get('location', '')} {inventory.get('status', '')} {animal_name}".lower()
                if query in text_to_search:
                    matches.append(inventory)
        
        if not matches:
            return "No inventories found matching the query."

        return json.dumps(matches)

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
            
        return json.dumps(inventories)

    except requests.exceptions.RequestException as e:
        if e.response is not None and e.response.status_code == 404:
            return "No inventory found for this product_id."
        return f"Error searching inventory for product_id: {e}"


if __name__ == "__main__":
    # print("--- Testing search_products ---")
    # print(search_products.invoke("sheep")) # Use invoke for tools

    # # Assuming there are customers, otherwise this might return "No customers found"
    # print("\n--- Testing search_customers ---")
    # print(search_customers.invoke("kalaiprrethi"))

    print("--- Testing search_inventory_stock ---")
    print(search_inventory_stock.invoke(""))

    # print("--- Testing search_inventory_stock_list ---")
    # print(search_inventory_stock_list.invoke("available stock"))

    # print("--- Testing check_inventory_for_product ---")
    # print(check_inventory_for_product.invoke("1231"))
