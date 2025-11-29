from ai_agent.tools import get_inventory_by_animal_id

if __name__ == "__main__":
    print("--- Testing get_inventory_by_animal_id ---")
    # Assuming Goat has ID 2 (based on previous logs)
    print(get_inventory_by_animal_id.invoke({"animal_id": 2}))
