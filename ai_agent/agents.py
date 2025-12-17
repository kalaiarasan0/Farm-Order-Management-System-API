import json
from typing import Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from ai_agent.tools import submit_final_order, search_products, search_customers, search_inventory_stock_list, check_inventory_for_product, verify_order_details, search_inventory_stock


# --- 2. Setup Llama 3.1 ---
# We use ChatOllama to connect to the local running model.
llm = ChatOllama(
    model="llama3.2",
    temperature=0,  # Keep it deterministic for tool usage
)

# --- 3. Connect (Bind) the Tool to the LLM ---
# This is the crucial step. It forces the LLM to be aware of this function.
tools = [submit_final_order, search_products, search_customers, search_inventory_stock_list, check_inventory_for_product, verify_order_details, search_inventory_stock]
llm_with_tools = llm.bind_tools(tools)

# --- 4. The Agent Execution Loop ---
# This function handles the conversation flow:
# User -> LLM -> Tool Decision -> Execution -> Result -> LLM -> Final Answer

def run_agent():
    print("--- Farm AI Agent Started (Type 'quit', 'exit', or 'close' to stop) ---")
    
    # Step A: Define the System Prompt ONCE
    system_prompt = """You are a farm assistant using tools to help users buy animals.

        AVAILABLE TOOLS:
        1. `search_products(query)`: Finds products (animals). Returns `product_id` (this is the `animal_id` in DB).
        2. `search_customers(query)`: Finds customers. Returns `customer_id`.
        3. `check_inventory_for_product(product_id)`: Checks stock for a product. Returns `inventory_id` and quantity.
        4. `verify_order_details(product_id, inventory_id, customer_id)`: Verifies order and returns `verification_token`.
        5. `submit_final_order(...)`: Requires `verification_token` to place the order.
        6. `search_inventory_stock()`: Finds ALL available stock. Returns full list.
        7. `search_inventory_stock_list(query)`: Searches for stock by name/id.

        CORE INSTRUCTION: 
        To buy an item, you MUST call tools in this exact order:
        1. Search Product -> get `product_id`.
        2. Search Customer -> get `customer_id`.
        3. Check Inventory (using `product_id`) -> get `inventory_id`.
        4. Verify Order -> get `verification_token`.
        5. Submit Order.

        ### PHASE 1: SEARCH (Goal: Get IDs)
        - Call `search_products(query)` AND `search_customers(query)` in parallel.
        - **STOP** and wait for results.
        - If no results are found, inform the user and **STOP**

        ### PHASE 2: INVENTORY (Goal: Check stock)
        - IF you have `product_id` (int) BUT NO `inventory_id` (int):
          - Call `check_inventory_for_product(product_id)`.
          - **STOP** and wait for results.
          - **IF result is "No inventory found"**: Inform the user and **STOP**. Do NOT guess another ID.

        ### PHASE 3: VERIFY (Goal: Get Verification Token)
        - IF you have `product_id`, `customer_id`, AND `inventory_id`:
          - Call `verify_order_details(product_id, inventory_id, customer_id)`.
          - **STOP** and wait for the `verification_token`.

        ### PHASE 4: SUBMIT (Goal: Place Order)
        - IF you have a `verification_token` from Phase 3:
          - Call `submit_final_order(product_id, quantity, inventory_id, customer_id, verification_token)`.

        CRITICAL RULES:
        1. **NEVER GUESS OR INVENT IDs**. You must obtain them from tool outputs.
        2. **Do search steps in parallel** in Phase 1 (e.g., search product and customer together).
        3. Do NOT ask the user for IDs if they gave you names. USE THE SEARCH TOOLS.
        4. You **MUST** call `verify_order_details` to get a token BEFORE calling `submit_final_order`.
        5. If you have NO IDs, you are in Phase 1. CALL SEARCH TOOLS IMMEDIATELY.
        6. **ONE PHASE PER TURN**. DO NOT call `submit_final_order` in the same turn as `search_...`. You must wait for the search results.
        """
    
    # Initialize conversation history with system prompt
    messages = [
        SystemMessage(content=system_prompt)
    ]

    while True:
        try:
            user_query = input("\nUser (or 'exit'): ")
            if user_query.lower() in ["exit", "quit", "close"]:
                print("--- Ending Session ---")
                break
            
            if not user_query.strip():
                continue

            # Add user message to history
            messages.append(HumanMessage(content=user_query))
            
            # Invoke LLM
            ai_msg = llm_with_tools.invoke(messages)
            messages.append(ai_msg)

            # Loop to handle tool calls
            while ai_msg.tool_calls:
                print(f"[AGENT] 🤖  Decided to call tool(s): {len(ai_msg.tool_calls)}")
                
                for tool_call in ai_msg.tool_calls:
                    selected_tool_name = tool_call["name"].lower()
                    print(f"[DEBUG] Tool Args: {tool_call['args']}")
                    
                    tool_output = "Unknown tool"
                    
                    # Match the tool name to our actual function
                    if selected_tool_name == "submit_final_order":
                        try:
                            tool_output = submit_final_order.invoke(tool_call["args"])
                        except Exception as e:
                            tool_output = f"Error: {e}"
                        
                        if str(tool_output).startswith("Error:"):
                             tool_output = f"{tool_output}\n\nSYSTEM HINT: You likely called search tools in parallel. The results are above. FIND the IDs in the tool outputs. USE THEM to call `submit_final_order` with integer IDs immediately. Do NOT search again."

                    elif selected_tool_name == "search_products":
                        try:
                            tool_output = search_products.invoke(tool_call["args"])
                        except Exception as e:
                            tool_output = f"Error: {e}"

                    elif selected_tool_name == "search_customers":
                        try:
                            tool_output = search_customers.invoke(tool_call["args"])
                        except Exception as e:
                            tool_output = f"Error: {e}"

                    elif selected_tool_name == "search_inventory_stock_list":
                        try:
                            tool_output = search_inventory_stock_list.invoke(tool_call["args"])
                        except Exception as e:
                            tool_output = f"Error: {e}"

                    elif selected_tool_name == "verify_order_details":
                        try:
                            tool_output = verify_order_details.invoke(tool_call["args"])
                        except Exception as e:
                            tool_output = f"Error: {e}"

                    elif selected_tool_name == "check_inventory_for_product":
                        try:
                            tool_output = check_inventory_for_product.invoke(tool_call["args"])
                        except Exception as e:
                            tool_output = f"Error: {e}"
                    
                    elif selected_tool_name == "search_inventory_stock":
                        try:
                            tool_output = search_inventory_stock.invoke(tool_call["args"])
                        except Exception as e:
                            tool_output = f"Error: {e}"
                    
                    print(f"[SYSTEM] 🔙  Tool Output: {tool_output}")
                    messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))

                # Get follow-up response from LLM
                ai_msg = llm_with_tools.invoke(messages)
                messages.append(ai_msg)

            # Final response for this turn
            print(f"\n[AGENT] 🗣️  Final Response:\n{ai_msg.content}")
        
        except KeyboardInterrupt:
            print("\n--- Session Interrupted ---")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

# --- 5. Run the Example ---
if __name__ == "__main__":
    run_agent()