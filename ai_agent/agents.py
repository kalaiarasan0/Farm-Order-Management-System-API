import json
from typing import Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from ai_agent.tools import create_farm_order, search_products, search_customers, search_inventory_stock_list, get_inventory_by_animal_id


# --- 2. Setup Llama 3.1 ---
# We use ChatOllama to connect to the local running model.
llm = ChatOllama(
    model="llama3.2",
    temperature=0,  # Keep it deterministic for tool usage
)

# --- 3. Connect (Bind) the Tool to the LLM ---
# This is the crucial step. It forces the LLM to be aware of this function.
tools = [create_farm_order, search_products, search_customers, search_inventory_stock_list, get_inventory_by_animal_id]
llm_with_tools = llm.bind_tools(tools)

# --- 4. The Agent Execution Loop ---
# This function handles the conversation flow:
# User -> LLM -> Tool Decision -> Execution -> Result -> LLM -> Final Answer

def run_agent(user_query: str):
    print(f"--- User Query: {user_query} ---")
    
    # Step A: Define the System Prompt
    system_prompt = """
    You are a smart farm sales assistant.
    
    CRITICAL RULE:
    You MUST follow this 4-step workflow for EVERY order request:
    
    Step 1: Call `search_products` (for animal ID) and `search_customers` (for customer ID).
    **STOP and WAIT for results.**
    
    Step 2: Call `get_inventory_by_animal_id` using the `product_id` found in Step 1.
    **STOP and WAIT for results.**
    
    Step 3: ONLY after you have `product_id`, `customer_id`, and `inventory_id`, call `create_farm_order`.
    
    FORBIDDEN:
    - Do NOT call `create_farm_order` in Step 1 or Step 2.
    - Do NOT guess IDs.
    
    If you are missing any ID, you MUST search for it.
    
    IMPORTANT:
    - IF YOU HAVE THE IDs, CALL THE TOOL IMMEDIATELY. DO NOT WRITE TEXT SAYING YOU WILL DO IT. JUST DO IT.
    """
    
    # Step B: Send user query to Llama 3.1 with System Prompt
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_query)
    ]
    ai_msg = llm_with_tools.invoke(messages)
    
    messages.append(ai_msg)

    # Step B: Loop until the LLM stops calling tools
    while ai_msg.tool_calls:
        print(f"[AGENT] 🤖  Decided to call tool(s): {len(ai_msg.tool_calls)}")
        
        # Step C: Execute the tools requested by the LLM
        for tool_call in ai_msg.tool_calls:
            selected_tool_name = tool_call["name"].lower()
            
            # Match the tool name to our actual function
            if selected_tool_name == "create_farm_order":
                tool_args = tool_call["args"]
                try:
                    tool_output = create_farm_order.invoke(tool_args)
                except Exception as e:
                    tool_output = f"Error: {e}"
                
                # Check for error string returned by tool (or exception caught above)
                if str(tool_output).startswith("Error:"):
                     tool_output = f"{tool_output}\n\nSYSTEM HINT: You likely called search tools in parallel. The results are above. FIND the IDs in the tool outputs. USE THEM to call `create_farm_order` with integer IDs immediately. Do NOT search again."
                
                print(f"[SYSTEM] 🔙  Tool Output: {tool_output}")
                messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))

            elif selected_tool_name == "search_products":
                tool_args = tool_call["args"]
                try:
                    tool_output = search_products.invoke(tool_args)
                except Exception as e:
                    tool_output = f"Error: {e}"
                print(f"[SYSTEM] 🔙  Tool Output: {tool_output}")
                messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))

            elif selected_tool_name == "search_customers":
                tool_args = tool_call["args"]
                try:
                    tool_output = search_customers.invoke(tool_args)
                except Exception as e:
                    tool_output = f"Error: {e}"
                print(f"[SYSTEM] 🔙  Tool Output: {tool_output}")
                messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))

            elif selected_tool_name == "search_inventory_stock_list":
                tool_args = tool_call["args"]
                try:
                    tool_output = search_inventory_stock_list.invoke(tool_args)
                except Exception as e:
                    tool_output = f"Error: {e}"
                print(f"[SYSTEM] 🔙  Tool Output: {tool_output}")
                messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))

            elif selected_tool_name == "get_inventory_by_animal_id":
                tool_args = tool_call["args"]
                try:
                    tool_output = get_inventory_by_animal_id.invoke(tool_args)
                except Exception as e:
                    tool_output = f"Error: {e}"
                print(f"[SYSTEM] 🔙  Tool Output: {tool_output}")
                messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))

        # Step D: Get the next response from the LLM
        ai_msg = llm_with_tools.invoke(messages)
        messages.append(ai_msg)

    # Step E: Final Response (when no more tools are called)
    print(f"\n[AGENT] 🗣️  Final Response:\n{ai_msg.content}")

# --- 5. Run the Example ---
if __name__ == "__main__":
    # Example 1: A query that requires the tool
    input_promt = input("Enter your prompt here => ")
    run_agent(input_promt)