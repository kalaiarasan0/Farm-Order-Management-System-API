from ai_agent.agents import run_agent

if __name__ == "__main__":
    print("--- Testing Refined Inventory Workflow ---")
    prompt = "place order of 3 units of Goat to the customer kalai arasan"
    print(f"Prompt: {prompt}\n")
    run_agent(prompt)
