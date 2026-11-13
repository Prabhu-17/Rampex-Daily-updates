import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openrouter import ChatOpenRouter

from tools import add, subtract, multiply, divide


# STEP 1: Load environment variables
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found in .env file")


# STEP 2: Connect to OpenRouter
model = ChatOpenRouter(
    model="openrouter/free",
    api_key=api_key,
    temperature=0
)


# STEP 3: Register Python tools
tools = [
    add,
    subtract,
    multiply,
    divide
]


# STEP 4: Create the AI agent
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt="""
    You are a helpful calculator assistant.

    Your responsibilities:
    1. Understand mathematical questions.
    2. Choose the correct calculator tool.
    3. Always use the tools for calculations.
    4. Never calculate manually when a tool is available.
    5. Explain the answer in simple language.
    6. If the user asks a non-mathematical question,
       politely explain that you are a calculator assistant.
    """
)


# STEP 5: Start the application
print("\n====================================")
print("       OPENROUTER CALCULATOR AI")
print("====================================")
print("Powered by LangChain + OpenRouter")
print("Ask mathematical questions!")
print("Type 'exit' to stop.\n")


messages = []

while True:

    user_input = input("You: ").strip()

    if user_input.lower() in ["exit", "quit"]:
        print("AI: Goodbye!")
        break

    if not user_input:
        continue

    try:

        messages.append({
            "role": "user",
            "content": user_input
        })

        result = agent.invoke({
            "messages": messages
        })

        messages = result["messages"]

        print("\nAI:", messages[-1].content, "\n")

    except Exception as error:

        print("\nError:", error, "\n")