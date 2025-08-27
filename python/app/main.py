from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（开发测试阶段用）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def sse_response(text: str):
    for ch in text:
        yield f"data: {ch}\n\n"
        await asyncio.sleep(0.05)
    yield "data: [END]\n\n"

@app.get("/sse/chat")
async def chat_sse(msg: str):
    print(msg)
    return StreamingResponse(sse_response(f"你说的是: {msg}"), media_type="text/event-stream")

@app.get("/test")
async def test():
    return "test"