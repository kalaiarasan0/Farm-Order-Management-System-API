from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from ai_agent.tools import (
    create_token_order,
    place_order_with_token,
    search_products,
    search_customers,
    search_inventory_stock_list,
    check_inventory_for_product,
    search_inventory_stock,
)


# --- 2. Setup Llama 3.1 ---
# We use ChatOllama to connect to the local running model.
llm = ChatOllama(
    model="llama3.2",
    temperature=0,  # Keep it deterministic for tool usage
)

# --- 3. Connect (Bind) the Tool to the LLM ---
# This is the crucial step. It forces the LLM to be aware of this function.
tools = [
    create_token_order,
    place_order_with_token,
    search_products,
    search_customers,
    search_inventory_stock_list,
    check_inventory_for_product,
    search_inventory_stock,
]
llm_with_tools = llm.bind_tools(tools)

# --- 4. The Agent Execution Loop ---
# This function handles the conversation flow:
# User -> LLM -> Tool Decision -> Execution -> Result -> LLM -> Final Answer


def run_agent():
    print("--- Farm AI Agent Started (Type 'quit', 'exit', or 'close' to stop) ---")

    # Step A: Define the System Prompt ONCE
    system_prompt = """You are a farm assistant.

        **CRITICAL: You generally CANNOT buy anything without knowing the integer IDs first.**
        The user will give you NAMES (e.g. "Goat", "Kalai").
        You MUST search for their IDs (e.g. 2, 101) before you can do ANYTHING else.

        AVAILABLE TOOLS:
        1. `search_products(query)`: Finds products (animals). Returns `product_id`.
        2. `search_customers(query)`: Finds customers. Returns `customer_id`.
        3. `check_inventory_for_product(product_id)`: Checks stock. Returns inventory info.
        4. `create_token_order(product_id, customer_id, quantity)`: Verifies order. **REQUIRES INTEGER IDs.**
        5. `place_order_with_token(verification_token)`: Places order.
        6. `search_inventory_stock()`: Finds ALL available stock.
        7. `search_inventory_stock_list(query)`: Searches stock.

        **EXECUTION PROTOCOL (Follow EXACTLY):**

        **STEP 1: GET IDs**
        - Does the user input contain NAMES instead of Integer IDs? -> **YOU MUST SEARCH.**
        - Call `search_products("name")` AND `search_customers("name")`.
        - **DO NOT CALL** `create_token_order` yet. It will FAIL if you pass names.
        - **STOP** and wait for the tool output to give you the Integers.

        **STEP 2: CHECK & VERIFY**
        - Now that you have `product_id` (int) and `customer_id` (int) from Step 1:
        - Call `create_token_order(product_id, customer_id, quantity)`.
        - **STOP** and wait for the token.

        **STEP 3: PLACE ORDER**
        - Call `place_order_with_token(token)`.

        **RULES:**
        - **NEVER** pass a string (like "Goat") to `product_id`. It MUST be an integer (like 2).
        - If you don't have the integer, **SEARCH FIRST**.
        - Do not try to skip steps.
        """

    # Initialize conversation history with system prompt
    messages = [SystemMessage(content=system_prompt)]

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
                print(f"[AGENT] Decided to call tool(s): {len(ai_msg.tool_calls)}")

                for tool_call in ai_msg.tool_calls:
                    selected_tool_name = tool_call["name"].lower()
                    print(f"[DEBUG] Tool Args: {tool_call['args']}")

                    tool_output = "Unknown tool"

                    # Match the tool name to our actual function
                    if selected_tool_name == "create_token_order":
                        try:
                            tool_output = create_token_order.invoke(tool_call["args"])
                        except Exception as e:
                            # Catch Pydantic validation errors (when agent passes separate args or strings for ints)
                            error_msg = str(e).lower()
                            if (
                                "validation error" in error_msg
                                or "argument" in error_msg
                            ):
                                tool_output = (
                                    "SYSTEM ERROR: Invalid Arguments for `create_token_order`. "
                                    "Did you pass a String (Name) instead of an Integer (ID)? "
                                    "You CANNOT guess IDs. "
                                    "STOP and call `search_products(name)` and `search_customers(name)` to get the real IDs."
                                )
                            else:
                                tool_output = f"Error: {e}"

                    elif selected_tool_name == "place_order_with_token":
                        try:
                            # Extract single argument correctly
                            args = tool_call["args"]
                            token = args.get("verification_token")
                            tool_output = place_order_with_token.invoke(token)
                        except Exception as e:
                            tool_output = f"Error: {e}"

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
                            tool_output = search_inventory_stock_list.invoke(
                                tool_call["args"]
                            )
                        except Exception as e:
                            tool_output = f"Error: {e}"

                    elif selected_tool_name == "check_inventory_for_product":
                        try:
                            tool_output = check_inventory_for_product.invoke(
                                tool_call["args"]
                            )
                        except Exception as e:
                            tool_output = f"Error: {e}"

                    elif selected_tool_name == "search_inventory_stock":
                        try:
                            tool_output = search_inventory_stock.invoke(
                                tool_call["args"]
                            )
                        except Exception as e:
                            tool_output = f"Error: {e}"

                    print(f"[SYSTEM] Tool Output: {tool_output}")
                    messages.append(
                        ToolMessage(
                            content=str(tool_output), tool_call_id=tool_call["id"]
                        )
                    )

                # Get follow-up response from LLM
                ai_msg = llm_with_tools.invoke(messages)
                messages.append(ai_msg)

            # Final response for this turn
            print(f"\n[AGENT] Final Response:\n{ai_msg.content}")

        except KeyboardInterrupt:
            print("\n--- Session Interrupted ---")
            break
        except Exception as e:
            print(f"An error occurred: {e}")


# --- 5. Run the Example ---
if __name__ == "__main__":
    run_agent()
