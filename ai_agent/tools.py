# --- 1. Define the Tool ---
# The @tool decorator makes this function understandable to the LLM.
# It uses the type hints and docstring to tell Llama 3.1 HOW to use it.

from langchain_core.tools import tool
import requests

API_BASE_URL = "http://127.0.0.1:8000"

@tool
def create_farm_order(product_id: int | str, quantity: int, inventory_id: int | str, customer_id: int | str = None, customer_name: str = None) -> str:
    """
    Use this tool to place an order.
    You MUST provide `product_id`, `inventory_id`, and `quantity`.
    `product_id` (animal_id) and `inventory_id` MUST be integers.
    Use `search_inventory_stock_list` to find BOTH the `product_id` and `inventory_id`.
    You SHOULD provide `customer_id` if known.
    If `customer_id` is NOT known, you can provide `customer_name`, but it is better to search for the customer first.
    """
    try:
        # 0. Validate inputs are integers
        if not str(product_id).isdigit() or not str(inventory_id).isdigit():
            return "ERROR: You provided a NAME (string) for `product_id` or `inventory_id`. You MUST use integer IDs. \n1. Call `search_products` to find the `product_id`.\n2. Call `get_inventory_by_animal_id` with that `product_id` to find the `inventory_id`.\n3. Then call this tool again with the integers."

        if customer_id and not str(customer_id).isdigit():
             return "ERROR: You provided a NAME for `customer_id`. Call `search_customers` to find the integer ID first."

        # 1. Define the API endpoint
        endpoint = f"{API_BASE_URL}/api/v1/orders/place-order"
        
        # 2. Construct the payload matching OrderCreate schema
        # {
        #   "customer_id": 123,
        #   "items": [ { "animal_id": 456, "inventory_id": 789, "quantity": 1 } ]
        # }
        
        payload = {
            "items": [
                {
                    "animal_id": int(product_id),
                    "inventory_id": int(inventory_id),
                    "quantity": quantity
                }
            ]
        }
        
        if customer_id:
            payload["customer_id"] = int(customer_id)
        elif customer_name:
            # If we only have a name, we return an error asking to search for ID.
            return "Error: Please find the 'customer_id' using 'search_customers' tool before placing an order."
        else:
             return "Error: 'customer_id' is required."

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
    Use this tool to find products (animals) based on a search query.
    Useful when the user asks for something vague like "milk goats" or "large animals".
    It searches name, species, and description.
    """
    try:
        # 1. Fetch all animals
        endpoint = f"{API_BASE_URL}/api/v1/animals/list"
        response = requests.get(endpoint)
        response.raise_for_status()
        animals = response.json()
        
        if not animals:
            return "No products found in the catalog."
            
        # 2. Perform simple client-side search
        query = query.lower()
        matches = []
        
        for animal in animals:
            # Search in name, species, and description
            text_to_search = f"{animal['name']} {animal['species']} {animal.get('description', '')}".lower()
            
            if query in text_to_search:
                matches.append(animal)
        
        if not matches:
            return f"No products found matching '{query}'."
            
        # 3. Format results
        formatted_results = []
        for item in matches[:5]: # Limit to top 5
            formatted_results.append(
                f"ID: {item['id']} | Name: {item['name']} | Species: {item['species']} | Price: ${item['base_price']} | Desc: {item.get('description', 'N/A')}"
            )
            
        return "\n".join(formatted_results)

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
        
        if not customers:
            return "No customers found."
            
        # 2. Client-side search
        query = query.lower()
        matches = []
        
        for cust in customers:
            text_to_search = f"{cust['first_name']} {cust['last_name']} {cust['email']} {cust['phone']}".lower()
            if query in text_to_search:
                matches.append(cust)
        
        if not matches:
            return f"No customers found matching '{query}'."
            
        # 3. Format results
        formatted_results = []
        for item in matches[:5]:
            formatted_results.append(
                f"ID: {item['id']} | Name: {item['first_name']} {item['last_name']} | Email: {item['email']} | Phone: {item['phone']}"
            )
            
        return "\n".join(formatted_results)

    except requests.exceptions.RequestException as e:
        return f"Error searching customers: {e}"


@tool
def search_inventory_stock_list(query: str) -> str:
    """
    Use this tool to find a inventory stock.
    Useful when you need to find `inventory_id` and `animal_id` (product_id) for an order.
    """
    try:
        # 1. Fetch all customers
        endpoint = f"{API_BASE_URL}/api/v1/inventories/list"
        response = requests.get(endpoint)
        response.raise_for_status()
        inventories = response.json()
        
        if not inventories:
            return "No inventories found."
            
        # 2. Client-side search
        query = query.lower()
        matches = []
        
        for inventory in inventories:
            # Handle potential None for animal
            animal_name = inventory['animal']['name'] if inventory.get('animal') else "Unknown"
            text_to_search = f"{inventory['id']} {inventory['animal_id']} {inventory['quantity']} {inventory['unit_price']} {inventory['location']} {inventory['status']} {animal_name}".lower()
            if query in text_to_search:
                matches.append(inventory)
        
        if not matches:
            return f"No inventory stock found matching '{query}'."
            
        # 3. Format results
        formatted_results = []
        for item in matches[:5]:
            animal_name = item['animal']['name'] if item.get('animal') else "Unknown"
            formatted_results.append(
                f"Inventory ID: {item['id']} | Animal ID: {item['animal_id']} | Quantity: {item['quantity']} | Unit Price: {item['unit_price']} | Location: {item['location']} | Status: {item['status']} | Animal Name: {animal_name}"
            )
            
        return "\n".join(formatted_results)

    except requests.exceptions.RequestException as e:
        return f"Error searching Stock Inventory: {e}"

@tool
def get_inventory_by_animal_id(animal_id: int) -> str:
    """
    Use this tool to find inventory items for a specific animal ID.
    Useful when you have the `animal_id` (product_id) and need the `inventory_id`.
    """
    try:
        endpoint = f"{API_BASE_URL}/api/v1/inventories/animal-id/{animal_id}"
        response = requests.get(endpoint)
        response.raise_for_status()
        inventories = response.json()
        
        if not inventories:
            return f"No inventory found for animal ID {animal_id}."
            
        formatted_results = []
        for item in inventories:
            formatted_results.append(
                f"Inventory ID: {item['id']} | Animal ID: {item['animal_id']} | Quantity: {item['quantity']} | Unit Price: {item['unit_price']} | Location: {item['location']} | Status: {item['status']}"
            )
            
        return "\n".join(formatted_results)

    except requests.exceptions.RequestException as e:
        return f"Error fetching inventory by animal ID: {e}"


if __name__ == "__main__":
    print("--- Testing search_products ---")
    print(search_products("goat"))
    print("\n--- Testing search_customers ---")
    # Assuming there are customers, otherwise this might return "No customers found"
    print(search_customers("kalai")) 