import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY", "")
BASE_URL = "https://openrouter.ai/api/v1"
DEBATER_MODEL = os.getenv("DEBATER_MODEL", "openai/gpt-4o-mini")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "openai/gpt-4o")
APP_URL = os.getenv("APP_URL", "http://localhost:8000")
APP_NAME = os.getenv("APP_NAME", "Debate Engine")

# Limits
MAX_TOOL_STEPS = 4          # tool-call rounds per agent turn
MAX_TOOL_PAYLOAD = 2500     # chars of a tool result passed back to the model
MAX_TURN_TOKENS = 700
