import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.core import TravelAgent
from config import config


app = FastAPI(title="旅睿 - 智能旅行清单管家", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent: Optional[TravelAgent] = None


class MessageRequest(BaseModel):
    message: str
    user_id: str = "default"


class ProfileUpdateRequest(BaseModel):
    user_id: str
    key: str
    value: str


class ItemRequest(BaseModel):
    item_id: str
    action: str
    user_id: str = "default"


@app.on_event("startup")
async def startup():
    global agent
    agent = TravelAgent()
    await agent.initialize()


@app.get("/")
async def root():
    return {
        "name": "旅睿 - 智能旅行清单管家",
        "version": "1.0.0",
        "description": "具备长期记忆、主动服务、聊天即操作的旅行清单系统"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/chat")
async def chat(request: MessageRequest):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        result = await agent.process_message(request.message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profile/update")
async def update_profile(request: ProfileUpdateRequest):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    try:
        await agent.update_user_profile(request.key, request.value)
        return {"success": True, "message": "Profile updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    profile = agent.memory_store.user_profile
    if profile and profile.user_id == user_id:
        return profile.model_dump()
    return {"error": "Profile not found"}


@app.get("/api/trip/current/{user_id}")
async def get_current_trip(user_id: str):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    trip = agent.memory_store.current_trip
    if trip:
        return trip.model_dump()
    return {"error": "No current trip"}


@app.post("/api/item/{user_id}")
async def manage_item(user_id: str, request: ItemRequest):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    current_trip = agent.memory_store.current_trip
    if not current_trip or not current_trip.checklist:
        raise HTTPException(status_code=400, detail="No active checklist")

    if request.action == "pack":
        for item in current_trip.checklist.items:
            if item.id == request.item_id:
                item.packed = True
                current_trip.checklist.packed_count += 1
                break
    elif request.action == "unpack":
        for item in current_trip.checklist.items:
            if item.id == request.item_id:
                item.packed = False
                current_trip.checklist.packed_count -= 1
                break
    elif request.action == "delete":
        current_trip.checklist.items = [
            item for item in current_trip.checklist.items if item.id != request.item_id
        ]
        current_trip.checklist.total_count -= 1

    agent.memory_store.save_current_trip(current_trip)

    return {"success": True, "checklist": current_trip.checklist.model_dump()}


@app.get("/api/history/{user_id}")
async def get_trip_history(user_id: str):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    history = agent.memory_store.trip_history
    return {"trips": [trip.model_dump() for trip in history]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
