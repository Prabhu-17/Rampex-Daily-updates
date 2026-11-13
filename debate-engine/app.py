import json
import asyncio

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse

import config
from orchestrator import run_debate

app = FastAPI(title="Multi-Agent Debate Engine")


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/api/config")
def get_config():
    return {"has_key": bool(config.API_KEY), "debater_model": config.DEBATER_MODEL,
            "judge_model": config.JUDGE_MODEL}


@app.get("/debate")
async def debate(q: str = Query(..., min_length=5, max_length=500)):
    if not config.API_KEY:
        return JSONResponse({"error": "OPENROUTER_API_KEY is not set. Put it in .env"},
                            status_code=400)
    queue: asyncio.Queue = asyncio.Queue()

    async def emit(event):
        await queue.put(event)

    async def runner():
        try:
            await run_debate(q, emit)
        except Exception as e:
            await emit({"type": "error", "message": f"{type(e).__name__}: {e}"})
        finally:
            await queue.put(None)

    task = asyncio.create_task(runner())

    async def gen():
        try:
            while (e := await queue.get()) is not None:
                yield {"data": json.dumps(e, ensure_ascii=False)}
        finally:
            task.cancel()  # browser closed the page: stop spending tokens

    return EventSourceResponse(gen())
